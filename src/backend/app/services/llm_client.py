import json
from typing import Any, Optional

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT


client = OpenAI(api_key=OPENAI_API_KEY, timeout=OPENAI_TIMEOUT) if OPENAI_API_KEY else None


AUDIT_SCHEMA = {
    "name": "solidity_audit_report",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "contract_name": {"type": "string"},
            "risk_level": {
                "type": "string",
                "enum": ["Low", "Medium", "High"]
            },
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "title": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["Low", "Medium", "High"]
                        },
                        "category": {"type": "string"},
                        "description": {"type": "string"},
                        "affected_part": {"type": "string"},
                        "fix_recommendation": {"type": "string"}
                    },
                    "required": [
                        "title",
                        "severity",
                        "category",
                        "description",
                        "affected_part",
                        "fix_recommendation"
                    ]
                }
            },
            "summary": {"type": "string"}
        },
        "required": [
            "contract_name",
            "risk_level",
            "issues",
            "summary"
        ]
    },
    "strict": True
}


def fallback_result(raw_text: str = "") -> dict:
    return {
        "contract_name": "Unknown",
        "risk_level": "Low",
        "issues": [],
        "summary": raw_text or "No valid model output was returned.",
        "meta": {
            "ai_enabled": bool(OPENAI_API_KEY),
            "ai_succeeded": False,
            "model": OPENAI_MODEL,
            "rule_findings_count": 0,
        },
    }


def _coerce_issue(issue: Any) -> Optional[dict]:
    if not isinstance(issue, dict):
        return None

    severity = str(issue.get("severity", "Low")).strip().title()
    if severity not in {"Low", "Medium", "High"}:
        severity = "Low"

    return {
        "title": str(issue.get("title", "")).strip() or "Unnamed issue",
        "severity": severity,
        "category": str(issue.get("category", "General")).strip() or "General",
        "description": str(issue.get("description", "")).strip() or "No description provided.",
        "affected_part": str(issue.get("affected_part", "Unknown")).strip() or "Unknown",
        "fix_recommendation": str(issue.get("fix_recommendation", "")).strip() or "Review the affected logic and apply appropriate safeguards.",
    }


def _derive_risk_level(issues: list[dict]) -> str:
    severities = {issue.get("severity", "Low") for issue in issues}

    if "High" in severities:
        return "High"
    if "Medium" in severities:
        return "Medium"
    return "Low"


def _normalize_result(payload: Any) -> dict:
    if not isinstance(payload, dict):
        return fallback_result("Model returned a non-object response.")

    raw_issues = payload.get("issues", [])
    issues = []
    if isinstance(raw_issues, list):
        for issue in raw_issues:
            normalized_issue = _coerce_issue(issue)
            if normalized_issue:
                issues.append(normalized_issue)

    risk_level = str(payload.get("risk_level", "")).strip().title()
    derived_risk_level = _derive_risk_level(issues)

    if risk_level not in {"Low", "Medium", "High"}:
        risk_level = derived_risk_level

    return {
        "contract_name": str(payload.get("contract_name", "Unknown")).strip() or "Unknown",
        "risk_level": risk_level,
        "issues": issues,
        "summary": str(payload.get("summary", "")).strip() or "Audit completed.",
        "meta": {
            "ai_enabled": bool(OPENAI_API_KEY),
            "ai_succeeded": True,
            "model": OPENAI_MODEL,
            "rule_findings_count": 0,
        },
    }


def call_llm(prompt: str) -> dict:
    if client is None:
        return fallback_result("Missing OPENAI_API_KEY in environment variables.")

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "You audit Solidity contracts and must return strictly valid JSON that matches the provided schema.",
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        }
                    ],
                },
            ],
            temperature=0,
            top_p=1,
            text={
                "format": {
                    "type": "json_schema",
                    "name": AUDIT_SCHEMA["name"],
                    "schema": AUDIT_SCHEMA["schema"],
                    "strict": AUDIT_SCHEMA["strict"],
                }
            }
        )

        raw_text = response.output_text.strip()
        return _normalize_result(json.loads(raw_text))

    except (json.JSONDecodeError, AttributeError) as exc:
        return fallback_result(f"Invalid model response: {exc}")
    except Exception as exc:
        return fallback_result(f"LLM request failed: {exc}")