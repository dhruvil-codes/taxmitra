# Tax Mitra 🇮🇳

**Your tax notice, made understandable.**

Turn confusing Indian income-tax notices into clear explanations, personalized checklists, and response drafts — in your language.

---
<img width="1843" height="951" alt="image" src="https://github.com/user-attachments/assets/f5b6f8f5-3239-4f47-9c2d-1130eeecd6c3" />
---

## Live Demo

**[taxmitra-eight.vercel.app](https://taxmitra-eight.vercel.app/)**

---

## What It Does

Tax Mitra helps you understand income-tax notices and prepare responses.

- **Plain-language explanations** — Understand what your notice means
- **PDF extraction** — Upload a 142(1) scrutiny notice to extract requests
- **Bilingual** — English/Hindi support throughout
- **Guided questions** — Simple flow to determine your response path
- **Response draft** — Editable draft pre-filled based on your answers
- **Official handoff** — Direct link to e-Filing portal for submission

**AI EXPLAINS → RULES DECIDE → HUMANS APPROVE**

Tax Mitra never submits anything. You review, approve, and submit through the official portal.

---

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL=http://localhost:8000` in `frontend/.env`

---

## Architecture

**Frontend:** React + TypeScript + Vite (Vercel)
**Backend:** FastAPI + Python (Railway)
**Knowledge:** Authoritative Income Tax Department corpus

---

## User Flow

<!-- EXCALIDRAW DIAGRAM -->
[ Landing → Demo Citizen → Dashboard → Notice → Understand → Questions → Draft → Portal ]

---

## Tech Stack

| Frontend | Backend |
|----------|---------|
| React 18 | FastAPI |
| TypeScript | Python 3.11+ |
| Vite | Pydantic |
| React Router | OpenAI (optional) |
| Tailwind CSS | PyPDF |

---

## Supported Notices

- **Section 143(1)(a)** — Income mismatch notices
- **Section 142(1)** — Scrutiny notices (PDF upload)

Other notice types are not supported and will display a refusal screen.

---

## Testing

```bash
cd backend
pytest
```

67 tests covering API contracts, deadlines, classification, and extraction.

---

## Deployment

- **Frontend:** Vercel (`frontend/vercel.json`)
- **Backend:** Railway (`backend/Procfile`)
- **CORS:** Configured for localhost and production Vercel origin

---

## License

Provided as-is for educational purposes.

---

## Disclaimer

Tax Mitra is an independent prototype. All data is fictional. Not affiliated with the Income Tax Department. For complex situations, consult a qualified professional.
