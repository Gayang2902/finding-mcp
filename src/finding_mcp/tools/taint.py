"""Taint analysis tools backed by Semgrep."""

from __future__ import annotations

import importlib.resources
import threading
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ..analyzers import semgrep
from ..config import Settings
from ..core.git_utils import cache_key
from ..models import (
    AnalysisSummary,
    PaginatedResponse,
    TaintFindingDetail,
    TaintFindingSummary,
    TraceStep,
)

_ANALYSES: dict[str, semgrep.AnalysisResult] = {}
_ANALYSES_MAX = 10
_LOCK = threading.Lock()

LANGUAGE_RULE_MAP = {
    "java": "java_spring_taint.yaml",
    "php": "php_taint.yaml",
    "javascript": "js_taint.yaml",
    "typescript": "js_taint.yaml",
    "tsx": "js_taint.yaml",
}


def _get_builtin_rule(filename: str) -> Path:
    rules_pkg = importlib.resources.files("finding_mcp.rules")
    resource = rules_pkg.joinpath(filename)
    return Path(str(resource))


def _get_rules_for_language(language: str | None) -> list[Path]:
    if language and language in LANGUAGE_RULE_MAP:
        return [_get_builtin_rule(LANGUAGE_RULE_MAP[language])]
    return [_get_builtin_rule(f) for f in set(LANGUAGE_RULE_MAP.values())]


def run_taint_analysis(
    settings: Settings,
    rule_file: str | None = None,
    language: str | None = None,
    target_dir: str | None = None,
) -> dict:
    root = settings.require_project_root()
    target = root
    if target_dir:
        target = (root / target_dir).resolve()
        try:
            target.relative_to(root)
        except ValueError as e:
            raise ValueError(f"target_dir must be inside project root: {target_dir}") from e

    if rule_file:
        rule_path = Path(rule_file)
        if not rule_path.is_absolute():
            rule_path = root / rule_path
        if not rule_path.exists():
            raise FileNotFoundError(f"Rule file not found: {rule_file}")
        rule_paths = [rule_path]
    else:
        rule_paths = _get_rules_for_language(language)

    all_findings: list[semgrep.TaintFinding] = []
    total_time = 0.0
    rule_names: list[str] = []

    for rp in rule_paths:
        rule_names.append(rp.name)
        start = time.monotonic()
        analysis_id, sarif_path = semgrep.run_semgrep(
            root, rp, target, settings.cache_dir,
            timeout=settings.semgrep_timeout,
        )
        elapsed = time.monotonic() - start
        total_time += elapsed

        findings = semgrep.parse_sarif(sarif_path, root)
        all_findings.extend(findings)

    compacted = semgrep.compact_findings(all_findings)
    if len(compacted) > settings.semgrep_max_findings:
        compacted = compacted[:settings.semgrep_max_findings]

    result = semgrep.AnalysisResult(
        analysis_id=analysis_id if len(rule_paths) == 1 else f"multi-{analysis_id}",
        commit_hash=cache_key(root),
        rule_file=", ".join(rule_names),
        target_dir=str(target),
        total_findings=len(compacted),
        findings=compacted,
        run_time_seconds=round(total_time, 2),
    )

    with _LOCK:
        if len(_ANALYSES) >= _ANALYSES_MAX:
            oldest_key = next(iter(_ANALYSES))
            del _ANALYSES[oldest_key]
        _ANALYSES[result.analysis_id] = result

    return AnalysisSummary(
        analysis_id=result.analysis_id,
        total_findings=result.total_findings,
        rule_file=result.rule_file,
        target_dir=str(target),
        run_time_seconds=result.run_time_seconds,
        commit_hash=result.commit_hash,
    ).model_dump()


def get_taint_paths(
    settings: Settings,
    analysis_id: str,
    limit: int = 20,
    offset: int = 0,
) -> PaginatedResponse:
    with _LOCK:
        result = _ANALYSES.get(analysis_id)
    if result is None:
        raise KeyError(f"Analysis not found: {analysis_id}. Run run_taint_analysis() first.")

    findings = result.findings
    page = findings[offset:offset + limit]
    summaries = [
        TaintFindingSummary(
            finding_id=f.finding_id,
            rule_id=f.rule_id,
            severity=f.severity,
            file_path=f.file_path,
            line_start=f.line_start,
            message_preview=f.message[:120],
        ).model_dump()
        for f in page
    ]

    return PaginatedResponse(
        items=summaries,
        total=len(findings),
        truncated=(offset + limit) < len(findings),
        commit_hash=result.commit_hash,
    )


def get_taint_path_detail(
    settings: Settings,
    analysis_id: str,
    finding_id: str,
) -> dict:
    with _LOCK:
        result = _ANALYSES.get(analysis_id)
    if result is None:
        raise KeyError(f"Analysis not found: {analysis_id}")

    for f in result.findings:
        if f.finding_id == finding_id:
            return TaintFindingDetail(
                finding_id=f.finding_id,
                rule_id=f.rule_id,
                message=f.message,
                severity=f.severity,
                file_path=f.file_path,
                line_start=f.line_start,
                line_end=f.line_end,
                code_snippet=f.code_snippet,
                dataflow_trace=[
                    TraceStep(
                        file_path=s.file_path,
                        line=s.line,
                        content=s.content,
                        label=s.label,
                    )
                    for s in f.dataflow_trace
                ],
                commit_hash=result.commit_hash,
            ).model_dump()

    raise KeyError(f"Finding not found: {finding_id}")


def list_analyses(settings: Settings) -> dict:
    with _LOCK:
        items = [
            AnalysisSummary(
                analysis_id=r.analysis_id,
                total_findings=r.total_findings,
                rule_file=r.rule_file,
                target_dir=r.target_dir,
                run_time_seconds=r.run_time_seconds,
                commit_hash=r.commit_hash,
            ).model_dump()
            for r in _ANALYSES.values()
        ]
    return {"analyses": items}


def register(mcp: FastMCP, settings: Settings) -> None:
    @mcp.tool(name="run_taint_analysis")
    def _run_taint_analysis(
        rule_file: str | None = None,
        language: str | None = None,
        target_dir: str | None = None,
    ) -> dict:
        """Run Semgrep taint analysis to extract all Source->Sink data flow paths.

        If rule_file is not provided, uses built-in taint rules for the specified
        language (java, php, javascript). If language is also None, runs all built-in rules.

        Returns an analysis_id. Use get_taint_paths() to retrieve results.
        """
        return run_taint_analysis(settings, rule_file, language, target_dir)

    @mcp.tool(name="get_taint_paths")
    def _get_taint_paths(
        analysis_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List taint findings from a completed analysis (paginated summaries).

        Each result includes finding_id — use get_taint_path_detail() to inspect
        one path at a time for consistent, thorough analysis.
        """
        result = get_taint_paths(settings, analysis_id, limit, offset)
        return result.model_dump()

    @mcp.tool(name="get_taint_path_detail")
    def _get_taint_path_detail(
        analysis_id: str,
        finding_id: str,
    ) -> dict:
        """Get full detail for one taint finding: code snippet, dataflow trace.

        Analyze one path at a time for consistency. Cross-reference with
        get_function_at() and get_callees() to validate the finding.
        """
        return get_taint_path_detail(settings, analysis_id, finding_id)

    @mcp.tool(name="list_taint_analyses")
    def _list_taint_analyses() -> dict:
        """List all completed taint analysis runs with their IDs and finding counts."""
        return list_analyses(settings)
