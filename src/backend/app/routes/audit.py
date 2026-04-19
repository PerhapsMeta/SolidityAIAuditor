from fastapi import APIRouter

from app.schemas import AuditRequest, AuditResponse
from app.services.analyzer import analyze_contract

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@router.post("/audit", response_model=AuditResponse)
def audit_contract(request: AuditRequest) -> AuditResponse:
    return analyze_contract(request.code)
