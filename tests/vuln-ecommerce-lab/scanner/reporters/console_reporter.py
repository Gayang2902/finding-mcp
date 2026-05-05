"""
Console reporter — Rich-formatted terminal output.
"""

from __future__ import annotations

from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from scanner.models.vulnerability import Severity, VulnerabilityReport

console = Console()

_SEVERITY_STYLES: Dict[str, str] = {
    "CRITICAL": "bold red",
    "HIGH": "bold orange3",
    "MEDIUM": "bold yellow",
    "LOW": "bold blue",
    "INFO": "dim",
}


class ConsoleReporter:
    """Prints scan results to the terminal using Rich formatting."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def print_summary(self, report: VulnerabilityReport) -> None:
        """Print executive summary table."""
        stats = report.summary_stats
        table = Table(title="[bold]Scan Summary[/bold]", show_header=True, header_style="bold")
        table.add_column("Severity", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Bar", no_wrap=True)

        total = max(stats.get("TOTAL", 1), 1)
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
            count = stats.get(sev, 0)
            bar = "█" * min(count * 20 // total, 20) if count else ""
            style = _SEVERITY_STYLES[sev]
            table.add_row(
                Text(sev, style=style),
                str(count),
                Text(bar, style=style),
            )
        table.add_section()
        table.add_row("[bold]TOTAL[/bold]", str(stats.get("TOTAL", 0)), "")
        console.print(table)

        meta = report.metadata
        console.print(
            f"\n[bold]Risk Score:[/bold] [red]{report.risk_score}[/red] | "
            f"[bold]Target:[/bold] {meta.target_url} | "
            f"[bold]Duration:[/bold] {meta.duration_seconds:.0f}s | "
            f"[bold]Requests:[/bold] {meta.total_requests}"
        )

    def print_findings(self, report: VulnerabilityReport) -> None:
        """Print detailed finding cards."""
        sorted_vulns = sorted(report.vulnerabilities, key=lambda v: v.severity_score, reverse=True)

        for vuln in sorted_vulns:
            style = _SEVERITY_STYLES.get(vuln.severity.value, "")
            header = f"[{style}][{vuln.severity.value}][/{style}] {vuln.title}"

            content_lines = [
                f"[bold]Type:[/bold]        {vuln.type.value}",
                f"[bold]Endpoint:[/bold]    {vuln.method} {vuln.endpoint}",
                f"[bold]Agent:[/bold]       {vuln.agent_name}",
                f"[bold]Confidence:[/bold]  {vuln.confidence:.0%}",
                f"[bold]CWE:[/bold]         {vuln.cwe_id or 'N/A'}",
                "",
                f"[bold]Description:[/bold] {vuln.description}",
                "",
                f"[bold]Impact:[/bold]      {vuln.impact}",
                f"[bold]Remediation:[/bold] {vuln.remediation}",
            ]

            if self.verbose and vuln.reproduction_steps:
                content_lines.append("")
                content_lines.append("[bold]Reproduction:[/bold]")
                for step in vuln.reproduction_steps:
                    content_lines.append(f"  {step}")

            console.print(Panel(
                "\n".join(content_lines),
                title=header,
                border_style=style.replace("bold ", "") if style else "white",
                padding=(0, 1),
            ))
            console.print()

    def print_endpoint_tree(self, report: VulnerabilityReport) -> None:
        """Print a tree view of tested endpoints with finding counts."""
        vuln_map: Dict[str, int] = {}
        for v in report.vulnerabilities:
            vuln_map[v.endpoint] = vuln_map.get(v.endpoint, 0) + 1

        tree = Tree("[bold]Endpoint Coverage[/bold]")
        for ep in sorted(set(v.endpoint for v in report.vulnerabilities)):
            count = vuln_map.get(ep, 0)
            label = f"{ep} — [red]{count} finding{'s' if count != 1 else ''}[/red]"
            tree.add(label)

        console.print(tree)

    def print_full_report(self, report: VulnerabilityReport) -> None:
        """Print complete report: summary + findings + coverage."""
        console.rule("[bold]Vulnerability Scan Report[/bold]")
        self.print_summary(report)
        console.print()
        console.rule("[bold]Findings[/bold]")
        self.print_findings(report)
        if report.vulnerabilities:
            console.rule("[bold]Endpoint Coverage[/bold]")
            self.print_endpoint_tree(report)
