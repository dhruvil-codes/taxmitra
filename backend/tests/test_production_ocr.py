from pathlib import Path


def test_production_image_installs_and_verifies_ocr_languages():
    dockerfile = Path(__file__).parents[2] / "Dockerfile"
    content = dockerfile.read_text(encoding="utf-8")
    assert "tesseract-ocr" in content
    assert "tesseract-ocr-hin" in content
    assert "tesseract --list-langs" in content
