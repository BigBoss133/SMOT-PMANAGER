"""Tests for PDF text extraction and chapter splitting."""

from __future__ import annotations

import tempfile
from pathlib import Path

import fitz
import pytest

from pman.pdf_extractor import Chapter, PDFExtractor, _detect_topic

REAL_PDF = Path("/home/michele-finocchiaro/Scrivania/SmotPmanager/Google_PM_Dispensa_Universitaria_LIBRO.pdf")


def _create_test_pdf(pages: list[str], path: Path) -> Path:
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


class TestValidatePdf:
    def test_missing_file_raises_file_not_found(self, tmp_path: Path) -> None:
        ext = PDFExtractor(tmp_path / "nonexistent.pdf")
        with pytest.raises(FileNotFoundError, match="PDF not found"):
            ext._validate_pdf()

    def test_non_pdf_raises_value_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.pdf"
        bad.write_text("not a pdf")
        ext = PDFExtractor(bad)
        with pytest.raises(ValueError, match="Cannot open PDF"):
            ext._validate_pdf()

    def test_valid_pdf_returns_true(self, tmp_path: Path) -> None:
        pdf = _create_test_pdf(["Hello world"], tmp_path / "ok.pdf")
        ext = PDFExtractor(pdf)
        assert ext._validate_pdf() is True


class TestExtractText:
    def test_returns_nonempty_string(self, tmp_path: Path) -> None:
        pdf = _create_test_pdf(["Hello world from PDF"], tmp_path / "t.pdf")
        ext = PDFExtractor(pdf)
        text = ext.extract_text()
        assert isinstance(text, str)
        assert len(text) > 0

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        ext = PDFExtractor(tmp_path / "nope.pdf")
        with pytest.raises(FileNotFoundError):
            ext.extract_text()

    def test_real_pdf_extracts_over_100k_chars(self) -> None:
        if not REAL_PDF.exists():
            pytest.skip("Real PDF not available")
        ext = PDFExtractor(REAL_PDF)
        text = ext.extract_text()
        assert len(text) > 100_000, f"Expected >100K chars, got {len(text)}"


class TestExtractChapters:
    def test_no_chapters_returns_empty(self, tmp_path: Path) -> None:
        pdf = _create_test_pdf(["Just some text without chapters"], tmp_path / "nochap.pdf")
        ext = PDFExtractor(pdf)
        chapters = ext.extract_chapters()
        assert chapters == []

    def test_single_chapter(self, tmp_path: Path) -> None:
        pdf = _create_test_pdf(
            ["CAPITOLO 1: INTRODUZIONE AL PROJECT MANAGEMENT\nSome intro text"],
            tmp_path / "one.pdf",
        )
        ext = PDFExtractor(pdf)
        chapters = ext.extract_chapters()
        assert len(chapters) >= 1
        assert chapters[0].number == 1
        assert "INTRODUZIONE" in chapters[0].title

    def test_real_pdf_has_at_least_35_chapters(self) -> None:
        if not REAL_PDF.exists():
            pytest.skip("Real PDF not available")
        ext = PDFExtractor(REAL_PDF)
        chapters = ext.extract_chapters()
        assert len(chapters) >= 35, f"Expected ≥35 chapters, got {len(chapters)}"
        for ch in chapters:
            assert isinstance(ch, Chapter)
            assert ch.number > 0
            assert len(ch.title) > 0
            assert ch.topic in ("charter", "stakeholder/raci", "wbs", "budget", "risks", "agile", "general")
            assert len(ch.text) > 0


class TestDetectTopic:
    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("IL PROJECT CHARTER", "charter"),
            ("ANALISI DEGLI STAKEHOLDER", "stakeholder/raci"),
            ("LA MATRICE RACI", "stakeholder/raci"),
            ("WORK BREAKDOWN STRUCTURE (WBS)", "wbs"),
            ("GESTIONE DELLA SCHEDULE", "wbs"),
            ("GESTIONE DEL BUDGET E EARNED VALUE MANAGEMENT", "budget"),
            ("GESTIONE DEI RISCHI", "risks"),
            ("FILOSOFIA E MANIFESTO AGILE", "agile"),
            ("FRAMEWORK SCRUM RUOLI E RESPONSABILITA", "agile"),
            ("INTRODUZIONE AL PROJECT MANAGEMENT", "general"),
            ("IL CICLO DI VITA DEL PROGETTO", "general"),
        ],
    )
    def test_topic_mapping(self, title: str, expected: str) -> None:
        assert _detect_topic(title) == expected

    def test_wbs_chapter_on_real_pdf(self) -> None:
        if not REAL_PDF.exists():
            pytest.skip("Real PDF not available")
        ext = PDFExtractor(REAL_PDF)
        chapters = ext.extract_chapters()
        wbs = [c for c in chapters if c.number == 13]
        assert len(wbs) == 1
        assert wbs[0].topic == "wbs"