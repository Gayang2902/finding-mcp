"""Response models. All tool outputs include file path, line, and commit hash
so the LLM can chain calls deterministically.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CodeLocation(BaseModel):
    """A point or span in the codebase. The minimum unit of cross-tool reference."""

    file_path: str = Field(description="Path relative to project root")
    line: int = Field(description="1-indexed start line")
    end_line: int | None = Field(default=None, description="1-indexed end line (inclusive)")
    column: int | None = Field(default=None, description="1-indexed column")


class SymbolDefinition(BaseModel):
    name: str
    kind: str = Field(description="ctags kind: function, method, class, variable, ...")
    location: CodeLocation
    signature: str | None = None
    language: str | None = None
    scope: str | None = Field(default=None, description="Enclosing class/namespace if any")


class SymbolReference(BaseModel):
    location: CodeLocation
    line_text: str = Field(description="The matched line, trimmed")


class FunctionBody(BaseModel):
    name: str
    location: CodeLocation
    signature: str
    body: str
    language: str
    truncated: bool = False


class CallSite(BaseModel):
    """A call expression discovered by tree-sitter or ripgrep."""

    callee: str
    location: CodeLocation
    line_text: str


class ImportEntry(BaseModel):
    raw: str = Field(description="Original import/use/require text")
    target: str = Field(description="Imported module/class/symbol")
    location: CodeLocation


class SearchHit(BaseModel):
    location: CodeLocation
    line_text: str
    match_text: str | None = None


class FileEntry(BaseModel):
    path: str
    size_bytes: int
    language: str | None = None


class RepoInfo(BaseModel):
    project_root: str
    commit_hash: str | None = Field(
        default=None, description="HEAD commit hash, or null if not a git repo / dirty"
    )
    is_dirty: bool = False
    languages: dict[str, int] = Field(
        default_factory=dict, description="Language -> file count"
    )
    total_files: int = 0


# --- Wrapper types for paginated/truncated responses ---


class PaginatedResponse(BaseModel):
    """Wraps a list with truncation/cursor metadata."""

    items: list[Any]
    total: int | None = None
    truncated: bool = False
    next_cursor: str | None = None
    commit_hash: str | None = None


# --- Taint analysis models ---


class TaintFindingSummary(BaseModel):
    finding_id: str
    rule_id: str
    severity: str
    file_path: str
    line_start: int
    message_preview: str = Field(description="First 120 chars of the message")


class TraceStep(BaseModel):
    file_path: str
    line: int
    content: str = Field(description="Source code at this trace step")
    label: str = Field(description="source | propagator | sink")


class TaintFindingDetail(BaseModel):
    finding_id: str
    rule_id: str
    message: str
    severity: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    dataflow_trace: list[TraceStep] = Field(default_factory=list)
    commit_hash: str | None = None


class AnalysisSummary(BaseModel):
    analysis_id: str
    total_findings: int
    rule_file: str
    target_dir: str
    run_time_seconds: float
    commit_hash: str | None = None


# --- Route extraction models ---


class RouteDefinition(BaseModel):
    http_method: str
    path: str
    handler_name: str | None = None
    middleware: list[str] = Field(default_factory=list)
    has_auth_middleware: bool = False
    framework: str
    location: CodeLocation
    class_prefix: str | None = None


class FrameworkDetection(BaseModel):
    framework: str
    language: str
    confidence: str
    evidence: str


class RouteMapResult(BaseModel):
    routes: list[RouteDefinition]
    frameworks_detected: list[FrameworkDetection]
    global_middleware: list[str] = Field(default_factory=list)
    total_routes: int
    files_scanned: int
    commit_hash: str | None = None


class AuthCoverageResult(BaseModel):
    total_routes: int
    protected_count: int
    unprotected_count: int
    unprotected_routes: list[RouteDefinition]
    auth_patterns_detected: list[str] = Field(default_factory=list)
    commit_hash: str | None = None
