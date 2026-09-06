"""Verified official Income Tax portal destinations."""

OFFICIAL_PORTAL = "https://www.incometax.gov.in/iec/foportal/"


def official_portal_payload() -> dict[str, str]:
    return {
        "url": OFFICIAL_PORTAL,
        "submission_boundary": "Tax Mitra prepares information for review; the taxpayer must complete any official submission on the Income Tax e-Filing portal.",
    }
