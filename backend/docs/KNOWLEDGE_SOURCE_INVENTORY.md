# Tax Mitra source-pack inventory

Audit of `TaxMitra_Knowledge.zip` (27 Aug 2026): 28 manifest records, 29
archive files, 6 PDFs, 20 Markdown files, 2 manifest files, 1 report, 1
README, and 1 SHA-256 list. The default runtime build ingests 10 local core
workflow documents into 116 chunks and retains the existing 15 demo chunks.

| Source ID | Authority/material | Status | Default |
|---|---|---|---|
| SEC-142 | CBDT Section 142 statutory capture | VERIFIED_OFFICIAL / CURRENT | Yes |
| SEC-143 | CBDT Section 143 statutory capture | VERIFIED_OFFICIAL / CURRENT | Yes |
| SEC-144 | CBDT Section 144 statutory capture | VERIFIED_OFFICIAL / CURRENT | Yes |
| SEC-144B | CBDT Section 144B statutory capture | VERIFIED_OFFICIAL / CURRENT | Yes |
| EP-MANUAL | Income Tax Department e-Proceedings manual | VERIFIED_OFFICIAL / CURRENT | Yes |
| EP-FAQ | Income Tax Department e-Proceedings FAQ | VERIFIED_OFFICIAL / CURRENT | Yes |
| AIS-FAQ | Income Tax Department AIS FAQ | VERIFIED_OFFICIAL / CURRENT | Yes |
| TRANSITION-FAQ | New Act transition FAQ | VERIFIED_OFFICIAL / CURRENT | Yes |
| NOTIFICATION-6-2021 | CBDT Faceless Assessment notification | VERIFIED_OFFICIAL / HISTORICAL | Yes, penalized |
| 1399-FAQ | Section 139(9) official FAQ | VERIFIED_OFFICIAL / CURRENT | Yes |

The V2 authoritative overlay reuses the same loader and retrieval path and
adds these directly verified portal records (each chunk carries publication,
update, AY/TY, Act-version, effective-period, workflow-context, status and
provenance metadata):

| Source ID | Authority/material | Status | Default |
|---|---|---|---|
| ITD-EPROCEEDINGS-2026 | Current e-Proceedings manual/response routes | VERIFIED_OFFICIAL / CURRENT | Yes |
| ITD-143-1-INTIMATION-2026 | Final 143(1) CPC intimation and rectification route | VERIFIED_OFFICIAL / CURRENT | Yes |
| ITD-RECTIFICATION-2026 | CPC rectification request types and boundaries | VERIFIED_OFFICIAL / CURRENT | Yes |
| ITD-EPROCEEDINGS-ACT2025-2026 | 1961/2025 Act transition FAQ | VERIFIED_OFFICIAL / CURRENT | Yes |
| ITD-TAX-CREDIT-MISMATCH-2026 | Tax Credit Mismatch and rectification manuals | VERIFIED_OFFICIAL / CURRENT | Yes |
| ITD-DEMAND-REFUND-2026 | Outstanding demand and refund reissue manuals | VERIFIED_OFFICIAL / CURRENT | Yes |
| ITD-REASSESSMENT-2026 | Reassessment transition FAQ | VERIFIED_OFFICIAL / CURRENT | Yes, explanation/safe-stop only |
| ITD-COMPLIANCE-AIS-2026 | AIS, e-Campaign, e-Verification and Compliance Portal | VERIFIED_OFFICIAL / CURRENT | Yes |
| ITD-PENALTY-PROCEEDINGS-2026 | e-Proceedings penalty boundary guidance | VERIFIED_OFFICIAL / CURRENT | Yes, safe-stop only |

The pack also contains current 2025 Act/2026 Rules/form material, Finance Act
and Finance Bill material, validation PDFs, taxpayer guidance, and lower-
priority FAQs. Run the ingestion script with `--all` only after reviewing those
materials for applicability. The manifest/report identifies the consolidated
1961 Act PDF and Rules 1962 candidate as `NEEDS_REVIEW`/unavailable, and the
Finance Bill as `UNKNOWN`; they are not silently used as current law.

The manifest JSON has shifted status/verification columns for four expanded
records. The ingestion script repairs only the known records using the pack
report's explicit status values and defaults unknown values to `NEEDS_REVIEW`.
No duplicates by title were found. A bill is never treated as enacted law, and
historical notifications are never preferred over current statutory material.
