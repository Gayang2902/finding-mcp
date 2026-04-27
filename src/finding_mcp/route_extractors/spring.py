"""Extract Spring Java routes using tree-sitter AST."""

from __future__ import annotations

from pathlib import Path

from ..models import CodeLocation, RouteDefinition
from ..treesitter_index import TreeSitterError, _node_text, _walk, parse_file

MAPPING_ANNOTATIONS = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
    "RequestMapping": "REQUEST",
}

METHOD_MAPPING_ANNOTATIONS = {
    "GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping",
}

AUTH_ANNOTATIONS = {"PreAuthorize", "Secured", "RolesAllowed"}


def _annotation_name(node, source: bytes) -> str | None:
    if node.type not in ("marker_annotation", "annotation"):
        return None
    name_node = node.child_by_field_name("name")
    if name_node is None:
        return None
    return _node_text(name_node, source)


def _annotation_path(node, source: bytes) -> str:
    args_node = node.child_by_field_name("arguments")
    if args_node is None:
        return ""
    text = _node_text(args_node, source)
    text = text.strip("()")
    if "=" in text:
        for part in text.split(","):
            part = part.strip()
            if part.startswith("value") or part.startswith("path"):
                _, _, val = part.partition("=")
                text = val.strip()
                break
    if text.startswith("{"):
        text = text.strip("{}")
        text = text.split(",")[0].strip()
    return text.strip("'\"")


def _is_method_level(node, source: bytes) -> bool:
    """True if annotation's grandparent is method_declaration (via modifiers)."""
    parent = node.parent
    if parent is None:
        return False
    # annotation -> modifiers -> method_declaration
    gp = parent.parent
    return gp is not None and gp.type == "method_declaration"


def _get_class_prefix(node, source: bytes) -> str | None:
    """Walk up from annotation to find class-level @RequestMapping prefix.

    Path: annotation -> modifiers -> method_declaration -> class_body -> class_declaration
    Then scan class_declaration's modifiers child for @RequestMapping.
    """
    cur = node.parent
    while cur is not None:
        if cur.type == "class_declaration":
            # Find the modifiers child of the class
            for child in cur.children:
                if child.type == "modifiers":
                    for ann in child.children:
                        name = _annotation_name(ann, source)
                        if name == "RequestMapping":
                            return _annotation_path(ann, source)
            return None
        cur = cur.parent
    return None


def _get_method_name(node, source: bytes) -> str | None:
    """Find the enclosing method_declaration and return its name."""
    cur = node.parent
    while cur is not None:
        if cur.type == "method_declaration":
            name_node = cur.child_by_field_name("name")
            if name_node:
                return _node_text(name_node, source)
            return None
        cur = cur.parent
    return None


def _get_method_auth(node, source: bytes) -> list[str]:
    """Check sibling annotations in the same modifiers node for auth annotations."""
    auth: list[str] = []
    # The annotation sits inside a modifiers node
    modifiers = node.parent
    if modifiers is not None and modifiers.type == "modifiers":
        for child in modifiers.children:
            name = _annotation_name(child, source)
            if name in AUTH_ANNOTATIONS:
                auth.append(name)

    # Also check class-level modifiers
    cur = node.parent
    while cur is not None:
        if cur.type == "class_declaration":
            for child in cur.children:
                if child.type == "modifiers":
                    for ann in child.children:
                        name = _annotation_name(ann, source)
                        if name in AUTH_ANNOTATIONS:
                            auth.append(name)
            break
        cur = cur.parent

    return auth


def extract(project_root: Path, files: list[Path]) -> tuple[list[RouteDefinition], list[str]]:
    routes: list[RouteDefinition] = []

    for fpath in files:
        try:
            cached = parse_file(fpath)
        except TreeSitterError:
            continue
        if cached.language != "java":
            continue

        rel_path = str(fpath.relative_to(project_root))

        for node in _walk(cached.root):
            ann_name = _annotation_name(node, cached.source)
            if ann_name is None or ann_name not in MAPPING_ANNOTATIONS:
                continue

            # Skip class-level annotations (they are prefixes, not routes)
            if not _is_method_level(node, cached.source):
                continue

            http_method = MAPPING_ANNOTATIONS[ann_name]
            path = _annotation_path(node, cached.source)

            if ann_name == "RequestMapping":
                args_node = node.child_by_field_name("arguments")
                if args_node:
                    args_text = _node_text(args_node, cached.source)
                    for m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                        if m in args_text:
                            http_method = m
                            break

            class_prefix = _get_class_prefix(node, cached.source)
            handler_name = _get_method_name(node, cached.source)
            auth_middleware = _get_method_auth(node, cached.source)

            full_path = path
            if class_prefix:
                full_path = class_prefix.rstrip("/") + "/" + path.lstrip("/")

            routes.append(RouteDefinition(
                http_method=http_method,
                path=full_path,
                handler_name=handler_name,
                middleware=auth_middleware,
                has_auth_middleware=len(auth_middleware) > 0,
                framework="spring",
                location=CodeLocation(
                    file_path=rel_path,
                    line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                ),
                class_prefix=class_prefix,
            ))

    return routes, []
