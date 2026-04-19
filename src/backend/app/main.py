from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes.audit import router as audit_router

app = FastAPI(title="Solidity AI Auditor Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router, prefix="/api")


def _validation_business_code(error: dict) -> str:
    error_type = error.get("type", "")
    location = error.get("loc", ())
    field = location[-1] if location else None

    if error_type == "missing" and field == "code":
        return "missing_contract_code"
    if error_type == "string_too_long" and field == "code":
        return "contract_code_too_long"
    if error_type == "string_type" and field == "code":
        return "invalid_contract_code_type"
    if error_type == "empty_contract_code":
        return "empty_contract_code"
    if error_type == "invalid_solidity_source":
        return "invalid_solidity_source"
    return "invalid_request_field"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    for error in exc.errors():
        location = " -> ".join(str(part) for part in error.get("loc", []))
        business_code = _validation_business_code(error)
        details.append(
            {
                "field": location,
                "code": business_code,
                "message": error.get("msg", "Invalid request."),
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "code": "invalid_audit_request",
                "message": "Request validation failed.",
                "details": details,
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "code": "request_failed",
                "message": detail,
                "details": [],
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "server_error",
                "code": "internal_server_error",
                "message": "Unexpected server error.",
                "details": [],
            }
        },
    )


@app.get("/")
def root():
    return {"message": "Backend is running"}
