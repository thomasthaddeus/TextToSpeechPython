"""Unified document scraping helpers for the import dialog."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path


@dataclass
class DocumentRow:
    item_number: int
    title: str
    primary_text: str
    secondary_text: str = ""


@dataclass(frozen=True)
class ParserDependency:
    module_name: str
    package_name: str
    purpose: str


class DocumentScraper:
    """Scrape common document formats into normalized document rows."""

    SUPPORTED_FILTER = (
        "Supported Documents (*.txt *.docx *.pdf *.html *.htm *.rtf *.epub "
        "*.xlsx *.xls *.csv *.pptx *.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp);;"
        "Text Documents (*.txt);;"
        "Word Documents (*.docx);;"
        "PDF Files (*.pdf);;"
        "HTML Files (*.html *.htm);;"
        "RTF Files (*.rtf);;"
        "EPUB Files (*.epub);;"
        "Spreadsheet Files (*.xlsx *.xls *.csv);;"
        "PowerPoint Files (*.pptx);;"
        "Image Files (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp);;"
        "All Files (*.*)"
    )
    FORMAT_DEPENDENCIES = {
        ".txt": (),
        ".docx": (
            ParserDependency("docx", "python-docx", "Word document imports"),
        ),
        ".pdf": (
            ParserDependency("pypdf", "pypdf", "PDF text-layer imports"),
        ),
        ".html": (
            ParserDependency("bs4", "beautifulsoup4", "HTML imports"),
        ),
        ".htm": (
            ParserDependency("bs4", "beautifulsoup4", "HTML imports"),
        ),
        ".rtf": (
            ParserDependency("striprtf", "striprtf", "RTF imports"),
        ),
        ".epub": (
            ParserDependency("bs4", "beautifulsoup4", "EPUB HTML extraction"),
            ParserDependency("ebooklib", "ebooklib", "EPUB imports"),
        ),
        ".xlsx": (
            ParserDependency("pandas", "pandas", "spreadsheet imports"),
            ParserDependency("openpyxl", "openpyxl", "XLSX imports"),
        ),
        ".xls": (
            ParserDependency("pandas", "pandas", "spreadsheet imports"),
            ParserDependency("xlrd", "xlrd", "legacy XLS imports"),
        ),
        ".csv": (
            ParserDependency("pandas", "pandas", "CSV imports"),
        ),
        ".pptx": (
            ParserDependency("pptx", "python-pptx", "PowerPoint imports"),
        ),
        ".png": (
            ParserDependency("PIL", "pillow", "image imports"),
            ParserDependency("pytesseract", "pytesseract", "image OCR imports"),
        ),
        ".jpg": (
            ParserDependency("PIL", "pillow", "image imports"),
            ParserDependency("pytesseract", "pytesseract", "image OCR imports"),
        ),
        ".jpeg": (
            ParserDependency("PIL", "pillow", "image imports"),
            ParserDependency("pytesseract", "pytesseract", "image OCR imports"),
        ),
        ".tif": (
            ParserDependency("PIL", "pillow", "image imports"),
            ParserDependency("pytesseract", "pytesseract", "image OCR imports"),
        ),
        ".tiff": (
            ParserDependency("PIL", "pillow", "image imports"),
            ParserDependency("pytesseract", "pytesseract", "image OCR imports"),
        ),
        ".bmp": (
            ParserDependency("PIL", "pillow", "image imports"),
            ParserDependency("pytesseract", "pytesseract", "image OCR imports"),
        ),
        ".webp": (
            ParserDependency("PIL", "pillow", "image imports"),
            ParserDependency("pytesseract", "pytesseract", "image OCR imports"),
        ),
    }
    OCR_PDF_DEPENDENCIES = (
        ParserDependency("pypdfium2", "pypdfium2", "scanned PDF rendering"),
        ParserDependency("PIL", "pillow", "scanned PDF image handling"),
        ParserDependency("pytesseract", "pytesseract", "scanned PDF OCR"),
    )

    @classmethod
    def missing_dependencies_for_suffix(cls, suffix):
        """Return parser dependencies missing for a specific file suffix."""
        normalized_suffix = suffix.lower()
        return [
            dependency
            for dependency in cls.FORMAT_DEPENDENCIES.get(normalized_suffix, ())
            if importlib.util.find_spec(dependency.module_name) is None
        ]

    @classmethod
    def missing_runtime_dependencies(cls):
        """Return missing parser dependencies for advertised import formats."""
        missing_by_package = {}
        for dependencies in cls.FORMAT_DEPENDENCIES.values():
            for dependency in dependencies:
                if importlib.util.find_spec(dependency.module_name) is None:
                    missing_by_package[dependency.package_name] = dependency

        for dependency in cls.OCR_PDF_DEPENDENCIES:
            if importlib.util.find_spec(dependency.module_name) is None:
                missing_by_package[dependency.package_name] = dependency

        return sorted(missing_by_package.values(), key=lambda item: item.package_name)

    @classmethod
    def format_missing_dependency_message(cls, dependencies):
        packages = ", ".join(dependency.package_name for dependency in dependencies)
        return (
            f"Missing parser package(s): {packages}. "
            "Run `poetry install` from the project directory so all advertised "
            "document formats are available."
        )

    @classmethod
    def dependency_status_message(cls):
        missing_dependencies = cls.missing_runtime_dependencies()
        if not missing_dependencies:
            return ""
        return cls.format_missing_dependency_message(missing_dependencies)

    def scrape_file(self, file_path):
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix not in self.FORMAT_DEPENDENCIES:
            raise ValueError(f"Unsupported document type: {suffix or '[none]'}")

        missing_dependencies = self.missing_dependencies_for_suffix(suffix)
        if missing_dependencies:
            raise RuntimeError(
                self.format_missing_dependency_message(missing_dependencies)
            )

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
        elif suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}:
            rows = self._scrape_image(path)
        return [
            self._row_to_dict(row, path)
            for row in rows
            if self._has_content(row)
        ]

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
        return bool(
            (row.primary_text or "").strip()
            or (row.secondary_text or "").strip()
        )

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
        needs_ocr = False
        for index, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                needs_ocr = True
            rows.append(DocumentRow(index, f"Page {index}", page_text))

        if needs_ocr:
            ocr_rows = self._perform_ocr_on_pdf(path)
            if ocr_rows:
                merged_rows = []
                for row_index, row in enumerate(rows, start=1):
                    ocr_row = ocr_rows[row_index - 1] if row_index - 1 < len(ocr_rows) else None
                    if row.primary_text.strip():
                        merged_rows.append(row)
                    elif ocr_row and self._has_content(ocr_row):
                        merged_rows.append(
                            DocumentRow(
                                row.item_number,
                                row.title,
                                ocr_row.primary_text,
                                ocr_row.secondary_text,
                            )
                        )
                    else:
                        merged_rows.append(row)
                rows = merged_rows
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
            if hasattr(item, "is_chapter") and not item.is_chapter():
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

    def _scrape_image(self, path):
        ocr_text = self._perform_ocr_on_image(path)
        return [DocumentRow(1, path.stem or "Image 1", ocr_text)]

    def _perform_ocr_on_pdf(self, path):
        try:
            import pypdfium2 as pdfium
        except ImportError as error:
            raise ValueError(
                "OCR support for scanned PDFs requires the 'pypdfium2' package."
            ) from error

        document = pdfium.PdfDocument(str(path))
        rows = []
        for index in range(len(document)):
            page = document[index]
            bitmap = page.render(scale=2).to_pil()
            page_text = self._ocr_image_object(bitmap)
            rows.append(DocumentRow(index + 1, f"Page {index + 1}", page_text))
        return rows

    def _perform_ocr_on_image(self, path):
        try:
            from PIL import Image
        except ImportError as error:
            raise ValueError(
                "OCR support for image files requires the 'Pillow' package."
            ) from error

        with Image.open(path) as image:
            return self._ocr_image_object(image)

    def _ocr_image_object(self, image):
        try:
            import pytesseract
        except ImportError as error:
            raise ValueError(
                "OCR support requires the 'pytesseract' package and a Tesseract installation."
            ) from error

        return pytesseract.image_to_string(image).strip()
