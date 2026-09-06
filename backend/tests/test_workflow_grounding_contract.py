from app.workflows.handlers import get_workflow_handler


def test_supported_handler_returns_authoritative_grounding_provenance():
    notice = {
        "section": "245",
        "assessment_year": "2025-26",
        "official_text": "Income Tax Department outstanding demand under section 245.",
        "demand_facts": {"demand_amount": 12000, "source": "processing"},
    }
    result = get_workflow_handler("demand_adjustment_245").get_questions(notice)
    assert "grounding" in result
    assert result["grounding"]["sources"]
    assert all(source["official_url"].startswith("https://www.incometax.gov.in/") for source in result["grounding"]["sources"])


def test_multi_choice_and_choice_with_other_values_are_preserved_for_api_contract():
    notice = {
        "section": "245",
        "official_text": "Outstanding demand under section 245.",
        "demand_facts": {"demand_amount": 12000, "source": "processing"},
    }
    questions = get_workflow_handler("demand_adjustment_245").get_questions(notice)["questions"]
    reasons = next(question for question in questions if question["id"] == "dispute_reasons")
    assert reasons["question_type"] == "multi_choice"
    assert isinstance(reasons["options"], list)
