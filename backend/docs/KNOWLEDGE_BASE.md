# Tax Mitra authoritative knowledge base

The runtime corpus is `app/knowledge/corpus/`. Each Markdown chunk uses
frontmatter that preserves both the legacy citation fields and source-pack
provenance: `source_id`, `document_title`, `document_type`,
`official_organization`, `source_url`, `section`, `rule`, `form`,
`assessment_year`, `tax_year`, `effective_from`, `effective_to`, `status`,
and `verification_status`.

## Ingestion

The source pack is not copied into permanent application storage. To build the
core workflow corpus from a local unpacked pack:

```text
python scripts/ingest_source_pack.py C:\path\to\TaxMitra_Knowledge --output-dir app/knowledge/corpus
```

The default scope is the Section 142(1), assessment, e-Proceedings, AIS,
transition, and defective-notice material. Add `--all` only when the broader
pack is intentionally reviewed. The script emits a normalized manifest beside
the chunks and prints document/chunk counts.

Only `VERIFIED_OFFICIAL` material should be used for consequential guidance.
`NEEDS_REVIEW`, `UNKNOWN`, `SUPERSEDED`, and `HISTORICAL` metadata remain
visible to retrieval and are not silently promoted.

## Retrieval and legal versions

Lexical retrieval remains the offline/`DEMO_MODE` path. Exact section
references receive priority, followed by verified/current authority. Historical
or superseded material is penalized. A query must carry its assessment year or
tax year when the legal regime matters; the retriever must not combine the
Income-tax Act, 1961 with the Income-tax Act, 2025 without an applicability
decision. Embedding retrieval remains optional and uses the same enriched
chunks and confidence floor.

## Citations and refusal

`citations_for()` returns source URL, title, section, source ID, verification,
version fields, and a bounded excerpt. If the result is below the configured
confidence floor, callers must return a refusal or needs-review result. Source
material must support the claim; a request for a document is not by itself
proof that the document is a statutory requirement.

To add a source, add a manifest record, validate its official URL and effective
dates, record its SHA-256 and verification state, then rerun ingestion and the
retrieval regression tests. Do not ingest a bill, candidate consolidation, or
historical notification as current law without explicit applicability review.
