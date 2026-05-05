"""
LLM prompt templates for all scanner agents.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Base system prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert web application security analyst specializing in API security testing.
Your role is to analyze HTTP request/response pairs and identify authorization vulnerabilities.

Focus on:
- Insecure Direct Object References (IDOR)
- Parameter tampering and client-side trust issues
- Privilege escalation (horizontal and vertical)
- Missing function-level access control
- Business logic flaws

Be precise, evidence-based, and actionable. Avoid false positives.
When uncertain, say so explicitly and assign low confidence.

Always respond in the format requested (JSON when asked for JSON).
"""


# ---------------------------------------------------------------------------
# IDOR prompts
# ---------------------------------------------------------------------------

def analyze_idor_response(
    endpoint: str,
    method: str,
    user_a_response: Dict[str, Any],
    user_b_response: Dict[str, Any],
) -> str:
    return f"""Analyze these two HTTP responses for an IDOR vulnerability.

ENDPOINT: {method} {endpoint}

OWNER RESPONSE (User A accessing their own resource):
Status: {user_a_response.get('status')}
Body: {user_a_response.get('body')}

ATTACKER RESPONSE (User B accessing User A's resource with User A's resource ID):
Status: {user_b_response.get('status')}
Body: {user_b_response.get('body')}

Questions to answer:
1. Is this a confirmed IDOR? (User B should have received 403/404 but got 2xx)
2. What sensitive data is exposed?
3. What is the business impact?
4. How confident are you? (0.0-1.0)

Respond with JSON:
{{
  "is_idor": true/false,
  "confidence": 0.0-1.0,
  "sensitive_data_exposed": ["field1", "field2"],
  "impact": "description of business impact",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "explanation": "brief explanation"
}}"""


def assess_idor_impact(endpoint: str, leaked_data: List[str]) -> str:
    return f"""Assess the business impact of an IDOR vulnerability.

ENDPOINT: {endpoint}
LEAKED DATA FIELDS: {', '.join(leaked_data) if leaked_data else 'unknown'}

Consider: data sensitivity, regulatory requirements (PII, financial data), abuse potential.

Respond with JSON:
{{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "impact_description": "detailed impact",
  "affected_data_types": ["PII", "financial", etc.],
  "regulatory_concern": true/false,
  "exploit_difficulty": "trivial|low|medium|high"
}}"""


def generate_idor_remediation(endpoint: str, vuln_details: str) -> str:
    return f"""Generate remediation advice for an IDOR vulnerability.

ENDPOINT: {endpoint}
VULNERABILITY: {vuln_details}

Respond with JSON:
{{
  "primary_fix": "main remediation step",
  "implementation_steps": ["step1", "step2"],
  "code_pattern": "pseudocode or pattern to follow",
  "validation_method": "how to verify the fix"
}}"""


# ---------------------------------------------------------------------------
# Parameter tampering prompts
# ---------------------------------------------------------------------------

def analyze_parameter_trust(
    endpoint: str,
    method: str,
    request_body: Dict[str, Any],
    response: Dict[str, Any],
) -> str:
    return f"""Analyze this API request/response for parameter tampering vulnerabilities.

ENDPOINT: {method} {endpoint}
REQUEST BODY: {request_body}
RESPONSE: Status={response.get('status')} Body={response.get('body')}

Questions:
1. Does the server accept client-supplied values it should calculate server-side?
   (e.g. price, total, discount, role, status)
2. Are there any fields that a client should not be able to set?
3. Was the tampered value reflected in the response?

Respond with JSON:
{{
  "tampering_detected": true/false,
  "confidence": 0.0-1.0,
  "vulnerable_fields": ["fieldName"],
  "server_accepted_value": true/false,
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "explanation": "brief explanation"
}}"""


def identify_tamperable_params(endpoint: str, method: str, endpoint_schema: Dict) -> str:
    return f"""Identify parameters in this API endpoint that clients should NOT control.

ENDPOINT: {method} {endpoint}
SCHEMA: {endpoint_schema}

Look for: price, amount, total, discount, role, status, userId, createdAt, updatedAt.

Respond with JSON:
{{
  "suspicious_params": [
    {{"name": "paramName", "reason": "why it's suspicious", "test_value": "what to try"}}
  ]
}}"""


# ---------------------------------------------------------------------------
# Privilege escalation prompts
# ---------------------------------------------------------------------------

def analyze_access_control(
    endpoint: str,
    method: str,
    role_responses: Dict[str, Dict[str, Any]],
    expected_roles: List[str],
) -> str:
    responses_text = "\n".join(
        f"  {role}: HTTP {info.get('status')} — {str(info.get('body', ''))[:200]}"
        for role, info in role_responses.items()
    )
    return f"""Analyze access control for this endpoint.

ENDPOINT: {method} {endpoint}
EXPECTED ALLOWED ROLES: {', '.join(expected_roles) if expected_roles else 'all authenticated'}

ACTUAL RESPONSES BY ROLE:
{responses_text}

Determine:
1. Are any roles accessing this endpoint that shouldn't be?
2. Is this a privilege escalation vulnerability?
3. What is the severity?

Respond with JSON:
{{
  "privilege_escalation_detected": true/false,
  "confidence": 0.0-1.0,
  "bypassing_roles": ["role1"],
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "type": "horizontal|vertical|both",
  "explanation": "brief explanation"
}}"""


def assess_escalation_impact(endpoint: str, achieved_role: str, from_role: str) -> str:
    return f"""Assess the impact of a privilege escalation vulnerability.

ENDPOINT: {endpoint}
ATTACKER ROLE: {from_role}
ACHIEVED ACCESS LEVEL: {achieved_role}

Respond with JSON:
{{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "impact": "what an attacker can do",
  "attack_scenario": "realistic attack description",
  "data_at_risk": ["data type 1", "data type 2"]
}}"""


# ---------------------------------------------------------------------------
# Business logic prompts
# ---------------------------------------------------------------------------

def identify_business_rules(endpoint_description: str, api_schema: str) -> str:
    return f"""Identify business rules that should be enforced for this API endpoint.

ENDPOINT DESCRIPTION: {endpoint_description}
API SCHEMA: {api_schema}

List the business rules that MUST be enforced server-side.

Respond with JSON:
{{
  "business_rules": [
    {{
      "rule": "description of rule",
      "test_scenario": "how to test if this rule is enforced",
      "violating_input": "what input would violate this rule"
    }}
  ]
}}"""


def analyze_rule_violation(rule: str, test_result: Dict[str, Any]) -> str:
    return f"""Analyze whether a business rule was violated.

BUSINESS RULE: {rule}
TEST RESULT:
  Request: {test_result.get('request')}
  Response Status: {test_result.get('status')}
  Response Body: {str(test_result.get('body', ''))[:500]}

Was the business rule enforced? What is the impact if not?

Respond with JSON:
{{
  "rule_violated": true/false,
  "confidence": 0.0-1.0,
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "impact": "business impact description",
  "explanation": "technical explanation"
}}"""


def generate_attack_scenarios(endpoint_group: str, endpoints: List[str]) -> str:
    return f"""Generate creative attack scenarios for this group of API endpoints.

ENDPOINT GROUP: {endpoint_group}
ENDPOINTS: {chr(10).join(endpoints)}

Think like an attacker trying to abuse business logic.

Respond with JSON:
{{
  "attack_scenarios": [
    {{
      "name": "scenario name",
      "description": "what the attacker does",
      "endpoints_involved": ["endpoint1"],
      "expected_impact": "what the attacker gains",
      "steps": ["step1", "step2"]
    }}
  ]
}}"""


# ---------------------------------------------------------------------------
# Generic prompts
# ---------------------------------------------------------------------------

def classify_vulnerability(endpoint: str, method: str, evidence: str) -> str:
    return f"""Classify this potential security vulnerability.

ENDPOINT: {method} {endpoint}
EVIDENCE: {evidence}

Respond with JSON:
{{
  "vulnerability_type": "IDOR|PARAMETER_TAMPERING|PRIVILEGE_ESCALATION|MISSING_FUNCTION_ACCESS_CONTROL|BUSINESS_LOGIC_FLAW|NONE",
  "confidence": 0.0-1.0,
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "title": "concise vulnerability title",
  "explanation": "brief technical explanation"
}}"""


def assess_severity(vuln_type: str, endpoint: str, impact: str) -> str:
    return f"""Assess the CVSS-aligned severity for this vulnerability.

TYPE: {vuln_type}
ENDPOINT: {endpoint}
IMPACT: {impact}

Consider: data sensitivity, authentication required, user interaction, scope.

Respond with JSON:
{{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "cvss_score_estimate": 0.0-10.0,
  "rationale": "why this severity"
}}"""


def generate_reproduction_steps(vuln_details: Dict[str, Any]) -> str:
    return f"""Generate clear step-by-step reproduction steps for this vulnerability.

VULNERABILITY DETAILS:
{vuln_details}

Write steps that a developer or security engineer can follow to reproduce the issue.

Respond with JSON:
{{
  "reproduction_steps": [
    "Step 1: ...",
    "Step 2: ..."
  ],
  "prerequisites": ["prerequisite 1"],
  "curl_example": "curl command to reproduce"
}}"""


def analyze_response_for_sensitive_data(response_body: Any, context: str) -> str:
    return f"""Analyze this API response for sensitive data exposure.

CONTEXT: {context}
RESPONSE BODY: {str(response_body)[:1000]}

Identify any PII, financial data, credentials, or other sensitive information.

Respond with JSON:
{{
  "sensitive_data_found": true/false,
  "data_categories": ["PII", "financial", "credentials", "internal"],
  "specific_fields": ["fieldName1", "fieldName2"],
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "explanation": "what data is exposed and why it's sensitive"
}}"""
