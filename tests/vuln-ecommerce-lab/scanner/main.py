"""
CLI entry point for the vulnerability scanner.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler

from scanner.agents.orchestrator import AGENT_REGISTRY, ScanOrchestrator
from scanner.config.settings import Settings
from scanner.reporters.console_reporter import ConsoleReporter
from scanner.reporters.html_reporter import HTMLReporter
from scanner.reporters.json_reporter import JSONReporter
from scanner.reporters.sarif_reporter import SARIFReporter

console = Console()


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=verbose)],
    )
    # Quiet noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def _build_settings(
    target: Optional[str],
    llm_url: Optional[str],
    llm_model: Optional[str],
) -> Settings:
    overrides = {}
    if target:
        overrides["target_url"] = target
    if llm_url:
        overrides["llm_base_url"] = llm_url
    if llm_model:
        overrides["llm_model"] = llm_model
    return Settings(**overrides)


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option("1.0.0", prog_name="vuln-scanner")
def cli() -> None:
    """LLM-powered API vulnerability scanner for e-commerce applications."""


# ---------------------------------------------------------------------------
# scan command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--target", "-t", default=None, help="Target API base URL")
@click.option("--llm-url", default=None, help="LLM API base URL (OpenAI-compatible)")
@click.option("--llm-model", default=None, help="LLM model name")
@click.option("--output", "-o", default="./reports", help="Output directory for reports")
@click.option("--agents", "-a", default=None, help="Comma-separated agent names (default: all)")
@click.option("--threads", default=3, help="Max concurrent agents")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
@click.option("--no-llm", is_flag=True, help="Disable LLM analysis (fast mode)")
@click.option(
    "--format",
    "-f",
    "output_format",
    multiple=True,
    type=click.Choice(["html", "json", "sarif", "console"]),
    default=["html", "json", "console"],
    help="Output format(s)",
)
def scan(
    target: Optional[str],
    llm_url: Optional[str],
    llm_model: Optional[str],
    output: str,
    agents: Optional[str],
    threads: int,
    verbose: bool,
    no_llm: bool,
    output_format: tuple,
) -> None:
    """Run the full vulnerability scan pipeline."""
    _configure_logging(verbose)
    settings = _build_settings(target, llm_url, llm_model)

    if no_llm:
        settings.enable_llm_analysis = False
        console.print("[yellow]LLM analysis disabled (fast mode)[/yellow]")

    agent_list = [a.strip() for a in agents.split(",")] if agents else None

    console.print(f"[bold blue]VulnScanner[/bold blue] v1.0.0")
    console.print(f"Target: [bold]{settings.target_url}[/bold]")
    console.print(f"LLM: [bold]{settings.llm_model}[/bold] @ {settings.llm_base_url}")

    orchestrator = ScanOrchestrator(settings)
    report = asyncio.run(orchestrator.run_full_scan(agents=agent_list, max_concurrency=threads))

    # Generate reports
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output, exist_ok=True)

    for fmt in set(output_format):
        if fmt == "html":
            path = os.path.join(output, f"report_{ts}.html")
            HTMLReporter().generate(report, path)
            console.print(f"[green]HTML report:[/green] {path}")
        elif fmt == "json":
            path = os.path.join(output, f"report_{ts}.json")
            JSONReporter().generate(report, path)
            console.print(f"[green]JSON report:[/green] {path}")
        elif fmt == "sarif":
            path = os.path.join(output, f"report_{ts}.sarif")
            SARIFReporter().generate(report, path)
            console.print(f"[green]SARIF report:[/green] {path}")
        elif fmt == "console":
            ConsoleReporter(verbose=verbose).print_full_report(report)

    total = report.summary_stats.get("TOTAL", 0)
    critical = report.summary_stats.get("CRITICAL", 0)
    high = report.summary_stats.get("HIGH", 0)

    # Exit code: 1 if critical/high findings, 0 otherwise
    sys.exit(1 if (critical + high) > 0 else 0)


# ---------------------------------------------------------------------------
# discover command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--target", "-t", default=None, help="Target API base URL")
@click.option("--output", "-o", default="./reports/endpoints.json", help="Output file")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def discover(target: Optional[str], output: str, verbose: bool) -> None:
    """Run endpoint discovery only and export the endpoint map."""
    _configure_logging(verbose)
    settings = _build_settings(target, None, None)

    console.print(f"Discovering endpoints at [bold]{settings.target_url}[/bold]")

    async def _run() -> None:
        from scanner.config.test_users import authenticate_all
        from scanner.crawlers.api_crawler import APICrawler
        from scanner.models.scan_context import ScanContext
        from scanner.utils.http_client import AsyncHTTPClient
        from scanner.utils.id_collector import IDCollector
        import json

        async with AsyncHTTPClient(base_url=settings.target_url) as http:
            ctx = ScanContext(target_url=settings.target_url)
            ids = IDCollector()
            try:
                authenticated = await authenticate_all(http)
                ctx.authenticated_users = authenticated
            except RuntimeError:
                console.print("[yellow]No users authenticated — proceeding with anonymous crawl[/yellow]")

            crawler = APICrawler(http, ctx, ids)
            await crawler.run(ctx.authenticated_users)

            os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
            endpoint_map = crawler.export_endpoint_map()
            with open(output, "w") as f:
                f.write(endpoint_map)

            console.print(f"[green]Endpoint map written to {output}[/green]")
            console.print(f"Discovered {len(ctx.discovered_endpoints)} endpoints")
            console.print(f"Collected IDs: {ids.summary()}")

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# analyze command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("agent_name", type=click.Choice(list(AGENT_REGISTRY.keys())))
@click.option("--target", "-t", default=None, help="Target API base URL")
@click.option("--llm-url", default=None, help="LLM API base URL")
@click.option("--llm-model", default=None, help="LLM model name")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def analyze(
    agent_name: str,
    target: Optional[str],
    llm_url: Optional[str],
    llm_model: Optional[str],
    verbose: bool,
) -> None:
    """Run a single analysis agent."""
    _configure_logging(verbose)
    settings = _build_settings(target, llm_url, llm_model)

    console.print(f"Running agent: [bold]{agent_name}[/bold]")
    orchestrator = ScanOrchestrator(settings)
    findings = asyncio.run(orchestrator.run_single_agent(agent_name))

    reporter = ConsoleReporter(verbose=verbose)
    for v in findings:
        console.print(v.to_summary())

    console.print(f"\n[bold]Total findings: {len(findings)}[/bold]")


# ---------------------------------------------------------------------------
# report command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("json_report", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["html", "sarif", "console"]),
    default="html",
    help="Output format",
)
@click.option("--output", "-o", default=None, help="Output file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def report(json_report: str, output_format: str, output: Optional[str], verbose: bool) -> None:
    """Generate a report from an existing JSON results file."""
    _configure_logging(verbose)

    import json
    from scanner.models.vulnerability import VulnerabilityReport

    with open(json_report) as f:
        data = json.load(f)

    vuln_report = VulnerabilityReport.model_validate(data)

    if output_format == "html":
        out = output or json_report.replace(".json", ".html")
        HTMLReporter().generate(vuln_report, out)
        console.print(f"[green]HTML report: {out}[/green]")
    elif output_format == "sarif":
        out = output or json_report.replace(".json", ".sarif")
        SARIFReporter().generate(vuln_report, out)
        console.print(f"[green]SARIF report: {out}[/green]")
    elif output_format == "console":
        ConsoleReporter(verbose=verbose).print_full_report(vuln_report)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    cli()


if __name__ == "__main__":
    main()
