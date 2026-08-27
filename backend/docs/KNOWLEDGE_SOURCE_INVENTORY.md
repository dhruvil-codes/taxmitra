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
