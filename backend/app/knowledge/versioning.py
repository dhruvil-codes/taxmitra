"""Applicability helpers for the Income-tax Act transition."""

from __future__ import annotations

from dataclasses import dataclass

ACT_1961 = "Income-tax Act, 1961"
ACT_2025 = "Income Tax Act, 2025"


@dataclass(frozen=True)
class Applicability:
    act_version: str | None = None
    ambiguous: bool = False


def resolve_applicability(
    assessment_year: str | None = None,
    tax_year: str | None = None,
    act_version: str | None = None,
) -> Applicability:
    """Resolve only the transition rule documented by the official portal.

    AY 2026-27 and earlier follow the 1961 Act; Tax Year 2026-27 onward
    follows the 2025 Act where the proceeding is under the new regime. If a
    caller supplies conflicting signals, retrieval must surface ambiguity.
    """
    if act_version:
        normalized = act_version.lower().replace("income-tax", "income tax")
        if "1961" in normalized:
            explicit = ACT_1961
        elif "2025" in normalized:
            explicit = ACT_2025
        else:
            explicit = act_version
    else:
        explicit = None

    inferred: set[str] = set()
    if assessment_year:
        ay = assessment_year.replace("AY", "").strip()
        if ay.startswith("2026-27") or ay[:4].isdigit() and int(ay[:4]) <= 2026:
            inferred.add(ACT_1961)
    if tax_year:
        ty = tax_year.replace("TY", "").replace("Tax Year", "").strip()
        if ty.startswith("2026-27") or ty[:4].isdigit() and int(ty[:4]) >= 2026:
            inferred.add(ACT_2025)
    if explicit and inferred and explicit not in inferred:
        return Applicability(act_version=explicit, ambiguous=True)
    if explicit:
        return Applicability(explicit)
    if len(inferred) == 1:
        return Applicability(next(iter(inferred)))
    if len(inferred) > 1:
        return Applicability(None, ambiguous=True)
    return Applicability()


def chunk_matches_context(chunk, applicability: Applicability, workflow_context: str | None = None) -> bool:
    """Return whether an item is safe to use for the requested context."""
    declared_act = chunk.act_version
    if not declared_act:
        if "tax year" in chunk.tax_year.lower() or chunk.tax_year.lower().startswith("ty "):
            declared_act = ACT_2025
        elif chunk.assessment_year:
            declared_act = ACT_1961
    if applicability.act_version and declared_act:
        normalized = declared_act.lower().replace("income-tax", "income tax")
        if ("1961" in normalized) != (applicability.act_version == ACT_1961):
            return False
        if ("2025" in normalized) != (applicability.act_version == ACT_2025):
            return False
    if workflow_context and chunk.workflow_context:
        wanted = workflow_context.lower()
        if not any(wanted in value.lower() or value.lower() in wanted or any(part in value.lower() for part in wanted.split('_') if len(part) > 2) for value in chunk.workflow_context):
            return False
    return chunk.status not in {"SUPERSEDED", "HISTORICAL"}
