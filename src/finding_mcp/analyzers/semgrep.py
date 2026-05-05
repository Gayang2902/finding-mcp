"""Semgrep taint analysis runner + SARIF parser.

Runs semgrep via subprocess (same pattern as ripgrep.py / ctags_index.py),
parses SARIF output, and compacts findings for efficient AI consumption.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path


class SemgrepError(RuntimeError):
    pass


@dataclass
class TraceStep:
    file_path: str
    line: int
    content: str
    label: str


@dataclass
class TaintFinding:
    finding_id: str
    rule_id: str
    message: str
    severity: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    dataflow_trace: list[TraceStep] = field(default_factory=list)


@dataclass
class AnalysisResult:
    analysis_id: str
    commit_hash: str | None
    rule_file: str
    target_dir: str
    total_findings: int
    findings: list[TaintFinding]
    run_time_seconds: float


def run_semgrep(
    project_root: Path,
    rule_file: Path,
    target_dir: Path,
    cache_dir: Path,
    timeout: int = 300,
) -> tuple[str, Path]:
    """Run semgrep and return (analysis_id, sarif_path)."""
    analysis_id = uuid.uuid4().hex[:12]
    sarif_dir = cache_dir / "semgrep"
    sarif_dir.mkdir(parents=True, exist_ok=True)
    sarif_path = sarif_dir / f"{analysis_id}.sarif.json"

    cmd = [
        "semgrep", "scan",
        "--config", str(rule_file),
        "--sarif",
        "--sarif-output", str(sarif_path),
        "--dataflow-traces",
        "--no-git-ignore",
        "--metrics=off",
        "--quiet",
        str(target_dir),
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError as e:
        raise SemgrepError(
            "semgrep is not installed. Install via `pip install semgrep` or `brew install semgrep`."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise SemgrepError(f"semgrep timed out after {timeout}s") from e

    # 0=findings, 1=no findings, 2+=errors
    if proc.returncode not in (0, 1):
        raise SemgrepError(
            f"semgrep failed (exit {proc.returncode}): {proc.stderr.strip()[:500]}"
        )

    if proc.stderr:
        print(f"[semgrep] {proc.stderr.strip()[:300]}", file=sys.stderr)

    if not sarif_path.exists():
        raise SemgrepError("semgrep did not produce SARIF output")

    return analysis_id, sarif_path


def parse_sarif(sarif_path: Path, project_root: Path) -> list[TaintFinding]:
    """Parse SARIF JSON into TaintFinding objects."""
    with sarif_path.open("r", encoding="utf-8") as f:
        sarif = json.load(f)

    findings: list[TaintFinding] = []
    runs = sarif.get("runs", [])
    if not runs:
        return findings

    results = runs[0].get("results", [])
    for result in results:
        rule_id = result.get("ruleId", "unknown")
        message = result.get("message", {}).get("text", "")
        level = result.get("level", "note")
        severity = _map_severity(level)

        locations = result.get("locations", [])
        if not locations:
            continue

        phys = locations[0].get("physicalLocation", {})
        artifact = phys.get("artifactLocation", {})
        raw_uri = artifact.get("uri", "")
        region = phys.get("region", {})

        file_path = _normalize_uri(raw_uri, project_root)
        line_start = region.get("startLine", 0)
        line_end = region.get("endLine", line_start)
        snippet_text = region.get("snippet", {}).get("text", "")

        if not snippet_text:
            snippet_text = _read_lines(project_root / file_path, line_start, line_end)

        finding_id = hashlib.sha256(
            f"{rule_id}:{file_path}:{line_start}".encode()
        ).hexdigest()[:12]

        trace = _extract_dataflow_trace(result, project_root)

        findings.append(TaintFinding(
            finding_id=finding_id,
            rule_id=rule_id,
            message=message,
            severity=severity,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            code_snippet=snippet_text.strip(),
            dataflow_trace=trace,
        ))

    return findings


def compact_findings(findings: list[TaintFinding], gap: int = 3) -> list[TaintFinding]:
    """Merge consecutive findings from the same file within `gap` lines."""
    if not findings:
        return []

    sorted_f = sorted(findings, key=lambda f: (f.file_path, f.line_start))
    compacted: list[TaintFinding] = []
    current = sorted_f[0]

    for nxt in sorted_f[1:]:
        if (nxt.file_path == current.file_path
                and nxt.rule_id == current.rule_id
                and nxt.line_start <= current.line_end + gap):
            current = TaintFinding(
                finding_id=current.finding_id,
                rule_id=current.rule_id,
                message=current.message,
                severity=_higher_severity(current.severity, nxt.severity),
                file_path=current.file_path,
                line_start=current.line_start,
                line_end=max(current.line_end, nxt.line_end),
                code_snippet=current.code_snippet + "\n" + nxt.code_snippet,
                dataflow_trace=current.dataflow_trace + nxt.dataflow_trace,
            )
        else:
            compacted.append(current)
            current = nxt

    compacted.append(current)
    return compacted


def _extract_dataflow_trace(result: dict, project_root: Path) -> list[TraceStep]:
    code_flows = result.get("codeFlows", [])
    if not code_flows:
        return []

    thread_flows = code_flows[0].get("threadFlows", [])
    if not thread_flows:
        return []

    locations = thread_flows[0].get("locations", [])
    steps: list[TraceStep] = []
    total = len(locations)

    for i, loc in enumerate(locations):
        phys = loc.get("location", {}).get("physicalLocation", {})
        artifact = phys.get("artifactLocation", {})
        region = phys.get("region", {})
        raw_uri = artifact.get("uri", "")
        file_path = _normalize_uri(raw_uri, project_root)
        line = region.get("startLine", 0)
        content = region.get("snippet", {}).get("text", "").strip()

        if i == 0:
            label = "source"
        elif i == total - 1:
            label = "sink"
        else:
            label = "propagator"

        steps.append(TraceStep(
            file_path=file_path,
            line=line,
            content=content,
            label=label,
        ))

    return steps


def _normalize_uri(uri: str, project_root: Path) -> str:
    cleaned = uri.replace("file://", "")
    try:
        return str(Path(cleaned).resolve().relative_to(project_root))
    except ValueError:
        return cleaned


def _read_lines(file_path: Path, start: int, end: int) -> str:
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[max(0, start - 1):end])
    except (FileNotFoundError, OSError):
        return ""


def _map_severity(level: str) -> str:
    return {"error": "ERROR", "warning": "WARNING", "note": "INFO"}.get(level, "INFO")


def _higher_severity(a: str, b: str) -> str:
    order = {"ERROR": 3, "WARNING": 2, "INFO": 1}
    return a if order.get(a, 0) >= order.get(b, 0) else b
