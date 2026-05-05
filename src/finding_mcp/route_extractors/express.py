"""Extract Express.js routes using tree-sitter AST."""

from __future__ import annotations

from pathlib import Path

from ..indexers.treesitter import TreeSitterError, _node_text, _walk, parse_file
from ..models import CodeLocation, RouteDefinition

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "all"}


def _is_route_call(node, source: bytes) -> tuple[str, bool] | None:
    """Check if node is app.METHOD() or router.METHOD(). Returns (method, True) or None."""
    if node.type != "call_expression":
        return None
    callee = node.child_by_field_name("function")
    if callee is None or callee.type != "member_expression":
        return None
    prop = callee.child_by_field_name("property")
    if prop is None:
        return None
    method = _node_text(prop, source).lower()
    if method not in HTTP_METHODS and method != "use":
        return None
    return method, method == "use"


def _extract_string(node, source: bytes) -> str | None:
    if node.type in ("string", "template_string"):
        text = _node_text(node, source)
        return text.strip("'\"`")
    return None


def extract(project_root: Path, files: list[Path]) -> tuple[list[RouteDefinition], list[str]]:
    routes: list[RouteDefinition] = []
    global_middleware: list[str] = []

    for fpath in files:
        try:
            cached = parse_file(fpath)
        except TreeSitterError:
            continue
        if cached.language not in ("javascript", "typescript", "tsx"):
            continue

        rel_path = str(fpath.relative_to(project_root))

        for node in _walk(cached.root):
            result = _is_route_call(node, cached.source)
            if result is None:
                continue
            method, is_use = result

            args_node = node.child_by_field_name("arguments")
            if args_node is None:
                continue
            args = [c for c in args_node.children if c.type not in ("(", ")", ",")]
            if not args:
                continue

            if is_use:
                # app.use(path?, middleware...)
                first_str = _extract_string(args[0], cached.source)
                if first_str:
                    mw_args = args[1:]
                else:
                    mw_args = args
                for mw in mw_args:
                    mw_name = _node_text(mw, cached.source).strip()
                    global_middleware.append(mw_name)
                continue

            # Route call: app.get(path, ...middleware, handler)
            path_str = _extract_string(args[0], cached.source)
            if path_str is None:
                continue

            middleware: list[str] = []
            handler_name: str | None = None

            if len(args) > 1:
                # Last arg is handler, middle args are middleware
                for mw_node in args[1:-1]:
                    middleware.append(_node_text(mw_node, cached.source).strip())
                last = args[-1]
                handler_name = _node_text(last, cached.source).strip()
                # Clean up arrow/anonymous functions to just show name or <anonymous>
                if last.type in ("arrow_function", "function_expression"):
                    handler_name = "<anonymous>"
                elif last.type == "identifier":
                    handler_name = _node_text(last, cached.source).strip()

            routes.append(RouteDefinition(
                http_method=method.upper(),
                path=path_str,
                handler_name=handler_name,
                middleware=middleware,
                has_auth_middleware=False,
                framework="express",
                location=CodeLocation(
                    file_path=rel_path,
                    line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                ),
            ))

    return routes, global_middleware
