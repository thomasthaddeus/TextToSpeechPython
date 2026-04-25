import shutil
import unittest
from pathlib import Path

from app.model.scraper.document_scraper import DocumentScraper


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

        self.assertGreaterEqual(len(rows), 2)
        self.assertEqual(rows[0]["source_type"], "html")
        self.assertIn("Heading", rows[0]["primary_text"])


if __name__ == "__main__":
    unittest.main()
