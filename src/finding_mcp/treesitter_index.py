"""tree-sitter wrapper.

Per-language parsers are lazily initialized. Trees are cached per (path, mtime).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Language, Node, Parser

from .languages import detect_language
from .models import CodeLocation, FunctionBody, ImportEntry


class TreeSitterError(RuntimeError):
    pass


# --- Lazy parser registry ---


_PARSERS: dict[str, Parser] = {}
_PARSER_LOCK = threading.Lock()


def _get_parser(language: str) -> Parser:
    with _PARSER_LOCK:
        if language in _PARSERS:
            return _PARSERS[language]

        try:
            if language == "java":
                import tree_sitter_java as ts_lang
                lang_obj = Language(ts_lang.language())
            elif language == "php":
                import tree_sitter_php as ts_lang
                # tree-sitter-php exposes language_php() in recent versions
                fn = getattr(ts_lang, "language_php", None) or ts_lang.language
                lang_obj = Language(fn())
            elif language == "javascript":
                import tree_sitter_javascript as ts_lang
                lang_obj = Language(ts_lang.language())
            elif language == "typescript":
                import tree_sitter_typescript as ts_lang
                lang_obj = Language(ts_lang.language_typescript())
            elif language == "tsx":
                import tree_sitter_typescript as ts_lang
                lang_obj = Language(ts_lang.language_tsx())
            else:
                raise TreeSitterError(f"Unsupported language: {language}")
        except ImportError as e:
            raise TreeSitterError(
                f"tree-sitter grammar for {language} not installed: {e}"
            ) from e

        parser = Parser(lang_obj)
        _PARSERS[language] = parser
        return parser


# --- Tree caching ---


@dataclass
class CachedTree:
    source: bytes
    root: Node
    language: str
    mtime: float


_TREE_CACHE: dict[Path, CachedTree] = {}
_TREE_LOCK = threading.Lock()


def parse_file(absolute_path: Path) -> CachedTree:
    language = detect_language(absolute_path)
    if language is None:
        raise TreeSitterError(f"Unsupported file type: {absolute_path}")

    try:
        mtime = absolute_path.stat().st_mtime
    except FileNotFoundError as e:
        raise TreeSitterError(f"File not found: {absolute_path}") from e

    with _TREE_LOCK:
        cached = _TREE_CACHE.get(absolute_path)
        if cached is not None and cached.mtime == mtime:
            return cached

    source = absolute_path.read_bytes()
    parser = _get_parser(language)
    tree = parser.parse(source)
    cached = CachedTree(source=source, root=tree.root_node, language=language, mtime=mtime)
    with _TREE_LOCK:
        _TREE_CACHE[absolute_path] = cached
    return cached


# --- Node helpers ---


# Node types that represent a callable definition, per language
FUNCTION_NODE_TYPES: dict[str, set[str]] = {
    "java": {"method_declaration", "constructor_declaration"},
    "php": {"function_definition", "method_declaration"},
    "javascript": {
        "function_declaration",
        "function_expression",
        "arrow_function",
        "method_definition",
        "generator_function_declaration",
    },
    "typescript": {
        "function_declaration",
        "function_expression",
        "arrow_function",
        "method_definition",
        "method_signature",
    },
    "tsx": {
        "function_declaration",
        "function_expression",
        "arrow_function",
        "method_definition",
        "method_signature",
    },
}


# Field names that hold the function name across grammars
NAME_FIELD_CANDIDATES = ("name",)


def _node_text(node: Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _function_name(node: Node, source: bytes) -> str | None:
    for field in NAME_FIELD_CANDIDATES:
        child = node.child_by_field_name(field)
        if child is not None:
            return _node_text(child, source)
    # Arrow functions / anonymous expressions: try to find a parent variable_declarator
    # so we can attribute the function to the variable it's assigned to.
    parent = node.parent
    while parent is not None:
        if parent.type in ("variable_declarator", "assignment_expression", "property_signature"):
            name_node = parent.child_by_field_name("name") or parent.child_by_field_name("left")
            if name_node:
                return _node_text(name_node, source)
        parent = parent.parent
    return None


def _signature(node: Node, source: bytes, language: str) -> str:
    """Best-effort signature line: from start to first '{' or ';'."""
    text = _node_text(node, source)
    for terminator in ("{", "=>", ";"):
        idx = text.find(terminator)
        if idx != -1:
            return text[:idx].strip()
    return text.splitlines()[0].strip() if text else ""


def _walk(node: Node):
    yield node
    for child in node.children:
        yield from _walk(child)


# --- Public API used by tools ---


def find_function(
    absolute_path: Path, function_name: str
) -> FunctionBody | None:
    cached = parse_file(absolute_path)
    func_types = FUNCTION_NODE_TYPES.get(cached.language, set())
    rel_path = str(absolute_path)

    for node in _walk(cached.root):
        if node.type not in func_types:
            continue
        name = _function_name(node, cached.source)
        if name == function_name:
            body_text = _node_text(node, cached.source)
            return FunctionBody(
                name=function_name,
                location=CodeLocation(
                    file_path=rel_path,
                    line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    column=node.start_point[1] + 1,
                ),
                signature=_signature(node, cached.source, cached.language),
                body=body_text,
                language=cached.language,
            )
    return None


def find_function_at_line(
    absolute_path: Path, line: int
) -> FunctionBody | None:
    """Find the innermost function enclosing the given 1-indexed line."""
    cached = parse_file(absolute_path)
    func_types = FUNCTION_NODE_TYPES.get(cached.language, set())
    target_row = line - 1  # tree-sitter rows are 0-indexed

    candidates: list[Node] = []
    for node in _walk(cached.root):
        if node.type not in func_types:
            continue
        if node.start_point[0] <= target_row <= node.end_point[0]:
            candidates.append(node)
    if not candidates:
        return None
    # Innermost = smallest span
    chosen = min(candidates, key=lambda n: n.end_byte - n.start_byte)
    name = _function_name(chosen, cached.source) or "<anonymous>"
    return FunctionBody(
        name=name,
        location=CodeLocation(
            file_path=str(absolute_path),
            line=chosen.start_point[0] + 1,
            end_line=chosen.end_point[0] + 1,
            column=chosen.start_point[1] + 1,
        ),
        signature=_signature(chosen, cached.source, cached.language),
        body=_node_text(chosen, cached.source),
        language=cached.language,
    )


# --- Call expression types per language (for get_callees) ---


CALL_NODE_TYPES: dict[str, set[str]] = {
    "java": {"method_invocation", "object_creation_expression"},
    "php": {"function_call_expression", "member_call_expression", "scoped_call_expression",
            "object_creation_expression"},
    "javascript": {"call_expression", "new_expression"},
    "typescript": {"call_expression", "new_expression"},
    "tsx": {"call_expression", "new_expression"},
}


def _callee_text(call_node: Node, source: bytes, language: str) -> str | None:
    """Extract the textual callee (e.g. 'foo' or 'obj.method') from a call expression."""
    # Try common field names across grammars
    for field in ("function", "name", "constructor"):
        child = call_node.child_by_field_name(field)
        if child is not None:
            return _node_text(child, source)
    # Fallback: first child
    if call_node.children:
        return _node_text(call_node.children[0], source)
    return None


def list_callees(absolute_path: Path, function_name: str) -> list[tuple[str, CodeLocation]]:
    """Return (callee, location) pairs for all calls inside `function_name`."""
    cached = parse_file(absolute_path)
    func_types = FUNCTION_NODE_TYPES.get(cached.language, set())
    call_types = CALL_NODE_TYPES.get(cached.language, set())

    target: Node | None = None
    for node in _walk(cached.root):
        if node.type in func_types:
            name = _function_name(node, cached.source)
            if name == function_name:
                target = node
                break
    if target is None:
        return []

    out: list[tuple[str, CodeLocation]] = []
    for node in _walk(target):
        if node.type not in call_types:
            continue
        callee = _callee_text(node, cached.source, cached.language)
        if not callee:
            continue
        out.append(
            (
                callee,
                CodeLocation(
                    file_path=str(absolute_path),
                    line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    column=node.start_point[1] + 1,
                ),
            )
        )
    return out


# --- Imports ---


# Import-like node types per language
IMPORT_NODE_TYPES: dict[str, set[str]] = {
    "java": {"import_declaration"},
    "php": {"namespace_use_declaration"},
    "javascript": {"import_statement", "import_clause"},
    "typescript": {"import_statement", "import_clause", "import_alias"},
    "tsx": {"import_statement", "import_clause", "import_alias"},
}


def list_imports(absolute_path: Path) -> list[ImportEntry]:
    cached = parse_file(absolute_path)
    types_ = IMPORT_NODE_TYPES.get(cached.language, set())
    rel_path = str(absolute_path)

    out: list[ImportEntry] = []
    for node in _walk(cached.root):
        if node.type not in types_:
            continue
        # Avoid duplicates (e.g. an import_clause inside import_statement)
        if node.parent is not None and node.parent.type in types_:
            continue
        raw = _node_text(node, cached.source).strip()
        target = _extract_import_target(node, cached.source, cached.language)
        out.append(
            ImportEntry(
                raw=raw,
                target=target,
                location=CodeLocation(
                    file_path=rel_path,
                    line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                ),
            )
        )
    return out


def _extract_import_target(node: Node, source: bytes, language: str) -> str:
    """Best-effort extraction of the imported module/class name."""
    # JS/TS: source string is the module path
    for field in ("source", "name", "path"):
        child = node.child_by_field_name(field)
        if child is not None:
            text = _node_text(child, source).strip()
            return text.strip("'\"")
    # Fallback: scan children for a string literal or identifier chain
    for child in node.children:
        if child.type in ("string", "string_literal", "scoped_identifier",
                          "qualified_name", "namespace_name"):
            return _node_text(child, source).strip().strip("'\"")
    return _node_text(node, source).strip()
