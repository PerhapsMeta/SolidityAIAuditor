# Solidity AI Auditor Backend

This directory contains the FastAPI backend for the Solidity AI Auditor project. The service accepts Solidity source code, performs lightweight rule-based checks, optionally calls the OpenAI API for structured analysis, merges both result sets, and returns a normalized audit report for the frontend.

## Overview

The backend is responsible for:

- validating incoming Solidity source code
- scanning for common high-signal security risks
- building a focused audit prompt for the LLM
- requesting schema-constrained JSON from OpenAI
- merging deterministic findings with AI findings
- returning consistent success and error payloads

## Project Structure

```text
backend/
├── app/
│   ├── main.py                 # FastAPI entrypoint, CORS, and exception handlers
│   ├── schemas.py              # Request and response models
│   ├── config.py               # Environment loading
│   ├── routes/
│   │   └── audit.py            # Health and audit routes
│   ├── services/
│   │   ├── analyzer.py         # Main audit orchestration
│   │   ├── prompt_builder.py   # Prompt construction
│   │   └── llm_client.py       # OpenAI integration and result normalization
│   └── utils/
│       └── rule_checks.py      # Rule-based Solidity checks
├── requirements.txt
└── README.md
```

## How the Backend Works

Each `POST /api/audit` request follows this flow:

1. The request body is validated in `app/schemas.py`.
2. `app/utils/rule_checks.py` scans the Solidity source for known risky patterns.
3. `app/services/prompt_builder.py` builds a Solidity-specific audit prompt.
4. `app/services/llm_client.py` calls OpenAI and requires output that matches a strict JSON schema.
5. `app/services/analyzer.py` merges AI findings with rule-based findings.
6. The backend returns a normalized response containing the contract name, risk level, issues, summary, and metadata.

## Requirements

- Python 3.10 or higher
- `pip`
- An OpenAI API key for AI-backed analysis

The backend still runs without an API key, but the AI step is skipped and only rule-based findings are returned.

## Installation

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

Create `backend/.env` or a repository-level `.env` file with:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4
OPENAI_TIMEOUT=45
```

Notes:

- `OPENAI_API_KEY` enables the OpenAI audit step
- `OPENAI_MODEL` defaults to `gpt-5.4`
- `OPENAI_TIMEOUT` defaults to `45` seconds
- the backend loads both the repository root `.env` and `backend/.env`

## Run the Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Default local URL:

```text
http://127.0.0.1:8000
```

## API Endpoints

### `GET /`

Basic backend health check.

Response:

```json
{
  "message": "Backend is running"
}
```

### `GET /api/health`

API health check.

Response:

```json
{
  "status": "ok"
}
```

### `POST /api/audit`

Analyzes Solidity source code and returns a structured audit report.

Request body:

```json
{
  "code": "pragma solidity ^0.8.20; contract Example { function ping() external pure returns (uint256) { return 1; } }"
}
```

## Request Validation

The `code` field:

- is required
- must be a string
- must not be empty after trimming whitespace
- must be no longer than `200000` characters
- must include a valid Solidity pragma such as `pragma solidity ^0.8.20;`

Validation lives in `app/schemas.py`. Validation and runtime errors are wrapped into structured error payloads in `app/main.py`.

## Success Response Format

Example response:

```json
{
  "contract_name": "Example",
  "risk_level": "Low",
  "issues": [],
  "summary": "No obvious issues were found by the rule-based or AI checks.",
  "meta": {
    "ai_enabled": false,
    "ai_succeeded": false,
    "model": "gpt-5.4",
    "rule_findings_count": 0
  }
}
```

Field descriptions:

- `contract_name`: detected contract, interface, or library name
- `risk_level`: overall risk level, one of `Low`, `Medium`, or `High`
- `issues`: list of findings
- `summary`: audit summary
- `meta.ai_enabled`: whether `OPENAI_API_KEY` is configured
- `meta.ai_succeeded`: whether the OpenAI request completed successfully
- `meta.model`: configured model name
- `meta.rule_findings_count`: number of rule-based findings merged into the final result

Each issue uses this structure:

```json
{
  "title": "Use of delegatecall",
  "severity": "High",
  "category": "Unsafe External Call",
  "description": "delegatecall executes code in the caller's storage context and can lead to storage corruption or privilege escalation.",
  "affected_part": "line 1: ...",
  "fix_recommendation": "Avoid delegatecall unless it is required for a carefully reviewed proxy pattern."
}
```

## Error Response Format

The backend wraps validation errors, HTTP errors, and unexpected server failures into a consistent JSON shape.

Validation error example:

```json
{
  "error": {
    "type": "validation_error",
    "code": "invalid_audit_request",
    "message": "Request validation failed.",
    "details": [
      {
        "field": "body -> code",
        "code": "invalid_solidity_source",
        "message": "Input must include a Solidity pragma with a version, such as 'pragma solidity ^0.8.20;'."
      }
    ]
  }
}
```

Business error codes currently used:

- `invalid_audit_request`
- `missing_contract_code`
- `empty_contract_code`
- `contract_code_too_long`
- `invalid_contract_code_type`
- `invalid_solidity_source`
- `invalid_request_field`
- `request_failed`
- `internal_server_error`

## Rule-Based Checks

The current rule engine in `app/utils/rule_checks.py` detects:

- `delegatecall`
- `tx.origin`
- low-level `.call`
- `selfdestruct`
- `block.timestamp` or `now`
- `unchecked` arithmetic blocks
- Solidity compiler versions below `0.8.x`

These checks are intentionally lightweight and are meant to catch obvious high-signal issues early.

## OpenAI Integration

The AI audit layer is implemented in `app/services/llm_client.py`.

Behavior:

- the OpenAI step only runs when `OPENAI_API_KEY` is configured
- the backend uses `client.responses.create(...)`
- the model output must match a strict JSON schema
- malformed model output is normalized or replaced with a fallback result
- API failures do not crash the backend; the service still returns a usable audit response

## Merge and Risk Logic

The final report is assembled in `app/services/analyzer.py`.

Important behavior:

- if the model returns an unknown contract name, the backend extracts one from source code using regex
- AI findings and rule-based findings are merged using `title + affected_part` as the deduplication key
- overall risk becomes `High` if any issue is high severity
- overall risk becomes `Medium` if there are no high issues but at least one medium issue
- otherwise overall risk is `Low`
- the summary includes counts of high, medium, and low findings when issues exist

## Example cURL Commands

Health checks:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/api/health
```

Audit request:

```bash
curl -X POST http://127.0.0.1:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"code":"pragma solidity ^0.8.20; contract A { function p(address a) external { a.delegatecall(\"\"); } }"}'
```

Possible response:

```json
{
  "contract_name": "A",
  "risk_level": "High",
  "issues": [
    {
      "title": "Use of delegatecall",
      "severity": "High",
      "category": "Unsafe External Call",
      "description": "delegatecall executes code in the caller's storage context and can lead to storage corruption or privilege escalation.",
      "affected_part": "line 1: pragma solidity ^0.8.20; contract A { function p(address a) external { a.delegatecall(\"\"); } }",
      "fix_recommendation": "Avoid delegatecall unless it is required for a carefully reviewed proxy pattern."
    }
  ],
  "summary": "Detected 1 potential issue(s): 1 high, 0 medium, 0 low. Missing OPENAI_API_KEY in environment variables.",
  "meta": {
    "ai_enabled": false,
    "ai_succeeded": false,
    "model": "gpt-5.4",
    "rule_findings_count": 1
  }
}
```

## Dependencies

Core dependencies from `requirements.txt` include:

- `fastapi`
- `uvicorn`
- `pydantic`
- `python-dotenv`
- `openai`

## Interactive API Docs

FastAPI exposes interactive docs while the backend is running:

```text
http://127.0.0.1:8000/docs
```

## Current Limitations

- single-file Solidity input only
- no multi-file import resolution
- no compilation, bytecode analysis, or symbolic execution
- no database or background job system
- lightweight checks only, so this should not be treated as a substitute for a professional audit

## Possible Future Improvements

- project-level multi-file analysis
- deeper AST-based Solidity checks
- stored audit history and report comparison
- async job processing for longer scans
- richer vulnerability categories and confidence scoring
