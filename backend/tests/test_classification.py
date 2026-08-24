import pytest

from app.rules.notice_types import (
    NoticeCategory,
    SUPPORTED_CATEGORIES,
    classify_notice,
    is_supported,
)


@pytest.mark.parametrize(
    "section,expected",
    [
        ("143(1)(a)", NoticeCategory.INCOME_MISMATCH_143_1A),
        ("143(1)", NoticeCategory.INCOME_MISMATCH_143_1A),
        (" 143(1)(a) ", NoticeCategory.INCOME_MISMATCH_143_1A),
        ("139(9)", NoticeCategory.DEFECTIVE_RETURN_139_9),
        ("148", NoticeCategory.UNSUPPORTED),
        ("245", NoticeCategory.UNSUPPORTED),
        ("", NoticeCategory.UNSUPPORTED),
        (None, NoticeCategory.UNSUPPORTED),
    ],
)
def test_classification(section, expected):
    assert classify_notice({"section": section}) == expected


def test_release_candidate_support_scope():
    # RC guides exactly one notice type; anything else must refuse.
    assert SUPPORTED_CATEGORIES == {NoticeCategory.INCOME_MISMATCH_143_1A}
    assert is_supported(NoticeCategory.INCOME_MISMATCH_143_1A)
    assert not is_supported(NoticeCategory.DEFECTIVE_RETURN_139_9)
    assert not is_supported(NoticeCategory.UNSUPPORTED)
