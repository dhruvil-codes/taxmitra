# Tax Mitra (टैक्स मित्र) — V2

> **AI-Guided Income Tax Notice Defense & Response Engine**  
> *Selected for the Top 250 in **Build What Moves India** (Project #172)*

[![Tests](https://img.shields.io/badge/Backend%20Tests-236%20Passing-emerald)](https://github.com/dhruvil-codes/taxmitra)
[![Vitest](https://img.shields.io/badge/Frontend%20Tests-48%20Passing-blue)](https://github.com/dhruvil-codes/taxmitra)
[![Playwright](https://img.shields.io/badge/Playwright%20E2E-10%20Passing-success)](https://github.com/dhruvil-codes/taxmitra)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)
[![Bilingual](https://img.shields.io/badge/Language-English%20%7C%20%E0%A4%B9%E0%A4%BF%E0%A4%A8%E0%A5%8D%E0%A4%A6%E0%A5%80-orange)](https://github.com/dhruvil-codes/taxmitra)

---

## 📌 Live Deployments

- **Web Application**: [taxmitra.bydhruvil.in](https://taxmitra.bydhruvil.in) (or [tax-mitra.vercel.app](https://tax-mitra.vercel.app))
- **Backend API**: [web-production-cfee8.up.railway.app](https://web-production-cfee8.up.railway.app)
- **API Documentation**: [web-production-cfee8.up.railway.app/docs](https://web-production-cfee8.up.railway.app/docs)

---

## 🎯 The Problem

Every year, over **7 crore citizens** file Income Tax returns in India. But the real anxiety strikes months later when a taxpayer receives a multi-page legal notice from the Income Tax Department full of statutory jargon, strict response windows, and dense questionnaires.

- **High Friction**: Ordinary citizens cannot interpret complex sections like 142(1), 133(6), 143(1)(a), or 139(9).
- **Prohibitive Cost**: Chartered Accountants (CAs) typically charge ₹5,000 to ₹25,000 just to draft a single formal reply letter.
- **Risk of Inaction**: Ignoring or mishandling notices leads to ex-parte best judgment assessments, frozen bank accounts, and severe penalties.

**Tax Mitra** turns intimidating tax communications into an empowering, step-by-step guided journey—producing **authentic, CA-grade formal reply letters** ready for the official e-Filing portal.

---

## ⚡ The 4 Pillars of Tax Mitra

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  01. UNDERSTAND │ ───► │   02. ANSWER    │ ───► │   03. PREPARE   │ ───► │     04. ACT     │
│ Plain Language  │      │ 1:1 Requisition │      │ CA-Style Reply  │      │ Official Portal │
│ Breakdown & AY  │      │ Fact Ingestion  │      │ Draft & Annexes │      │ Step Guidance   │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
```

1. **Understand (समझें)**: Upload any notice PDF. Tax Mitra parses the text/OCR, identifies the DIN, Section, Assessment Year, and statutory deadline, and explains the notice in simple English or Hindi.
2. **Answer (उत्तर दें)**: Every departmental requisition is extracted 1:1. The citizen chooses their stance (*Provide / Partial / Explain*) and inputs real supporting facts (e.g., bank account numbers, ledger folios).
3. **Prepare (तैयार करें)**: Generates an authentic CA-style formal reply letter with official statutory letterhead, DIN, numbered arguments, dynamic Annexures, and multi-format downloads (PDF, TXT, MD).
4. **Act (कार्रवाई करें)**: Guides the citizen through the exact click-by-click path on the official Income Tax e-Filing portal (*Pending Actions → e-Proceedings*).

---

## 🚀 What's New in V2

### 1. The "Answer the Notice" Requisition Engine
In V1, questionnaires were broad and generic. V2 introduces **1:1 requisition extraction**:
- An Assessing Officer's notice under Section 142(1) or 133(6) is parsed into its individual legal demands (e.g., *Computation of Income, Balance Sheet, Cash Deposits, Bank Statements*).
- Each demand generates a dedicated questionnaire item with position choices and a free-text facts input.
- Answers are deterministically bound into the final legal response.

### 2. Authentic CA-Style Legal Letterhead
Instead of generic AI text summaries, Tax Mitra V2 structures an authentic legal submission letter matching real-world CA practice in India:
- **Statutory Address**: `To Assessment Unit / Verification Unit / Technical Unit / Review Unit / Income Tax Department`
- **Statutory Header**: Full `Ref:`, masked PAN, Assessment Year, and official notice `DIN`.
- **Numbered Submissions**: Citizen facts are embedded as formal numbered arguments.
- **Dynamic Annexures**: Every supporting document is tagged `(As per Annexure — N)` and compiled into a complete **List of Enclosures / Annexures**.
- **Multi-Format Export**: One-click download as **PDF**, **Plain Text (.txt)**, or **Markdown (.md)**, plus one-click clipboard copy.

### 3. Comprehensive Notice Universe & "Safe Stop" Guardrail
Coverage spans the primary direct tax notice categories:
- **Section 142(1)**: Scrutiny notice & multi-item questionnaire.
- **Section 133(6)**: Third-party information requisition summons.
- **Section 143(1)(a)**: Adjustment intimation for income/tax credit mismatches.
- **Section 139(9)**: Defective return intimation.
- **Section 245**: Outstanding tax demand & refund adjustment.
- **Section 154**: Rectification of mistake apparent from record.
- **🛡️ "Safe Stop" Guardrail**: If a high-risk or criminal notice arrives (such as Section 148 search & seizure or prosecution), Tax Mitra safely stops automation and advises the taxpayer to consult a certified advocate/CA.

### 4. Full Bilingual Support (English + हिन्दी)
- Universal toggle between **English** and **Devanagari Hindi** across all screens.
- Notice facts, questions, safety disclaimers, and portal instructions are fully localized with verified legal terms.

### 5. Strict Non-Agency Boundary
- **Zero Credential Ingestion**: Tax Mitra never asks for e-Filing passwords.
- **Zero Impersonation**: Tax Mitra never files on behalf of citizens. The user retains complete authority and submits directly on the official government portal.

---

## 🏗️ Architecture

```
tax-mitra/
├── backend/
│   ├── app/
│   │   ├── data/             # Synthetic demo notices (19 notices, 5 citizens)
│   │   ├── extraction/       # PDF parser & Tesseract OCR fallback
│   │   ├── knowledge/        # Versioned statutory rules & retrieval
│   │   ├── routers/          # FastAPI routers (workflows, notices, scrutiny)
│   │   ├── rules/            # Letter templates, response paths, notice types
│   │   └── workflows/        # Handlers, notice_requests, question models
│   └── tests/                # 236 passing pytest suites
├── frontend/
│   ├── src/
│   │   ├── components/       # Universal workflow & contract UI
│   │   ├── pages/            # Landing, Login, Dashboard, Notice, Journey
│   │   ├── i18n.tsx          # Bilingual English/Hindi dictionary
│   │   └── lib.ts            # Type contracts & API client
│   ├── tests/                # Playwright mobile & desktop E2E tests
│   └── playwright.config.ts  # Multi-device viewport matrix
```

---

## 🧪 Verification & Test Suite

Tax Mitra enforces automated end-to-end verification before every release:

- **Backend Pytest**: **236 passed, 0 failed** in `15.34s`
  ```bash
  cd backend && python -m pytest tests/ -q
  ```
- **Frontend Vitest**: **48 passed, 0 failed** in `15.49s`
  ```bash
  cd frontend && npm test
  ```
- **Playwright E2E**: **10 passed across all viewports** in `48.0s`
  ```bash
  cd frontend && npm run test:e2e
  ```
  - iPhone SE (`375x812`)
  - iPhone 12/13/14 (`390x844`)
  - iPhone Pro Max (`430x932`)
  - Standard Laptop (`1366x768`)
  - Full HD Desktop (`1920x1080`)

---

## 💻 Local Setup & Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or pnpm

### 1. Start the Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or: .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to experience Tax Mitra locally.

---

## 🏆 Hackathon Submission Details

- **Hackathon**: [Build What Moves India](https://buildwhatmovesindia.com/)
- **Theme**: Income Tax Department / Direct Taxes
- **Project Selection**: Top 250 Project **#172**
- **Author**: **Dhruvil Mistry** ([GitHub](https://github.com/dhruvil-codes))

---

*Disclaimer: Tax Mitra is an independent educational and civic technology prototype. It is not affiliated with the Income Tax Department or CBDT. It does not provide legal advice or execute submissions on behalf of taxpayers.*
