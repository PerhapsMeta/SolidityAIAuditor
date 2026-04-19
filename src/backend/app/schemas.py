import re
from typing import List, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError


Severity = Literal["Low", "Medium", "High"]
RiskLevel = Literal["Low", "Medium", "High"]


class AuditRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=200_000)

    @field_validator("code")
    @classmethod
    def code_must_look_like_solidity(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise PydanticCustomError(
                "empty_contract_code",
                "Solidity code cannot be empty.",
            )
        if not re.search(r"\bpragma\s+solidity\s+[^;]+;", stripped, re.IGNORECASE):
            raise PydanticCustomError(
                "invalid_solidity_source",
                "Input must include a Solidity pragma with a version, such as 'pragma solidity ^0.8.20;'.",
            )
        return stripped


class IssueItem(BaseModel):
    title: str
    severity: Severity
    category: str
    description: str
    affected_part: str
    fix_recommendation: str


class AuditMeta(BaseModel):
    ai_enabled: bool
    ai_succeeded: bool
    model: str
    rule_findings_count: int = Field(..., ge=0)


class AuditResponse(BaseModel):
    contract_name: str
    risk_level: RiskLevel
    issues: List[IssueItem]
    summary: str
    meta: AuditMeta
