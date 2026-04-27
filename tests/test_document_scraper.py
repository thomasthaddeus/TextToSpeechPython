import shutil
import unittest
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from docx import Document
from pptx import Presentation
from PIL import Image
from pypdf import PdfWriter

from app.model.scraper.document_scraper import DocumentRow, DocumentScraper


HAS_EBOOKLIB = importlib.util.find_spec("ebooklib") is not None
HAS_OPENPYXL = importlib.util.find_spec("openpyxl") is not None
HAS_STRIPRTF = importlib.util.find_spec("striprtf") is not None


def build_pdf_bytes(text):
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            b"<< /Length %d >>\nstream\nBT\n/F1 18 Tf\n50 100 Td\n(%s) Tj\nET\nendstream"
            % (
                len(
                    f"BT\n/F1 18 Tf\n50 100 Td\n({text}) Tj\nET\n".encode(
                        "utf-8"
                    )
                ),
                text.encode("utf-8"),
            )
        ),
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("utf-8"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("utf-8"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("utf-8"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("utf-8")
    )
    return bytes(pdf)


class DocumentScraperTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path("data/dynamic/tmp/document_scraper_tests")
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.scraper = DocumentScraper()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scrape_txt_splits_into_document_rows(self):
        text_path = self.temp_dir / "sample.txt"
        text_path.write_text(
            "First block.\n\nSecond block.",
            encoding="utf-8",
        )

        rows = self.scraper.scrape_file(text_path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["title"], "Text Block 1")
        self.assertEqual(rows[0]["primary_text"], "First block.")
        self.assertEqual(rows[1]["primary_text"], "Second block.")
        self.assertEqual(rows[0]["source_type"], "txt")
        self.assertEqual(rows[0]["metadata"], {})

    def test_dependency_status_reports_missing_advertised_parser_packages(self):
        missing_modules = {"ebooklib", "striprtf", "xlrd"}

        def fake_find_spec(module_name):
            return None if module_name in missing_modules else object()

        with patch(
            "app.model.scraper.document_scraper.importlib.util.find_spec",
            side_effect=fake_find_spec,
        ):
            missing_dependencies = DocumentScraper.missing_runtime_dependencies()

        missing_packages = {
            dependency.package_name for dependency in missing_dependencies
        }
        self.assertIn("ebooklib", missing_packages)
        self.assertIn("striprtf", missing_packages)
        self.assertIn("xlrd", missing_packages)

    def test_scrape_file_fails_clearly_when_parser_dependency_is_missing(self):
        rtf_path = self.temp_dir / "sample.rtf"
        rtf_path.write_text(
            r"{\rtf1\ansi Missing dependency sample.}",
            encoding="utf-8",
        )

        def fake_find_spec(module_name):
            return None if module_name == "striprtf" else object()

        with patch(
            "app.model.scraper.document_scraper.importlib.util.find_spec",
            side_effect=fake_find_spec,
        ):
            with self.assertRaisesRegex(RuntimeError, "striprtf"):
                self.scraper.scrape_file(rtf_path)

    def test_xls_imports_require_the_xlrd_reader_package(self):
        missing_dependencies = DocumentScraper.missing_dependencies_for_suffix(".xls")
        package_names = {dependency.package_name for dependency in missing_dependencies}

        if importlib.util.find_spec("xlrd") is None:
            self.assertIn("xlrd", package_names)
        else:
            self.assertNotIn("xlrd", package_names)

    def test_scrape_html_extracts_text_sections(self):
        html_path = self.temp_dir / "sample.html"
        html_path.write_text(
            (
                "<html><head><title>Sample</title></head><body>"
                "<h1>Heading</h1><p>Paragraph one.</p><p>Paragraph two.</p>"
                "</body></html>"
            ),
            encoding="utf-8",
        )

        rows = self.scraper.scrape_file(html_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Heading")
        self.assertEqual(rows[0]["source_type"], "html")
        self.assertIn("Heading", rows[0]["primary_text"])
        self.assertIn("Paragraph two.", rows[0]["primary_text"])
        self.assertEqual(rows[0]["metadata"]["kind"], "html_section")
        self.assertEqual(rows[0]["metadata"]["heading_level"], 1)

    def test_scrape_html_preserves_table_rows(self):
        html_path = self.temp_dir / "table.html"
        html_path.write_text(
            (
                "<html><body>"
                "<table><tr><th>Step</th><th>Status</th></tr>"
                "<tr><td>Import</td><td>Ready</td></tr></table>"
                "</body></html>"
            ),
            encoding="utf-8",
        )

        rows = self.scraper.scrape_file(html_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Table 1 Row 1")
        self.assertIn("Step: Import", rows[0]["primary_text"])
        self.assertEqual(rows[0]["metadata"]["kind"], "table_row")

    def test_scrape_docx_extracts_paragraphs(self):
        docx_path = self.temp_dir / "sample.docx"
        document = Document()
        document.add_paragraph("First paragraph.")
        document.add_paragraph("Second paragraph.")
        document.save(docx_path)

        rows = self.scraper.scrape_file(docx_path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["title"], "Paragraph 1")
        self.assertEqual(rows[1]["primary_text"], "Second paragraph.")
        self.assertEqual(rows[0]["metadata"]["kind"], "paragraph")

    def test_scrape_docx_preserves_headings_and_tables(self):
        docx_path = self.temp_dir / "structured.docx"
        document = Document()
        document.add_heading("Launch Plan", level=1)
        document.add_paragraph("Prepare the narration script.")
        table = document.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Task"
        table.cell(0, 1).text = "Owner"
        table.cell(1, 0).text = "Record intro"
        table.cell(1, 1).text = "Narrator"
        document.save(docx_path)

        rows = self.scraper.scrape_file(docx_path)

        self.assertEqual(rows[0]["title"], "Launch Plan")
        self.assertIn("Prepare the narration script.", rows[0]["primary_text"])
        self.assertEqual(rows[0]["metadata"]["kind"], "section")
        self.assertEqual(rows[0]["metadata"]["heading_level"], 1)
        self.assertEqual(rows[1]["title"], "Table 1 Row 1")
        self.assertIn("Task: Record intro", rows[1]["primary_text"])
        self.assertEqual(rows[1]["metadata"]["kind"], "table_row")

    def test_scrape_pdf_extracts_page_text(self):
        pdf_path = self.temp_dir / "sample.pdf"
        pdf_path.write_bytes(build_pdf_bytes("Hello PDF"))

        rows = self.scraper.scrape_file(pdf_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Page 1")
        self.assertIn("Hello PDF", rows[0]["primary_text"])
        self.assertEqual(rows[0]["metadata"]["kind"], "page")
        self.assertEqual(rows[0]["metadata"]["extraction"], "text-layer")

    @unittest.skipUnless(HAS_STRIPRTF, "striprtf is not installed")
    def test_scrape_rtf_extracts_text(self):
        rtf_path = self.temp_dir / "sample.rtf"
        rtf_path.write_text(
            r"{\rtf1\ansi This is {\b bold} text.}",
            encoding="utf-8",
        )

        rows = self.scraper.scrape_file(rtf_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "RTF Block 1")
        self.assertIn("This is bold text.", rows[0]["primary_text"])

    @unittest.skipUnless(HAS_EBOOKLIB, "ebooklib is not installed")
    def test_scrape_epub_extracts_chapter_text(self):
        from ebooklib import epub

        epub_path = self.temp_dir / "sample.epub"
        book = epub.EpubBook()
        book.set_identifier("sample-book")
        book.set_title("Sample Book")
        book.set_language("en")
        chapter = epub.EpubHtml(title="Chapter 1", file_name="chapter1.xhtml", lang="en")
        chapter.content = "<html><head><title>Chapter 1</title></head><body><p>EPUB body text.</p></body></html>"
        book.add_item(chapter)
        book.toc = (chapter,)
        book.spine = ["nav", chapter]
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        epub.write_epub(str(epub_path), book)

        rows = self.scraper.scrape_file(epub_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Chapter 1")
        self.assertIn("EPUB body text.", rows[0]["primary_text"])
        self.assertEqual(rows[0]["metadata"]["kind"], "chapter")
        self.assertEqual(rows[0]["metadata"]["chapter_number"], 1)

    def test_scrape_csv_extracts_rows(self):
        csv_path = self.temp_dir / "sample.csv"
        pd.DataFrame(
            [{"Name": "Alice", "Role": "Narrator"}, {"Name": "Bob", "Role": "Editor"}]
        ).to_csv(csv_path, index=False)

        rows = self.scraper.scrape_file(csv_path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["title"], "Sheet1 Row 1")
        self.assertIn("Name: Alice", rows[0]["primary_text"])
        self.assertIn("Columns: Name, Role", rows[0]["secondary_text"])
        self.assertEqual(rows[0]["metadata"]["kind"], "sheet_row")
        self.assertEqual(rows[0]["metadata"]["sheet_name"], "Sheet1")

    @unittest.skipUnless(HAS_OPENPYXL, "openpyxl is not installed")
    def test_scrape_xlsx_extracts_rows(self):
        xlsx_path = self.temp_dir / "sample.xlsx"
        with pd.ExcelWriter(xlsx_path) as writer:
            pd.DataFrame([{"Chapter": "Intro", "Pages": 2}]).to_excel(
                writer,
                sheet_name="Outline",
                index=False,
            )

        rows = self.scraper.scrape_file(xlsx_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Outline Row 1")
        self.assertIn("Chapter: Intro", rows[0]["primary_text"])
        self.assertEqual(rows[0]["metadata"]["columns"], ["Chapter", "Pages"])

    def test_scrape_pptx_extracts_slide_text_and_notes(self):
        pptx_path = self.temp_dir / "sample.pptx"
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[1])
        slide.shapes.title.text = "Slide Heading"
        slide.placeholders[1].text = "Slide body text."
        notes_frame = slide.notes_slide.notes_text_frame
        notes_frame.text = "Speaker notes."
        presentation.save(pptx_path)

        rows = self.scraper.scrape_file(pptx_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Slide 1")
        self.assertIn("Slide Heading", rows[0]["primary_text"])
        self.assertIn("Speaker notes.", rows[0]["secondary_text"])
        self.assertEqual(rows[0]["metadata"]["kind"], "slide")
        self.assertTrue(rows[0]["metadata"]["has_notes"])

    def test_scrape_image_uses_ocr_path(self):
        image_path = self.temp_dir / "sample.png"
        Image.new("RGB", (40, 20), color="white").save(image_path)

        with patch(
            "app.model.scraper.document_scraper.importlib.util.find_spec",
            return_value=object(),
        ), patch.object(
            DocumentScraper,
            "_perform_ocr_on_image",
            return_value="Scanned image text",
        ) as mocked_ocr:
            rows = self.scraper.scrape_file(image_path)

        mocked_ocr.assert_called_once()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "sample")
        self.assertEqual(rows[0]["primary_text"], "Scanned image text")
        self.assertEqual(rows[0]["source_type"], "png")
        self.assertEqual(rows[0]["metadata"]["extraction"], "ocr")

    def test_scrape_pdf_falls_back_to_ocr_when_text_layer_is_missing(self):
        pdf_path = self.temp_dir / "scanned.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(pdf_path, "wb") as file:
            writer.write(file)

        with patch.object(
            DocumentScraper,
            "_perform_ocr_on_pdf",
            return_value=[DocumentRow(1, "Page 1", "OCR page text")],
        ) as mocked_ocr:
            rows = self.scraper.scrape_file(pdf_path)

        mocked_ocr.assert_called_once()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Page 1")
        self.assertEqual(rows[0]["primary_text"], "OCR page text")
        self.assertEqual(rows[0]["metadata"]["extraction"], "ocr")


if __name__ == "__main__":
    unittest.main()
