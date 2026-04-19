import re
from typing import Dict, List


def _line_for(code: str, pattern: str) -> str:
    for line_number, line in enumerate(code.splitlines(), start=1):
        if pattern.lower() in line.lower():
            return f"line {line_number}: {line.strip()[:120]}"
    return pattern


def _finding(
    title: str,
    severity: str,
    category: str,
    description: str,
    affected_part: str,
    fix_recommendation: str,
) -> Dict:
    return {
        "title": title,
        "severity": severity,
        "category": category,
        "description": description,
        "affected_part": affected_part,
        "fix_recommendation": fix_recommendation,
    }


def run_rule_checks(code: str) -> List[Dict]:
    findings = []
    lowered = code.lower()

    if "delegatecall" in lowered:
        findings.append(
            _finding(
                "Use of delegatecall",
                "High",
                "Unsafe External Call",
                "delegatecall executes code in the caller's storage context and can lead to storage corruption or privilege escalation.",
                _line_for(code, "delegatecall"),
                "Avoid delegatecall unless it is required for a carefully reviewed proxy pattern.",
            )
        )

    if "tx.origin" in lowered:
        findings.append(
            _finding(
                "Use of tx.origin for authorization",
                "High",
                "Access Control",
                "tx.origin can be abused through phishing-style call chains and should not be used for authorization checks.",
                _line_for(code, "tx.origin"),
                "Use msg.sender and explicit role or ownership checks instead.",
            )
        )

    if re.search(r"\.call\s*\{?\s*value\s*:", code) or re.search(r"\.call\s*\(", code):
        findings.append(
            _finding(
                "Low-level call requires review",
                "Medium",
                "External Call",
                "Low-level calls bypass type checks and can introduce reentrancy or silent failure risks if not handled carefully.",
                _line_for(code, ".call"),
                "Check the returned success flag, update state before external calls, and consider ReentrancyGuard for value transfers.",
            )
        )

    if "selfdestruct" in lowered:
        findings.append(
            _finding(
                "Use of selfdestruct",
                "High",
                "Lifecycle",
                "selfdestruct can permanently remove contract code or force-send ether and is heavily restricted in modern EVM semantics.",
                _line_for(code, "selfdestruct"),
                "Avoid selfdestruct for normal control flow and replace it with an explicit pause or withdrawal mechanism.",
            )
        )

    if "block.timestamp" in lowered or re.search(r"\bnow\b", lowered):
        findings.append(
            _finding(
                "Timestamp-dependent logic",
                "Low",
                "Time Dependence",
                "Block timestamps can be influenced within a small range and should not drive high-value randomness or fragile authorization.",
                _line_for(code, "block.timestamp") if "block.timestamp" in lowered else _line_for(code, "now"),
                "Use timestamps only for coarse deadlines and avoid them for randomness or critical ordering decisions.",
            )
        )

    if "unchecked" in lowered:
        findings.append(
            _finding(
                "Unchecked arithmetic block",
                "Medium",
                "Arithmetic",
                "unchecked disables Solidity overflow and underflow checks inside the block.",
                _line_for(code, "unchecked"),
                "Keep unchecked blocks minimal and document the invariant that makes overflow or underflow impossible.",
            )
        )

    if "pragma solidity" in lowered and re.search(r"pragma\s+solidity\s+[\^~]?\s*0\.[0-7]\.", lowered):
        findings.append(
            _finding(
                "Old Solidity compiler version",
                "Medium",
                "Compiler",
                "The contract appears to target a pre-0.8 Solidity compiler, which lacks built-in arithmetic overflow checks.",
                _line_for(code, "pragma solidity"),
                "Upgrade to Solidity 0.8.x or add well-tested arithmetic safety libraries if an upgrade is not possible.",
            )
        )

    return findings
