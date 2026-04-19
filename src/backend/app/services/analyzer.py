import re

from app.config import OPENAI_MODEL, OPENAI_API_KEY
from app.utils.rule_checks import run_rule_checks
from app.services.prompt_builder import build_audit_prompt
from app.services.llm_client import call_llm


def _contract_name(code: str) -> str:
    match = re.search(r"\b(?:contract|interface|library)\s+([A-Za-z_][A-Za-z0-9_]*)", code)
    return match.group(1) if match else "Unknown"


def _risk_level(issues: list[dict]) -> str:
    severities = {issue.get("severity") for issue in issues}
    if "High" in severities:
        return "High"
    if "Medium" in severities:
        return "Medium"
    return "Low"


def _summary(issues: list[dict], ai_summary: str) -> str:
    if issues:
        high_count = sum(1 for issue in issues if issue.get("severity") == "High")
        medium_count = sum(1 for issue in issues if issue.get("severity") == "Medium")
        low_count = sum(1 for issue in issues if issue.get("severity") == "Low")
        return (
            f"Detected {len(issues)} potential issue(s): "
            f"{high_count} high, {medium_count} medium, {low_count} low. "
            f"{ai_summary.strip()}"
        ).strip()

    return ai_summary.strip() or "No obvious issues were found by the rule-based or AI checks."


def _merge_findings(ai_issues: list[dict], rule_findings: list[dict]) -> list[dict]:
    merged = list(ai_issues or [])
    seen = {
        (
            issue.get("title", "").lower(),
            issue.get("affected_part", "").lower(),
        )
        for issue in merged
    }

    for finding in rule_findings:
        key = (
            finding.get("title", "").lower(),
            finding.get("affected_part", "").lower(),
        )
        if key not in seen:
            merged.append(finding)
            seen.add(key)

    return merged


def analyze_contract(code: str) -> dict:
    rule_findings = run_rule_checks(code)
    prompt = build_audit_prompt(code, rule_findings)
    result = call_llm(prompt)

    result.setdefault(
        "meta",
        {
            "ai_enabled": bool(OPENAI_API_KEY),
            "ai_succeeded": False,
            "model": OPENAI_MODEL,
            "rule_findings_count": 0,
        },
    )

    if not result.get("contract_name") or result.get("contract_name") == "Unknown":
        result["contract_name"] = _contract_name(code)
    result["issues"] = _merge_findings(result.get("issues", []), rule_findings)
    result["meta"]["rule_findings_count"] = len(rule_findings)

    if result["issues"]:
        result["risk_level"] = _risk_level(result["issues"])
    else:
        result["risk_level"] = "Low"

    result["summary"] = _summary(result["issues"], result.get("summary", ""))
    return result
