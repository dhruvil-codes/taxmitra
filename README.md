# Tax Mitra 🇮🇳

**Your tax notice, made understandable.**

Tax Mitra is a guided digital experience that turns a confusing Indian income tax
notice into a simple explanation, a personalized document checklist, an editable
response draft, and a clear next official step — in the citizen's own language,
with every claim traceable to official sources.

> Notice → Understand → Answer → Prepare → Review → Act

**AI explains. Rules decide. Humans approve.**

---

## Status

Prototype scaffold for the **Build What Moves India** hackathon
(submission deadline: Aug 28, 2026, 8:00 PM IST).

## Repository structure

```
tax-mitra/
├── backend/                 # FastAPI service: rules engine, RAG knowledge base, AI layer
│   ├── app/
│   │   ├── routers/         # API endpoints (notices, workflow, AI)
│   │   ├── rules/           # Deterministic decision logic — pure Python, zero AI
│   │   ├── knowledge/       # Curated official-source corpus + retrieval
│   │   ├── ai/              # OpenAI provider, caching, pre-generated content
│   │   ├── data/            # Synthetic citizens and notices (fictional)
│   │   └── static_fallbacks/# Pre-generated, cited content served instantly
│   ├── scripts/             # build_kb.py, pregenerate.py
│   └── tests/               # pytest suite
├── frontend/                # React + TypeScript + Vite mobile-first UI
│   └── src/{pages,components,locales,lib}
└── README.md
```

## Disclaimer

Tax Mitra is an **independent prototype** created for a hackathon. All data shown
is **fictional and synthetic**. Tax Mitra is **not** an official Income Tax
Department service, is not affiliated with the Government of India, and never
submits anything on a citizen's behalf. The official e-Filing portal remains the
authoritative source and the only official submission channel.
