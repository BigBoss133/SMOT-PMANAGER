"""PDF text extraction and chapter splitting using PyMuPDF."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


@dataclass
class Chapter:
    """A single chapter extracted from a PDF."""

    number: int
    title: str
    topic: str  # "charter", "stakeholder/raci", "wbs", "budget", "risks", "agile", "general"
    text: str


# Pattern matching "CAPITOLO X:" at the start of a line (case-insensitive)
_CAPITOLO_RE = re.compile(r"CAPITOLO\s+(\d+)\s*:\s*(.+)", re.IGNORECASE)

_TOPIC_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"CHARTER", re.IGNORECASE), "charter"),
    (re.compile(r"STAKEHOLDER|RACI", re.IGNORECASE), "stakeholder/raci"),
    (re.compile(r"WBS|WORK\s+BREAKDOWN|SCHEDULE|CRONOPROGRAMMA", re.IGNORECASE), "wbs"),
    (re.compile(r"BUDGET|COSTI|EARNED\s+VALUE", re.IGNORECASE), "budget"),
    (re.compile(r"RISCHI?|RISK", re.IGNORECASE), "risks"),
    (re.compile(r"AGILE|SCRUM|SPRINT|KANBAN", re.IGNORECASE), "agile"),
]


def _detect_topic(title: str) -> str:
    """Map chapter title to topic for RAG metadata filtering."""
    for pattern, topic in _TOPIC_RULES:
        if pattern.search(title):
            return topic
    return "general"


class PDFExtractor:
    """Extract text and chapters from PDF documents."""

    def __init__(self, pdf_path: str | Path) -> None:
        self.pdf_path = Path(pdf_path)

    def extract_text(self) -> str:
        """Extract all text from the PDF."""
        self._validate_pdf()
        doc = fitz.open(str(self.pdf_path))
        try:
            return "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()

    def extract_chapters(self) -> list[Chapter]:
        """Split PDF into chapters based on 'CAPITOLO X:' pattern."""
        self._validate_pdf()
        sections = self._get_section_pages()
        if not sections:
            return []

        doc = fitz.open(str(self.pdf_path))
        try:
            chapters: list[Chapter] = []
            for idx, (start_page, title, number) in enumerate(sections):
                end_page = sections[idx + 1][0] if idx + 1 < len(sections) else len(doc)
                text = "\n".join(doc[p].get_text() for p in range(start_page, end_page))
                topic = _detect_topic(title)
                chapters.append(Chapter(number=number, title=title, topic=topic, text=text))
            return chapters
        finally:
            doc.close()

    def _get_section_pages(self) -> list[tuple[int, str, int]]:
        """Find chapter boundaries by scanning for 'CAPITOLO X:' pattern.

        Returns list of (page_index, title, chapter_number) sorted by page.
        """
        doc = fitz.open(str(self.pdf_path))
        try:
            sections: list[tuple[int, str, int]] = []
            for page_idx in range(len(doc)):
                text = doc[page_idx].get_text()
                for m in _CAPITOLO_RE.finditer(text):
                    chap_num = int(m.group(1))
                    raw_title = m.group(2).strip()
                    # Title may span multiple lines — collect continuation lines
                    after = text[m.end() :]
                    lines_after = after.split("\n")
                    continuation: list[str] = []
                    for line in lines_after:
                        stripped = line.strip()
                        if not stripped:
                            if continuation:
                                break
                            continue
                        if re.match(r"^\d+\.", stripped) or stripped.lower().startswith(
                            "dispensa di",
                        ):
                            break
                        continuation.append(stripped)
                    full_title = f"{raw_title} {' '.join(continuation)}".strip()
                    if not continuation:
                        full_title = raw_title
                    # Deduplicate: keep first occurrence of each chapter number
                    if not any(s[2] == chap_num for s in sections):
                        sections.append((page_idx, full_title.strip(), chap_num))
            sections.sort(key=lambda s: s[0])
            return sections
        finally:
            doc.close()

    def _validate_pdf(self) -> bool:
        """Check if PDF is valid and extractable.

        Raises FileNotFoundError if the file doesn't exist.
        Raises ValueError if the file is not a valid PDF.
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        try:
            doc = fitz.open(str(self.pdf_path))
            page_count = len(doc)
            doc.close()
        except Exception as exc:
            raise ValueError(f"Cannot open PDF: {self.pdf_path}") from exc
        if page_count == 0:
            raise ValueError(f"PDF has no pages: {self.pdf_path}")
        return True
