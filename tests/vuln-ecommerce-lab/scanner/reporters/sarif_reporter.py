"""
SARIF v2.1.0 reporter — for GitHub/GitLab security dashboard integration.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

from scanner.models.vulnerability import VulnerabilityReport, VulnerabilityType

# CWE mapping per vulnerability type
_CWE_MAP: Dict[str, str] = {
    VulnerabilityType.IDOR.value: "CWE-639",
    VulnerabilityType.PARAMETER_TAMPERING.value: "CWE-472",
    VulnerabilityType.PRIVILEGE_ESCALATION.value: "CWE-269",
    VulnerabilityType.MISSING_FUNCTION_ACCESS_CONTROL.value: "CWE-285",
    VulnerabilityType.BUSINESS_LOGIC_FLAW.value: "CWE-840",
}

# SARIF severity level mapping
_SEVERITY_MAP: Dict[str, str] = {
    "CRITICAL": "error",
    "HIGH": "error",
    "MEDIUM": "warning",
    "LOW": "note",
    "INFO": "none",
}

_SCANNER_VERSION = "1.0.0"
_SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"


class SARIFReporter:
    """Generates SARIF v2.1.0 format reports for CI/CD security dashboards."""

    def generate(self, report: VulnerabilityReport, output_path: str) -> str:
        """
        Write SARIF report to *output_path*.

        Returns the path written.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        sarif = self._build_sarif(report)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sarif, f, indent=2)

        return output_path

    def _build_sarif(self, report: VulnerabilityReport) -> Dict[str, Any]:
        rules = self._build_rules()
        results = [self._vuln_to_result(v) for v in report.vulnerabilities]

        return {
            "$schema": _SARIF_SCHEMA,
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "VulnScanner",
                            "version": _SCANNER_VERSION,
                            "informationUri": "https://github.com/example/vuln-scanner",
                            "rules": rules,
                        }
                    },
                    "results": results,
                    "properties": {
                        "targetUrl": report.metadata.target_url,
                        "scanStart": report.metadata.scan_start.isoformat(),
                        "llmModel": report.metadata.llm_model,
                        "totalRequests": report.metadata.total_requests,
                    },
                }
            ],
        }

    def _build_rules(self) -> List[Dict[str, Any]]:
        """Build SARIF rule definitions from vulnerability type registry."""
        rules = []
        type_meta = {
            VulnerabilityType.IDOR.value: {
                "name": "InsecureDirectObjectReference",
                "shortDescription": "Insecure Direct Object Reference (IDOR)",
                "fullDescription": "A resource can be accessed by any authenticated user, not just the owner.",
                "helpUri": "https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References",
            },
            VulnerabilityType.PARAMETER_TAMPERING.value: {
                "name": "ParameterTampering",
                "shortDescription": "Parameter Tampering",
                "fullDescription": "Server trusts client-supplied values that should be computed server-side.",
                "helpUri": "https://owasp.org/www-community/attacks/Web_Parameter_Tampering",
            },
            VulnerabilityType.PRIVILEGE_ESCALATION.value: {
                "name": "PrivilegeEscalation",
                "shortDescription": "Privilege Escalation",
                "fullDescription": "A user can access functionality or data reserved for higher-privileged roles.",
                "helpUri": "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
            },
            VulnerabilityType.MISSING_FUNCTION_ACCESS_CONTROL.value: {
                "name": "MissingFunctionLevelAccessControl",
                "shortDescription": "Missing Function-Level Access Control",
                "fullDescription": "An endpoint lacks proper authentication or authorization enforcement.",
                "helpUri": "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
            },
            VulnerabilityType.BUSINESS_LOGIC_FLAW.value: {
                "name": "BusinessLogicFlaw",
                "shortDescription": "Business Logic Flaw",
                "fullDescription": "A business rule is not enforced server-side, allowing abuse.",
                "helpUri": "https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/10-Business_Logic_Testing/",
            },
        }

        for vuln_type, meta in type_meta.items():
            cwe = _CWE_MAP.get(vuln_type, "")
            rules.append({
                "id": vuln_type,
                "name": meta["name"],
                "shortDescription": {"text": meta["shortDescription"]},
                "fullDescription": {"text": meta["fullDescription"]},
                "helpUri": meta["helpUri"],
                "properties": {
                    "tags": ["security", cwe],
                    "cwe": cwe,
                },
            })
        return rules

    def _vuln_to_result(self, vuln: Any) -> Dict[str, Any]:
        """Convert a Vulnerability to a SARIF result object."""
        level = _SEVERITY_MAP.get(vuln.severity.value, "warning")
        cwe = _CWE_MAP.get(vuln.type.value, "")

        message_text = vuln.description
        if vuln.reproduction_steps:
            message_text += "\n\nReproduction:\n" + "\n".join(vuln.reproduction_steps)

        return {
            "ruleId": vuln.type.value,
            "level": level,
            "message": {"text": message_text},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": vuln.evidence.request_url,
                            "uriBaseId": "%SRCROOT%",
                        }
                    },
                    "logicalLocations": [
                        {
                            "name": f"{vuln.method} {vuln.endpoint}",
                            "kind": "function",
                        }
                    ],
                }
            ],
            "properties": {
                "severity": vuln.severity.value,
                "confidence": vuln.confidence,
                "agentName": vuln.agent_name,
                "cwe": cwe,
                "impact": vuln.impact,
                "remediation": vuln.remediation,
                "discoveredAt": vuln.discovered_at.isoformat(),
            },
        }
