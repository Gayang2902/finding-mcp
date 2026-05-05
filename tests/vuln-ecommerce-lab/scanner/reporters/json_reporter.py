"""
JSON reporter — exports VulnerabilityReport as structured JSON.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from scanner.models.vulnerability import VulnerabilityReport


class JSONReporter:
    """Exports scan results as pretty-printed JSON."""

    def generate(self, report: VulnerabilityReport, output_path: str) -> str:
        """
        Write JSON report to *output_path*.

        Returns the path written.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        data = report.model_dump(mode="json")
        # Add human-readable timestamp
        data["generated_at"] = datetime.utcnow().isoformat() + "Z"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        return output_path

    def generate_with_timestamp(self, report: VulnerabilityReport, output_dir: str) -> str:
        """Generate JSON with a timestamp-based filename."""
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"vuln_report_{ts}.json"
        return self.generate(report, os.path.join(output_dir, filename))
