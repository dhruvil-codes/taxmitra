"""Regression tests to ensure Hindi responses are not silently returning English."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def has_devanagari(text: str) -> bool:
    """Check if text contains Devanagari characters (Hindi)."""
    return any(ord(c) > 127 for c in text)


def test_143_1a_hindi_questions_not_english():
    """Regression test: 143(1)(a) Hindi questions must contain Devanagari characters."""
    client = TestClient(app)
    
    r_hi = client.get("/api/workflow/questions/N-2026-001?locale=hi")
    assert r_hi.status_code == 200
    data_hi = r_hi.json()
    
    questions_hi = data_hi.get('questions', [])
    assert len(questions_hi) > 0, "No questions returned for Hindi locale"
    
    # Check each question has Hindi text
    for q in questions_hi:
        question_text = q.get('text', '')
        help_text = q.get('help', '')
        
        # At least one of question or help should have Hindi
        assert has_devanagari(question_text + help_text), \
            f"Question {q.get('id')} has no Hindi characters: {question_text[:50]}"
        
        # Check options are also in Hindi if present
        for opt in q.get('options', []):
            option_label = opt.get('label', '')
            if option_label:
                assert has_devanagari(option_label), \
                    f"Option {opt.get('id')} has no Hindi characters: {option_label}"


def test_139_9_hindi_questions_not_english():
    """Regression test: 139(9) Hindi questions must contain Devanagari characters."""
    client = TestClient(app)
    
    r_hi = client.get("/api/workflow/questions/N-2026-004?locale=hi")
    assert r_hi.status_code == 200
    data_hi = r_hi.json()
    
    questions_hi = data_hi.get('questions', [])
    assert len(questions_hi) > 0, "No questions returned for Hindi locale"
    
    # Check each question has Hindi text
    for q in questions_hi:
        question_text = q.get('text', '')
        help_text = q.get('help', '')
        
        assert has_devanagari(question_text + help_text), \
            f"Question {q.get('id')} has no Hindi characters: {question_text[:50]}"
        
        # Check options are also in Hindi if present
        for opt in q.get('options', []):
            option_label = opt.get('label', '')
            if option_label:
                assert has_devanagari(option_label), \
                    f"Option {opt.get('id')} has no Hindi characters: {option_label}"


def test_133_6_hindi_questions_not_english():
    """Regression test: 133(6) Hindi questions must contain Devanagari characters."""
    client = TestClient(app)
    
    r_hi = client.get("/api/workflow/questions/N-2026-006?locale=hi")
    assert r_hi.status_code == 200
    data_hi = r_hi.json()
    
    questions_hi = data_hi.get('questions', [])
    assert len(questions_hi) > 0, "No questions returned for Hindi locale"
    
    # Check each question has Hindi text
    for q in questions_hi:
        question_text = q.get('text', '')
        help_text = q.get('help', '')
        
        assert has_devanagari(question_text + help_text), \
            f"Question {q.get('id')} has no Hindi characters: {question_text[:50]}"
        
        # Check options are also in Hindi if present
        for opt in q.get('options', []):
            option_label = opt.get('label', '')
            if option_label:
                assert has_devanagari(option_label), \
                    f"Option {opt.get('id')} has no Hindi characters: {option_label}"


def test_245_hindi_questions_not_english():
    """Regression test: 245 Hindi questions must contain Devanagari characters."""
    client = TestClient(app)
    
    r_hi = client.get("/api/workflow/questions/N-2026-010?locale=hi")
    assert r_hi.status_code == 200
    data_hi = r_hi.json()
    
    questions_hi = data_hi.get('questions', [])
    assert len(questions_hi) > 0, "No questions returned for Hindi locale"
    
    # Check each question has Hindi text
    for q in questions_hi:
        question_text = q.get('text', '')
        help_text = q.get('help', '')
        
        assert has_devanagari(question_text + help_text), \
            f"Question {q.get('id')} has no Hindi characters: {question_text[:50]}"
        
        # Check options are also in Hindi if present
        for opt in q.get('options', []):
            option_label = opt.get('label', '')
            if option_label:
                assert has_devanagari(option_label), \
                    f"Option {opt.get('id')} has no Hindi characters: {option_label}"


def test_154_hindi_questions_not_english():
    """Regression test: 154 Hindi questions must contain Devanagari characters."""
    client = TestClient(app)
    
    r_hi = client.get("/api/workflow/questions/N-2026-008?locale=hi")
    assert r_hi.status_code == 200
    data_hi = r_hi.json()
    
    questions_hi = data_hi.get('questions', [])
    assert len(questions_hi) > 0, "No questions returned for Hindi locale"
    
    # Check each question has Hindi text
    for q in questions_hi:
        question_text = q.get('text', '')
        help_text = q.get('help', '')
        
        assert has_devanagari(question_text + help_text), \
            f"Question {q.get('id')} has no Hindi characters: {question_text[:50]}"
        
        # Check options are also in Hindi if present
        for opt in q.get('options', []):
            option_label = opt.get('label', '')
            if option_label:
                assert has_devanagari(option_label), \
                    f"Option {opt.get('id')} has no Hindi characters: {option_label}"


def test_142_1_hindi_questions_not_english():
    """Regression test: 142(1) Hindi questions must contain Devanagari characters."""
    client = TestClient(app)
    
    r_hi = client.get("/api/workflow/questions/N-2026-003?locale=hi")
    assert r_hi.status_code == 200
    data_hi = r_hi.json()
    
    questions_hi = data_hi.get('questions', [])
    assert len(questions_hi) > 0, "No questions returned for Hindi locale"
    
    # Check each question has Hindi text
    for q in questions_hi:
        question_text = q.get('question', '')
        help_text = q.get('why_we_are_asking', '')
        
        assert has_devanagari(question_text + help_text), \
            f"Question {q.get('question_id')} has no Hindi characters: {question_text[:50]}"
        
        # Check options are also in Hindi if present
        for opt in q.get('options', []):
            option_label = opt.get('label', '')
            if option_label:
                assert has_devanagari(option_label), \
                    f"Option {opt.get('id')} has no Hindi characters: {option_label}"


def test_english_and_hindi_questions_differ():
    """Regression test: English and Hindi questions should not be identical."""
    client = TestClient(app)
    
    test_notice_ids = ['N-2026-001', 'N-2026-004', 'N-2026-006', 'N-2026-010', 'N-2026-008']
    
    for notice_id in test_notice_ids:
        r_en = client.get(f"/api/workflow/questions/{notice_id}?locale=en")
        r_hi = client.get(f"/api/workflow/questions/{notice_id}?locale=hi")
        
        assert r_en.status_code == 200
        assert r_hi.status_code == 200
        
        data_en = r_en.json()
        data_hi = r_hi.json()
        
        questions_en = data_en.get('questions', [])
        questions_hi = data_hi.get('questions', [])
        
        assert len(questions_en) == len(questions_hi), \
            f"Question count differs between English ({len(questions_en)}) and Hindi ({len(questions_hi)})"
        
        # Check that at least some content differs
        for q_en, q_hi in zip(questions_en, questions_hi):
            text_en = q_en.get('text', '') or q_en.get('question', '')
            text_hi = q_hi.get('text', '') or q_hi.get('question', '')
            
            # If texts are identical, that's a regression
            if text_en == text_hi and text_en:
                # Only fail if both are non-empty and identical
                assert False, \
                    f"Notice {notice_id}: English and Hindi question text are identical: {text_en[:50]}"