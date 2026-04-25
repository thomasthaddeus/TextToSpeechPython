"""Unified document scraping helpers for the import dialog."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentRow:
    item_number: int
    title: str
    primary_text: str
    secondary_text: str = ""


class DocumentScraper:
    """Scrape common document formats into normalized document rows."""

    SUPPORTED_FILTER = (
        "Supported Documents (*.txt *.docx *.pdf *.html *.htm *.rtf *.epub "
        "*.xlsx *.xls *.csv *.pptx);;"
        "Text Documents (*.txt);;"
        "Word Documents (*.docx);;"
        "PDF Files (*.pdf);;"
        "HTML Files (*.html *.htm);;"
        "RTF Files (*.rtf);;"
        "EPUB Files (*.epub);;"
        "Spreadsheet Files (*.xlsx *.xls *.csv);;"
        "PowerPoint Files (*.pptx);;"
        "All Files (*.*)"
    )

    def scrape_file(self, file_path):
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".txt":
            rows = self._scrape_txt(path)
        elif suffix == ".docx":
            rows = self._scrape_docx(path)
        elif suffix == ".pdf":
            rows = self._scrape_pdf(path)
        elif suffix in {".html", ".htm"}:
            rows = self._scrape_html(path)
        elif suffix == ".rtf":
            rows = self._scrape_rtf(path)
        elif suffix == ".epub":
            rows = self._scrape_epub(path)
        elif suffix in {".xlsx", ".xls", ".csv"}:
            rows = self._scrape_spreadsheet(path)
        elif suffix == ".pptx":
            rows = self._scrape_pptx(path)
        else:
            raise ValueError(f"Unsupported document type: {suffix or '[none]'}")

        return [self._row_to_dict(row, path) for row in rows if self._has_content(row)]

    def _row_to_dict(self, row, path):
        return {
            "item_number": row.item_number,
            "title": row.title,
            "primary_text": row.primary_text,
            "secondary_text": row.secondary_text,
            "source_path": str(path),
            "source_type": path.suffix.lower().lstrip("."),
        }

    def _has_content(self, row):
        return bool((row.primary_text or "").strip() or (row.secondary_text or "").strip())

    def _split_blocks(self, text):
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        blocks = [block.strip() for block in normalized.split("\n\n")]
        return [block for block in blocks if block]

    def _scrape_txt(self, path):
        text = path.read_text(encoding="utf-8")
        blocks = self._split_blocks(text) or [text.strip()]
        return [
            DocumentRow(index, f"Text Block {index}", block)
            for index, block in enumerate(blocks, start=1)
            if block
        ]

    def _scrape_docx(self, path):
        from docx import Document

        document = Document(path)
        paragraphs = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]
        return [
            DocumentRow(index, f"Paragraph {index}", paragraph)
            for index, paragraph in enumerate(paragraphs, start=1)
        ]

    def _scrape_pdf(self, path):
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        rows = []
        for index, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            rows.append(DocumentRow(index, f"Page {index}", page_text))
        return rows

    def _scrape_html(self, path):
        from bs4 import BeautifulSoup

        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else path.stem
        paragraphs = [
            element.get_text(" ", strip=True)
            for element in soup.find_all(["h1", "h2", "h3", "p", "li"])
            if element.get_text(" ", strip=True)
        ]
        if not paragraphs:
            paragraphs = [soup.get_text(" ", strip=True)]
        return [
            DocumentRow(index, f"{title} Section {index}", paragraph)
            for index, paragraph in enumerate(paragraphs, start=1)
            if paragraph
        ]

    def _scrape_rtf(self, path):
        from striprtf.striprtf import rtf_to_text

        rtf_content = path.read_text(encoding="utf-8")
        text = rtf_to_text(rtf_content)
        blocks = self._split_blocks(text) or [text.strip()]
        return [
            DocumentRow(index, f"RTF Block {index}", block)
            for index, block in enumerate(blocks, start=1)
            if block
        ]

    def _scrape_epub(self, path):
        from bs4 import BeautifulSoup
        from ebooklib import ITEM_DOCUMENT, epub

        book = epub.read_epub(str(path))
        rows = []
        item_number = 1
        for item in book.get_items():
            if item.get_type() != ITEM_DOCUMENT:
                continue
            soup = BeautifulSoup(item.get_content(), "html.parser")
            title = soup.title.get_text(strip=True) if soup.title else f"Chapter {item_number}"
            text = soup.get_text(" ", strip=True)
            if not text:
                continue
            rows.append(DocumentRow(item_number, title, text))
            item_number += 1
        return rows

    def _scrape_spreadsheet(self, path):
        import pandas as pd

        if path.suffix.lower() == ".csv":
            sheets = {"Sheet1": pd.read_csv(path)}
        else:
            sheets = pd.read_excel(path, sheet_name=None)

        rows = []
        item_number = 1
        for sheet_name, frame in sheets.items():
            cleaned_frame = frame.fillna("")
            for row_index, row in cleaned_frame.iterrows():
                values = [
                    f"{column}: {str(value).strip()}"
                    for column, value in row.items()
                    if str(value).strip()
                ]
                if not values:
                    continue
                rows.append(
                    DocumentRow(
                        item_number,
                        f"{sheet_name} Row {row_index + 1}",
                        " | ".join(values),
                    )
                )
                item_number += 1
        return rows

    def _scrape_pptx(self, path):
        from pptx import Presentation

        presentation = Presentation(str(path))
        rows = []
        for index, slide in enumerate(presentation.slides, start=1):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text.strip())
            notes_text = ""
            if slide.has_notes_slide:
                notes_text = slide.notes_slide.notes_text_frame.text.strip()
            rows.append(
                DocumentRow(
                    index,
                    f"Slide {index}",
                    " ".join(slide_text).strip(),
                    notes_text,
                )
            )
        return rows
