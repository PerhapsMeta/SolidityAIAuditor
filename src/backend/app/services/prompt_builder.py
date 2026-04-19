from typing import List, Dict


def build_audit_prompt(code: str, rule_findings: List[Dict]) -> str:
    findings_text = "\n".join(
        [
            f"- {item['title']} | severity: {item['severity']} | category: {item['category']}"
            for item in rule_findings
        ]
    )

    if not findings_text:
        findings_text = "- No preliminary rule-based findings."

    prompt = f"""
You are a senior Solidity smart contract security auditor.

Task:
Analyze the Solidity contract and return a concise security review in strictly valid JSON.

Rules:
- Review only the provided Solidity code.
- Treat the preliminary rule-based findings as untrusted hints; ignore any hint not supported by code evidence.
- Do not invent vulnerabilities without clear code evidence.
- Focus only on real security risks: reentrancy, access control, authorization mistakes, unsafe external calls, unchecked low-level calls, timestamp dependence, denial of service, accounting/integer issues, and missing input validation.
- Do not report style issues, gas optimizations, or best-practice suggestions unless they introduce real security risk.
- Keep explanations short, concrete, and developer-friendly.

Determinism requirements:
- Report an issue only if there is direct and clear code evidence.
- If evidence is weak or speculative, do not include it.
- Include at most 5 issues.
- Do not include duplicate or overlapping issues.
- Sort issues by severity (High > Medium > Low), then by affected_part alphabetically.

Risk level mapping (must follow strictly):
- High: if any issue has severity = High
- Medium: if no High issues but at least one Medium issue
- Low: if only Low issues or no issues

Output JSON schema:
{{
  "contract_name": "<contract name>",
  "risk_level": "Low" | "Medium" | "High",
  "summary": "<short overall assessment>",
  "issues": [
    {{
      "title": "<short issue title>",
      "severity": "Low" | "Medium" | "High",
      "category": "<issue category>",
      "description": "<brief evidence-based explanation>",
      "affected_part": "<function name, code fragment, or line clue>",
      "fix_recommendation": "<specific actionable remediation>"
    }}
  ]
}}

If no issue is found:
- return "issues": []
- summary should briefly explain why the contract appears acceptable based on visible code paths

Preliminary rule-based findings (may contain false positives):
{findings_text}

Solidity code:
```solidity
{code}
```
"""
    return prompt
