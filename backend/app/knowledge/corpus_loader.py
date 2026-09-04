"""Corpus loader: parses markdown chunks with simple frontmatter.

Frontmatter keys include source_id, document_title, document_type,
official_organization, source_url, section, page_location, excerpt, summary,
applicability, effective_period, rule, form, assessment_year, tax_year,
effective_from, effective_to, verified_date, status, verification_status, and tags.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

_TEXT_KEYS = {"section", "title", "source_name", "official_url", "accessed_date", "verification", "source_id", "document_title", "document_type", "official_organization", "source_url", "page_location", "excerpt", "summary", "applicability", "effective_period", "rule", "form", "assessment_year", "tax_year", "effective_from", "effective_to", "verified_date", "status", "verification_status"}


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    section: str = ""
    title: str = ""
    source_name: str = ""
    official_url: str = ""
    accessed_date: str = ""
    verification: str = "pending"
    tags: tuple[str, ...] = field(default_factory=tuple)
    source_id: str = ""
    document_title: str = ""
    document_type: str = ""
    official_organization: str = ""
    source_url: str = ""
    page_location: str = ""
    excerpt: str = ""
    summary: str = ""
    applicability: str = ""
    effective_period: str = ""
    verified_date: str = ""
    rule: str = ""
    form: str = ""
    assessment_year: str = ""
    tax_year: str = ""
    effective_from: str = ""
    effective_to: str = ""
    status: str = "CURRENT"
    verification_status: str = "NEEDS_REVIEW"


def _parse_frontmatter_line(line: str) -> tuple[str, str] | None:
    if ":" not in line:
        return None
    key, _, value = line.partition(":")
    return key.strip(), value.strip().strip('"')


def parse_chunk(raw: str) -> Chunk:
    lines = raw.strip().splitlines()
    meta: dict[str, str] = {}
    tags: tuple[str, ...] = ()
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), -1)
        if end > 0:
            for line in lines[1:end]:
                parsed = _parse_frontmatter_line(line)
                if not parsed:
                    continue
                key, value = parsed
                if key == "tags":
                    tags = tuple(t.strip() for t in value.split(",") if t.strip())
                elif key == "id":
                    meta["id"] = value
                elif key in _TEXT_KEYS:
                    meta[key] = value
            body = "\n".join(lines[end + 1 :]).strip()
        else:
            body = raw.strip()
    else:
        body = raw.strip()
    return Chunk(
        id=meta.get("id", ""),
        text=body,
        section=meta.get("section", ""),
        title=meta.get("title", ""),
        source_name=meta.get("source_name", ""),
        official_url=meta.get("official_url", ""),
        accessed_date=meta.get("accessed_date", ""),
        verification=meta.get("verification", "pending"),
        tags=tags,
        source_id=meta.get("source_id", meta.get("id", "")),
        document_title=meta.get("document_title", meta.get("title", "")),
        document_type=meta.get("document_type", ""),
        official_organization=meta.get("official_organization", ""),
        source_url=meta.get("source_url", meta.get("official_url", "")),
        rule=meta.get("rule", ""), form=meta.get("form", ""),
        assessment_year=meta.get("assessment_year", ""), tax_year=meta.get("tax_year", ""),
        effective_from=meta.get("effective_from", ""), effective_to=meta.get("effective_to", ""),
        status=meta.get("status", "CURRENT"),
        verification_status={"verified": "VERIFIED_OFFICIAL", "VERIFIED_OFFICIAL": "VERIFIED_OFFICIAL", "pending": "PENDING_VERIFICATION", "not_applicable": "NOT_APPLICABLE", "unknown": "UNKNOWN"}.get(meta.get("verification_status", meta.get("verification", "unknown")), "UNKNOWN"),
        page_location=meta.get("page_location", ""), excerpt=meta.get("excerpt", ""),
        summary=meta.get("summary", ""), applicability=meta.get("applicability", ""),
        effective_period=meta.get("effective_period", "") or " to ".join(filter(None, (meta.get("effective_from", ""), meta.get("effective_to", "")))),
        verified_date=meta.get("verified_date", ""),
    )


@lru_cache(maxsize=1)
def load_corpus(corpus_dir: str) -> tuple[Chunk, ...]:
    chunks: list[Chunk] = []
    for name in sorted(os.listdir(corpus_dir)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(corpus_dir, name), encoding="utf-8") as fh:
            chunk = parse_chunk(fh.read())
        if chunk.id and chunk.text:
            chunks.append(chunk)
    return tuple(chunks)


@lru_cache(maxsize=1)
def corpus_index(corpus_dir: str) -> dict[str, Chunk]:
    return {c.id: c for c in load_corpus(corpus_dir)}


def citations_for(chunk_ids: tuple[str, ...], corpus_dir: str) -> list[dict]:
    """Resolve citation ids into provenance records for the Source Panel."""
    index = corpus_index(corpus_dir)
    out = []
    for cid in chunk_ids:
        chunk = index.get(cid)
        if chunk is None:
            continue
        out.append(
            {
                "id": chunk.id,
                "section": chunk.section,
                "title": chunk.title,
                "source_name": chunk.source_name,
                "official_url": chunk.official_url,
                "accessed_date": chunk.accessed_date,
                "verification": chunk.verification,
                "source_id": chunk.source_id,
                "document_title": chunk.document_title or chunk.title,
                "document_type": chunk.document_type,
                "official_organization": chunk.official_organization,
                "source_url": chunk.source_url or chunk.official_url,
                "page_location": chunk.page_location,
                "excerpt": chunk.excerpt or chunk.text[:600],
                "summary": chunk.summary or chunk.text[:240],
                "applicability": chunk.applicability or chunk.assessment_year or chunk.tax_year or "Unknown",
                "effective_period": chunk.effective_period,
                "verified_date": chunk.verified_date,
                "rule": chunk.rule,
                "form": chunk.form,
                "assessment_year": chunk.assessment_year,
                "tax_year": chunk.tax_year,
                "effective_from": chunk.effective_from,
                "effective_to": chunk.effective_to,
                "status": chunk.status,
                "verification_status": chunk.verification_status,
                "verification_state": {"VERIFIED_OFFICIAL": "Verified", "PENDING_VERIFICATION": "Pending verification", "NOT_APPLICABLE": "Not applicable", "UNKNOWN": "Unknown"}.get(chunk.verification_status, "Unknown"),
                "why_supports": f"This source covers {chunk.section or chunk.title}, which is relevant to the explanation.",
            }
        )
    return out
