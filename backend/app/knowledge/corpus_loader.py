"""Corpus loader: parses markdown chunks with simple frontmatter.

Frontmatter keys: id, section, title, source_name, official_url,
accessed_date, verification, tags (comma-separated).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

_TEXT_KEYS = {"section", "title", "source_name", "official_url", "accessed_date", "verification"}


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
                "excerpt": chunk.text[:600],
            }
        )
    return out
