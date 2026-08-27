"""Ingest the curated Tax Mitra source pack into metadata-preserving chunks.

Default scope is the core notice workflow. Use --all for the complete local
pack. The source pack itself is never copied into the application at runtime.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

CORE = {"SEC-142", "SEC-143", "SEC-144", "SEC-144B", "EP-MANUAL", "EP-FAQ", "AIS-FAQ", "TRANSITION-FAQ", "1399-FAQ", "SCRUTINY-GUIDELINES-2026", "NOTIFICATION-6-2021"}
VALID_STATUS = {"CURRENT", "SUPERSEDED", "HISTORICAL", "UNKNOWN"}
VALID_VERIFICATION = {"VERIFIED_OFFICIAL", "NEEDS_REVIEW"}

def _repair(record: dict) -> dict:
    """Repair the pack's four shifted late JSON records conservatively."""
    r = dict(record)
    if r.get("status") not in VALID_STATUS:
        # The pack report/manifest uses this exact shifted pattern.
        r["notes"] = r.get("status", r.get("notes", ""))
        r["status"] = r.get("priority", "UNKNOWN") if r.get("priority") in VALID_STATUS else r.get("topic", "UNKNOWN")
        r["verification_status"] = r.get("priority") if r.get("priority") in VALID_VERIFICATION else r.get("verification_status", "NEEDS_REVIEW")
        r["priority"] = r.get("form", r.get("priority", "P1")) if str(r.get("form", "")).startswith("P") else r.get("priority", "P1")
    # These records were exported with the same four-column shift. Their
    # source-pack report supplies the safe canonical values below.
    corrections = {
        "FINANCE-ACT-2026": ("P1", "CURRENT", "VERIFIED_OFFICIAL"),
        "SCRUTINY-GUIDELINES-2026": ("P0", "CURRENT", "VERIFIED_OFFICIAL"),
        "NOTIFICATION-6-2021": ("P0", "HISTORICAL", "VERIFIED_OFFICIAL"),
        "1399-FAQ": ("P0", "CURRENT", "VERIFIED_OFFICIAL"),
    }
    if r.get("source_id") in corrections:
        r["priority"], r["status"], r["verification_status"] = corrections[r["source_id"]]
    if r.get("source_id") == "NOTIFICATION-6-2021":
        r["act_section"] = "143(2), 142(1), 142(2A), 144"
        r["tax_year"] = ""
        r["form"] = ""
    if r.get("source_id") in {"FINANCE-ACT-2026", "SCRUTINY-GUIDELINES-2026", "1399-FAQ"}:
        r["form"] = ""
    if r.get("verification_status") not in VALID_VERIFICATION:
        r["verification_status"] = "NEEDS_REVIEW"
    return r

def _text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path), strict=False)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="replace")

def _chunks(text: str, size: int = 1800) -> list[str]:
    text = re.sub(r"\r\n?", "\n", text).strip()
    paragraphs = re.split(r"\n\s*\n", text)
    result, current = [], ""
    for paragraph in paragraphs:
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        if not paragraph:
            continue
        if current and len(current) + len(paragraph) + 1 > size:
            result.append(current)
            current = ""
        while len(paragraph) > size:
            result.append(paragraph[:size])
            paragraph = paragraph[size:]
        current = f"{current} {paragraph}".strip()
    if current:
        result.append(current)
    return result

def _frontmatter(record: dict, chunk_id: str) -> str:
    values = {
        "id": chunk_id, "source_id": record["source_id"], "section": record.get("act_section", ""),
        "title": record.get("title", ""), "document_title": record.get("title", ""),
        "document_type": record.get("document_type", ""), "official_organization": record.get("official_organization", ""),
        "official_url": record.get("source_url", ""), "source_url": record.get("source_url", ""),
        "accessed_date": record.get("retrieved_on", ""), "verification": record.get("verification_status", "NEEDS_REVIEW"),
        "verification_status": record.get("verification_status", "NEEDS_REVIEW"), "rule": record.get("rule", ""),
        "form": record.get("form", ""), "assessment_year": record.get("assessment_year", ""),
        "tax_year": record.get("tax_year", ""), "effective_from": record.get("effective_from", ""),
        "effective_to": record.get("effective_to", ""), "status": record.get("status", "UNKNOWN"),
        "tags": ", ".join(filter(None, [record.get("topic", ""), record.get("act_section", "")])),
    }
    lines = ["---"] + [f'{key}: "{str(value).replace(chr(34), chr(39))}"' for key, value in values.items()] + ["---"]
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((args.source_dir / "source_manifest.json").read_text(encoding="utf-8"))
    records = [_repair(item) for item in manifest]
    selected = [r for r in records if r.get("local_filename") and (args.all or r.get("source_id") in CORE)]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    normalized = []
    count = 0
    for record in selected:
        path = args.source_dir / record["local_filename"]
        if not path.exists():
            continue
        body = _text(path)
        normalized.append({k: v for k, v in record.items() if k != "notes"})
        for number, chunk in enumerate(_chunks(body)):
            chunk_id = f"{record['source_id'].lower()}-{number + 1:04d}"
            (args.output_dir / f"{chunk_id}.md").write_text(_frontmatter(record, chunk_id) + "\n" + chunk + "\n", encoding="utf-8")
            count += 1
    (args.output_dir / "source_manifest.normalized.json").write_text(json.dumps(normalized, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"documents": len(normalized), "chunks": count, "output": str(args.output_dir)}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
