# Solidity AI Auditor

AI-assisted Solidity smart contract auditing with a lightweight web UI and a FastAPI analysis backend.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Conflux](https://img.shields.io/badge/built%20for-Conflux%20Hackathon-blue)](https://confluxnetwork.org)
[![Hackathon](https://img.shields.io/badge/Global%20Hackfest%202026-prototype-green)](https://github.com/conflux-fans/global-hackfest-2026)

## Overview

Solidity AI Auditor is a web-based vulnerability detector for reviewing Solidity smart contracts. Users upload a `.sol` file in the frontend, and the backend combines deterministic rule-based checks with an OpenAI structured-output audit pass to generate a concise security report.

The project is designed as a practical prototype: fast to run locally, easy to demo, and focused on high-signal findings such as `delegatecall`, `tx.origin`, unsafe low-level calls, timestamp dependence, unchecked arithmetic, and outdated Solidity compiler targets.

## 🏆 Hackathon Information

- **Event**: Global Hackfest 2026
- **Focus Area**: Open Innovation
- **Team**: SafeByte
- **Submission Date**: 19/4/2026

## 👥 Team

| Name | Role | GitHub | Discord |
|------|------|--------|---------|
| L.yu | Product / Frontend | L19711221-debug | TBD |
| Lynn | Backend / AI | PerhapsMeta | TBD |

## 🚀 Problem Statement

**What problem does your project solve?**

Smart contract security reviews are expensive, slow, and often inaccessible to solo builders, hackathon teams, and early-stage protocol developers. Many teams ship experimental Solidity code without any structured security pass, which increases the risk of avoidable issues reaching testnet or production.

This problem matters because even small authorization mistakes or unsafe external calls can lead to severe financial loss. Developers need a fast first-pass review tool that can flag obvious risks before a manual audit.

Current limitations in existing solutions include:

- manual audits are accurate but costly and time-consuming
- generic LLM prompts can hallucinate issues or return inconsistent output
- static analysis tools can be hard to use for beginners and may overwhelm users with low-signal warnings

Blockchain development benefits from a tool that blends deterministic checks with AI reasoning, returning a structured report that is easier to interpret and act on during rapid iteration.

## 💡 Solution

**How does your project address the problem?**

Solidity AI Auditor provides a two-layer audit flow:

- a rule-based scanner first identifies common high-signal patterns
- an OpenAI-powered audit prompt then reviews the same Solidity source and returns strictly structured JSON
- the backend merges both outputs into a single report with contract name, risk level, issue list, summary, and metadata

This approach improves consistency over prompt-only auditing while remaining lightweight enough for demos, hackathon workflows, and early development use.

Benefits for users include:

- fast local contract review without a heavy toolchain
- structured issue output suitable for UI rendering and future automation
- graceful fallback when no API key is configured
- cleaner error handling for invalid or non-Solidity input

## Go-to-Market Plan (required)

- **Target users**: hackathon teams, indie smart contract developers, student builders, and early-stage Web3 product teams
- **Why they would use it**: it offers a quick security sanity check before code review, testnet deployment, or submission demos
- **Distribution path**: demo-driven adoption in hackathons, developer communities, Solidity learning groups, and open-source showcases
- **Key metrics**: number of analyzed contracts, repeat usage per project, issue detection rate, and API-backed audit completion rate
- **Ecosystem fit**: the product can serve as a developer onboarding tool for builders exploring Conflux-compatible contract development workflows

## ⚡ Conflux Integration

**How does your project leverage Conflux features?**

The current repository is an auditing prototype and does not yet include direct on-chain Conflux integration. It is positioned as a developer tool that can later support Conflux deployment and ecosystem-specific validation workflows.

- [ ] **Core Space** - Not integrated in the current prototype
- [ ] **eSpace** - Not integrated in the current prototype
- [ ] **Cross-Space Bridge** - Not integrated in the current prototype
- [ ] **Gas Sponsorship** - Not integrated in the current prototype
- [ ] **Built-in Contracts** - Not integrated in the current prototype
- [ ] **Tree-Graph Consensus** - Not directly used in the current prototype

### Partner Integrations

- [ ] **Privy** - Not integrated
- [ ] **Pyth Network** - Not integrated
- [ ] **LayerZero** - Not integrated
- [ ] **Other** - OpenAI API for structured security analysis

## ✨ Features

### Core Features

- **Solidity file upload and preview** - Load `.sol` files into a browser-based review interface with synced line numbers
- **Rule-based vulnerability checks** - Detect common risky patterns such as `delegatecall`, `tx.origin`, `.call`, `selfdestruct`, `unchecked`, and old compiler versions
- **AI-generated audit report** - Produce structured findings with severity, category, description, affected code clue, and remediation guidance

### Advanced Features

- **Strict JSON output contract** - The backend requests schema-constrained model responses for predictable parsing
- **Merged analysis pipeline** - Rule findings are merged with AI findings to reduce missed obvious issues
- **Robust validation and error UX** - Both frontend and backend reject invalid or non-Solidity input with actionable error messages

### Future Features (Roadmap)

- **Multi-file contract support** - Analyze imports and project-level contract sets instead of single-file input
- **Conflux-aware deployment checks** - Add network presets, deployment validation, and chain-specific recommendations
- **Persistent audit history** - Store previous reports for comparison and team review

## 🛠️ Technology Stack

### Frontend

- **Framework**: Vanilla HTML, CSS, and JavaScript
- **Styling**: Custom CSS with a terminal-inspired dark UI
- **State Management**: In-browser DOM state
- **Web3 Integration**: None in the current prototype

### Backend

- **Runtime**: Python 3
- **Framework**: FastAPI
- **Validation**: Pydantic
- **APIs**: REST

### AI Layer

- **Provider**: OpenAI API
- **Model**: Configurable with `OPENAI_MODEL`, defaulting to `gpt-5.4`
- **Output Format**: JSON schema constrained response

### Infrastructure

- **Frontend Serving**: Any static file server
- **Backend Serving**: Uvicorn
- **Configuration**: `.env` via `python-dotenv`

## 🏗️ Architecture

```text
┌────────────────────┐      ┌──────────────────────────┐      ┌─────────────────────┐
│   Frontend UI      │      │    FastAPI Backend       │      │     OpenAI API      │
│  (HTML/CSS/JS)     │ ───► │ /api/audit               │ ───► │ Structured JSON     │
│ Upload + Preview   │      │ Rule checks + prompting  │      │ security analysis   │
└────────────────────┘      └──────────────────────────┘      └─────────────────────┘
                                      │
                                      ▼
                           ┌──────────────────────────┐
                           │ Deterministic rule checks│
                           │ delegatecall / tx.origin │
                           │ .call / unchecked / etc. │
                           └──────────────────────────┘
```

**High-level architecture description:**

The frontend lets users upload a Solidity file, preview the code, and trigger analysis. The backend validates the request, performs lightweight rule-based checks, builds a Solidity-specific audit prompt, and optionally calls the OpenAI API for structured findings. The backend then merges the results and returns a normalized audit response for display.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.10 or higher
- **pip**
- **Git**
- **OpenAI API key** for AI-backed analysis, optional for rule-based fallback mode

### Development Tools (Optional)

- **virtualenv** or **venv** for Python environment isolation
- **http-server** or **python -m http.server** for serving the frontend locally

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/SolidityAIAuditor.git
cd SolidityAIAuditor
```

### 2. Install Backend Dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

### 3. Environment Configuration

Create `backend/.env` or a repository-level `.env`:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.4
OPENAI_TIMEOUT=45
```

Notes:

- if `OPENAI_API_KEY` is empty, the backend still works in rule-based fallback mode
- the backend loads both repository root `.env` and `backend/.env`

### 4. Start the Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

The backend will run at `http://127.0.0.1:8000`.

### 5. Start the Frontend

Serve the `frontend/` directory with any static server. For example:

```bash
cd frontend
python3 -m http.server 8080
```

Then open `http://127.0.0.1:8080`.

## 🧪 Testing

### Run Manual Checks

There is no automated test suite in the current repository yet. Recommended manual verification:

```bash
# Backend health check
curl http://127.0.0.1:8000/

# API health check
curl http://127.0.0.1:8000/api/health

# Example audit request
curl -X POST http://127.0.0.1:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"code":"pragma solidity ^0.8.20; contract A { function p(address a) external { a.delegatecall(\"\"); } }"}'
```

### Current Validation Coverage

The backend and frontend currently validate:

- missing contract source
- empty input
- oversized input
- invalid Solidity source without `pragma solidity`
- obvious non-Solidity input such as HTML, JavaScript, Python, JSON, or C/C++

## 📱 Usage

### Getting Started

1. Start the backend server.
2. Serve the frontend and open it in the browser.
3. Upload a `.sol` contract file.
4. Click **Analyze contract**.
5. Review the generated risk summary, severity counts, and vulnerability list.

### API Usage

`POST /api/audit`

Request body:

```json
{
  "code": "pragma solidity ^0.8.20; contract Example { function ping() external pure returns (uint256) { return 1; } }"
}
```

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

### Interactive Docs

FastAPI auto-generated documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## 📂 Project Structure

```text
.
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/
│   │   └── utils/
│   ├── requirements.txt
│   └── README.md
├── README.md
└── README1.md
```

## ⚠️ Limitations

- current analysis is single-file only
- no symbolic execution or compiler-driven AST analysis is included
- no persistence, authentication, or collaboration workflow is implemented
- rule-based checks are intentionally lightweight and should not replace a professional audit

## 📌 Status

This repository is a functional prototype suitable for local demos and hackathon iteration. It is best positioned as an AI-assisted first-pass auditor, not a replacement for full manual security review.
