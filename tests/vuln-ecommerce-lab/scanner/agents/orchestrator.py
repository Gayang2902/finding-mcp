"""
Scan orchestrator — manages the full vulnerability scan pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from scanner.agents.base_agent import BaseAnalysisAgent
from scanner.agents.business_logic_agent import BusinessLogicAgent
from scanner.agents.idor_agent import IDORAgent
from scanner.agents.missing_access_control_agent import MissingAccessControlAgent
from scanner.agents.parameter_tampering_agent import ParameterTamperingAgent
from scanner.agents.privilege_escalation_agent import PrivilegeEscalationAgent
from scanner.config.settings import Settings
from scanner.config.test_users import authenticate_all
from scanner.crawlers.api_crawler import APICrawler
from scanner.crawlers.auth_crawler import AuthCrawler
from scanner.models.scan_context import ScanContext
from scanner.models.vulnerability import ScanMetadata, Vulnerability, VulnerabilityReport
from scanner.utils.http_client import AsyncHTTPClient
from scanner.utils.id_collector import IDCollector
from scanner.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)
console = Console()

# Registry of available agents
AGENT_REGISTRY: Dict[str, Type[BaseAnalysisAgent]] = {
    "idor": IDORAgent,
    "parameter_tampering": ParameterTamperingAgent,
    "privilege_escalation": PrivilegeEscalationAgent,
    "missing_access_control": MissingAccessControlAgent,
    "business_logic": BusinessLogicAgent,
}


class ScanOrchestrator:
    """
    Orchestrates the full scan pipeline:
      1. Initialize clients
      2. API discovery (crawl + enumerate IDs)
      3. Auth mapping
      4. Parallel agent execution
      5. Deduplication + confidence filtering
      6. Report generation
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._http: Optional[AsyncHTTPClient] = None
        self._llm: Optional[LLMClient] = None
        self._ctx: Optional[ScanContext] = None
        self._id_collector = IDCollector()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_full_scan(
        self,
        agents: Optional[List[str]] = None,
        max_concurrency: int = 3,
    ) -> VulnerabilityReport:
        """
        Execute the complete scan pipeline.

        Args:
            agents: List of agent names to run (None = all)
            max_concurrency: Max agents to run in parallel

        Returns:
            VulnerabilityReport with all findings
        """
        scan_start = datetime.utcnow()
        console.print(f"[bold green]Starting scan[/bold green] → {self._settings.target_url}")

        async with self._create_http_client() as http:
            self._http = http
            self._llm = self._create_llm_client()
            self._ctx = ScanContext(target_url=self._settings.target_url, scan_start=scan_start)

            # Phase 1: Authentication
            with _progress_context("Authenticating test users") as progress:
                task = progress.add_task("auth", total=None)
                await self._phase_authenticate()
                progress.update(task, completed=True)

            # Phase 2: API Discovery
            with _progress_context("Discovering API endpoints") as progress:
                task = progress.add_task("crawl", total=None)
                await self._phase_discover()
                progress.update(task, completed=True)

            # Phase 3: Auth mapping
            with _progress_context("Mapping access control") as progress:
                task = progress.add_task("auth_map", total=None)
                await self._phase_auth_mapping()
                progress.update(task, completed=True)

            # Phase 4: Agent analysis
            agent_names = agents or list(AGENT_REGISTRY.keys())
            console.print(f"[bold]Running agents:[/bold] {', '.join(agent_names)}")

            all_findings: List[Vulnerability] = []
            semaphore = asyncio.Semaphore(max_concurrency)

            async def run_agent(name: str) -> List[Vulnerability]:
                async with semaphore:
                    return await self._run_agent(name)

            results = await asyncio.gather(
                *[run_agent(name) for name in agent_names],
                return_exceptions=True,
            )
            for r in results:
                if isinstance(r, Exception):
                    logger.error("Agent failed: %s", r)
                elif isinstance(r, list):
                    all_findings.extend(r)

        # Phase 5: Build report
        scan_end = datetime.utcnow()
        report = self._build_report(all_findings, scan_start, scan_end, agent_names)
        self._print_summary(report)
        return report

    async def run_single_agent(self, agent_name: str) -> List[Vulnerability]:
        """
        Run a single agent. Requires the pipeline to be initialized.
        """
        async with self._create_http_client() as http:
            self._http = http
            self._llm = self._create_llm_client()
            self._ctx = ScanContext(target_url=self._settings.target_url)

            await self._phase_authenticate()
            await self._phase_discover()

            return await self._run_agent(agent_name)

    # ------------------------------------------------------------------
    # Pipeline phases
    # ------------------------------------------------------------------

    async def _phase_authenticate(self) -> None:
        assert self._http is not None and self._ctx is not None
        try:
            authenticated = await authenticate_all(self._http)
            self._ctx.authenticated_users = authenticated
            logger.info("Authenticated %d users", len(authenticated))
        except RuntimeError as exc:
            logger.warning("Authentication phase failed: %s", exc)
            console.print(f"[yellow]Warning: {exc}[/yellow]")

    async def _phase_discover(self) -> None:
        assert self._http is not None and self._ctx is not None
        crawler = APICrawler(self._http, self._ctx, self._id_collector)
        await crawler.run(self._ctx.authenticated_users)
        self._ctx.total_requests = self._http.request_count

    async def _phase_auth_mapping(self) -> None:
        assert self._http is not None and self._ctx is not None
        auth_crawler = AuthCrawler(self._http, self._ctx)
        await auth_crawler.run(self._ctx.authenticated_users)

    async def _run_agent(self, agent_name: str) -> List[Vulnerability]:
        assert self._http is not None and self._llm is not None and self._ctx is not None

        agent_cls = AGENT_REGISTRY.get(agent_name)
        if agent_cls is None:
            logger.error("Unknown agent: %s. Available: %s", agent_name, list(AGENT_REGISTRY))
            return []

        console.print(f"  [cyan]→ Running {agent_name}[/cyan]")
        t0 = time.monotonic()
        try:
            agent = agent_cls(self._http, self._llm, self._ctx, self._settings)
            findings = await agent.analyze()
            elapsed = time.monotonic() - t0
            console.print(
                f"  [green]✓ {agent_name}[/green]: {len(findings)} findings ({elapsed:.1f}s)"
            )
            return findings
        except Exception as exc:
            elapsed = time.monotonic() - t0
            logger.exception("Agent %s failed after %.1fs: %s", agent_name, elapsed, exc)
            console.print(f"  [red]✗ {agent_name} failed: {exc}[/red]")
            return []

    # ------------------------------------------------------------------
    # Report construction
    # ------------------------------------------------------------------

    def _build_report(
        self,
        findings: List[Vulnerability],
        scan_start: datetime,
        scan_end: datetime,
        agents_used: List[str],
    ) -> VulnerabilityReport:
        assert self._ctx is not None and self._http is not None

        metadata = ScanMetadata(
            target_url=self._settings.target_url,
            scan_start=scan_start,
            scan_end=scan_end,
            agents_used=agents_used,
            llm_model=self._settings.llm_model,
            total_requests=self._http.request_count,
            endpoints_tested=len(self._ctx.discovered_endpoints),
            duration_seconds=(scan_end - scan_start).total_seconds(),
        )

        report = VulnerabilityReport(metadata=metadata, vulnerabilities=findings)

        # Deduplicate and filter by confidence
        report = report.deduplicate()
        report = report.filter_by_confidence(self._settings.confidence_threshold)

        return report

    # ------------------------------------------------------------------
    # Client factories
    # ------------------------------------------------------------------

    def _create_http_client(self) -> AsyncHTTPClient:
        return AsyncHTTPClient(
            base_url=self._settings.target_url,
            timeout=self._settings.request_timeout,
            retry_attempts=self._settings.retry_attempts,
            rate_limit_rps=self._settings.rate_limit_rps,
            proxy=self._settings.http_proxy,
        )

    def _create_llm_client(self) -> LLMClient:
        return LLMClient(
            base_url=self._settings.llm_base_url,
            model=self._settings.llm_model,
            api_key=self._settings.llm_api_key,
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
            enable_cache=self._settings.enable_llm_cache,
        )

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _print_summary(self, report: VulnerabilityReport) -> None:
        stats = report.summary_stats
        table = Table(title="Scan Summary", show_header=True)
        table.add_column("Severity", style="bold")
        table.add_column("Count", justify="right")

        colors = {"CRITICAL": "red", "HIGH": "orange3", "MEDIUM": "yellow", "LOW": "blue", "INFO": "dim"}
        for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
            count = stats.get(severity, 0)
            table.add_row(f"[{colors[severity]}]{severity}[/{colors[severity]}]", str(count))
        table.add_row("[bold]TOTAL[/bold]", str(stats.get("TOTAL", 0)))

        console.print(table)
        console.print(
            f"Risk Score: [bold red]{report.risk_score}[/bold red] | "
            f"Duration: {report.metadata.duration_seconds:.0f}s | "
            f"Requests: {report.metadata.total_requests}"
        )


def _progress_context(description: str) -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn(f"[bold]{description}[/bold]"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )
