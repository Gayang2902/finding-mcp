"""
Base class for all scanner analysis agents.
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from scanner.agents.llm_prompts import SYSTEM_PROMPT
from scanner.config.settings import Settings
from scanner.models.scan_context import ScanContext
from scanner.models.vulnerability import Evidence, Severity, Vulnerability, VulnerabilityType
from scanner.utils.http_client import AsyncHTTPClient
from scanner.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class BaseAnalysisAgent(ABC):
    """
    Abstract base for vulnerability analysis agents.

    Subclasses implement `analyze()` and use the helper methods provided here
    to create findings, call the LLM, and verify results.
    """

    name: str = "base"
    description: str = ""
    vuln_types: List[VulnerabilityType] = []

    def __init__(
        self,
        http_client: AsyncHTTPClient,
        llm_client: LLMClient,
        scan_context: ScanContext,
        settings: Settings,
    ) -> None:
        self._http = http_client
        self._llm = llm_client
        self._ctx = scan_context
        self._settings = settings
        self._findings: List[Vulnerability] = []
        self._logger = logging.getLogger(f"scanner.agents.{self.name}")

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def analyze(self) -> List[Vulnerability]:
        """Run analysis and return discovered vulnerabilities."""
        ...

    # ------------------------------------------------------------------
    # Vulnerability creation
    # ------------------------------------------------------------------

    def _create_vulnerability(
        self,
        vuln_type: VulnerabilityType,
        severity: Severity,
        title: str,
        endpoint: str,
        method: str,
        evidence: Evidence,
        description: str = "",
        reproduction_steps: Optional[List[str]] = None,
        impact: str = "",
        remediation: str = "",
        confidence: float = 0.7,
        cwe_id: Optional[str] = None,
    ) -> Vulnerability:
        """Factory method for creating Vulnerability objects with this agent's metadata."""
        return Vulnerability(
            id=str(uuid.uuid4()),
            type=vuln_type,
            severity=severity,
            title=title,
            description=description,
            endpoint=endpoint,
            method=method,
            evidence=evidence,
            reproduction_steps=reproduction_steps or [],
            impact=impact,
            remediation=remediation,
            confidence=confidence,
            discovered_at=datetime.utcnow(),
            agent_name=self.name,
            cwe_id=cwe_id,
        )

    def _build_evidence(
        self,
        method: str,
        url: str,
        response_status: int,
        response_body: Any = None,
        request_body: Any = None,
        request_headers: Optional[Dict[str, str]] = None,
        response_headers: Optional[Dict[str, str]] = None,
        expected_behavior: str = "",
        actual_behavior: str = "",
        comparison_url: Optional[str] = None,
        comparison_status: Optional[int] = None,
        comparison_body: Any = None,
    ) -> Evidence:
        return Evidence(
            request_method=method,
            request_url=url,
            request_headers=request_headers or {},
            request_body=request_body,
            response_status=response_status,
            response_headers=response_headers or {},
            response_body=response_body,
            expected_behavior=expected_behavior,
            actual_behavior=actual_behavior,
            comparison_request_url=comparison_url,
            comparison_response_status=comparison_status,
            comparison_response_body=comparison_body,
        )

    # ------------------------------------------------------------------
    # LLM helpers
    # ------------------------------------------------------------------

    async def _ask_llm_for_analysis(
        self,
        prompt: str,
        expect_json: bool = True,
    ) -> Dict[str, Any]:
        """
        Send *prompt* to the LLM and return parsed JSON result.
        Returns empty dict on failure or when LLM is disabled.
        """
        if not self._settings.enable_llm_analysis:
            return {}
        try:
            if expect_json:
                return await self._llm.analyze_json(prompt, system_prompt=SYSTEM_PROMPT)
            else:
                text = await self._llm.analyze(prompt, system_prompt=SYSTEM_PROMPT)
                return {"text": text}
        except Exception as exc:
            self._logger.warning("LLM analysis failed: %s", exc)
            return {}

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    async def _verify_finding(self, vuln: Vulnerability) -> bool:
        """
        Re-test the finding to reduce false positives.
        Returns True if the finding is confirmed on re-test.
        """
        if not self._settings.verify_findings:
            return True

        # Basic re-test: replay the original request and check status
        try:
            resp = await self._http.make_request(
                method=vuln.method,
                path=vuln.endpoint,
            )
            # If we expected a bypass and it still returns 2xx, confirmed
            if vuln.evidence.response_status in (200, 201) and resp.status_code in (200, 201):
                self._logger.debug("Finding verified: %s", vuln.title)
                return True
            # Status changed — may be transient or false positive
            self._logger.debug(
                "Finding status changed on re-test: %d → %d for %s",
                vuln.evidence.response_status, resp.status_code, vuln.title,
            )
            return False
        except Exception as exc:
            self._logger.debug("Verification request failed: %s", exc)
            return True  # network error — keep the finding

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def _log(self, message: str, *args: Any) -> None:
        self._logger.info(message, *args)

    def _log_finding(self, vuln: Vulnerability) -> None:
        self._logger.warning(
            "FINDING [%s] %s — %s %s (confidence=%.0f%%)",
            vuln.severity.value,
            vuln.title,
            vuln.method,
            vuln.endpoint,
            vuln.confidence * 100,
        )

    # ------------------------------------------------------------------
    # Context helpers
    # ------------------------------------------------------------------

    def _get_user(self, alias: str) -> Any:
        return self._ctx.authenticated_users.get(alias)

    def _get_customers(self) -> List[Any]:
        return self._ctx.customer_users

    def _get_ids(self, resource_type: str) -> List[Any]:
        return self._ctx.get_ids(resource_type)
