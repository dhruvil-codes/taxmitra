# Tax Mitra V2 implementation plan

## Objective

Evolve the existing 143(1)(a)/142(1) prototype into a universal Income Tax
communication engine. Every PDF uses one ingestion and classification path;
workflow capability determines whether Tax Mitra guides, explains, partially
supports, or safely stops. Government submission remains outside the product.

## Audit findings

- `app/workflows/registry.py` has a useful extension point but only five
  definitions, a boolean support flag, and no canonical capability enum,
  evidence list, or classification evidence payload.
- `app/workflows/handlers.py` delegates only 143(1)(a) and 142(1); all other
  registered entries use a generic safe-stop handler.
- `app/ingestion/pipeline.py` already validates PDFs, preserves page order and
  provenance, combines native text with page-scoped OCR, and extracts multiple
  numbered requests. Section detection and request normalization need to cover
  the full taxonomy and low-confidence cases.
- The API already exposes generic catalog/classify/extract/workflow routes,
  while legacy `/api/workflow/*` and `/api/scrutiny/*` contracts must remain
  compatible.
- The frontend has a shared shell and workflow metadata types, but upload
  routing, unsupported copy, and `Scrutiny.tsx` still assume 142(1) in places.
- Knowledge and evidence layers exist and must distinguish official grounding,
  deterministic rules, and generated explanations. Current corpus coverage is
  strongest for 142(1), 143(1), and 139(9).

## Implementation sequence

1. Replace registry metadata with a canonical taxonomy and capability enum;
   expand section/terminology signals, expose confidence plus evidence, and
   route ambiguous/weak extraction/grounding to useful safe-stop contracts.
2. Define the universal workflow contract and handler factory while preserving
   legacy adapters. Add request normalization, request confirmation, minimum
   question planning, evidence mapping, review gates, and official handoff
   metadata as backend-owned decisions.
3. Implement P0 workflows: real 139(9) defective-return guidance and 143(1)
   general-intimation guidance. Keep 143(1)(a) and 142(1) behavior backward
   compatible; only generate responses from grounded facts and confirmed
   requests.
4. Add grounded partial/explanation-only workflows for 154/TDS mismatch and
   245, plus useful safe-stop handlers for reassessment, penalty, AO and other
   high-risk communications. Do not claim unsupported automation.
5. Make upload and notice journeys consume the universal contract, render
   dynamic requests/questions/evidence/safe-stop facts, and remove tax-specific
   routing logic from shared frontend navigation.
6. Harden OCR/section extraction for Hindi, bilingual, mixed, tables, long and
   noisy PDFs; verify Docker OCR when infrastructure allows.
7. Add/expand backend and frontend tests for taxonomy, confidence/evidence,
   routing capabilities, P0 handlers, provenance, question/evidence safety,
   approval gating, and regressions. Run lint/build/test/diff checks.
8. Update README and architecture documentation with accurate support levels,
   product claim, workflow registry, and remaining blockers.

## Acceptance checkpoints

- No workflow is marked `SUPPORTED` without domain rules, grounding,
  request handling, questions, evidence/action logic, safe-stop conditions,
  tests, and frontend integration.
- Every response/action path requires explicit human approval and ends in
  taxpayer-controlled official portal handoff.
- `Not sure` remains distinct from `No`; ambiguous or low-confidence cases do
  not receive an automated response.
- Existing 143(1)(a) and 142(1) routes and tests remain green.
