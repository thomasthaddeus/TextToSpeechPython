from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from app.model.scraper.pptx_scraper import PPTXScraper
from loguru import logger


class SecondController:
    def __init__(self, view):
        self.view = view
        self.scraper = PPTXScraper()
        self.imported_text = ""
        self.view.browseButton.clicked.connect(self.choose_file)
        self.view.loadButton.clicked.connect(self.load_file)
        self.view.importButton.clicked.connect(self.import_text)
        self.view.closeButton.clicked.connect(self.view.close)

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Choose PowerPoint File",
            str(Path.cwd()),
            "PowerPoint Files (*.pptx)",
        )
        if file_path:
            self.view.filePathEdit.setText(file_path)
            logger.info("Selected PPTX file {}", file_path)

    def load_file(self):
        file_path = self.view.filePathEdit.text().strip()
        if not file_path:
            QMessageBox.warning(
                self.view,
                "Missing File",
                "Choose a PowerPoint file before loading.",
            )
            return

        try:
            extracted_rows = self.scraper.scrape_pptx(file_path)
        except Exception as error:
            logger.exception("Failed to import PowerPoint file: {}", error)
            QMessageBox.critical(
                self.view,
                "Import Error",
                f"Unable to read the PowerPoint file.\n\n{error}",
            )
            return

        preview_chunks = []
        for slide_number, slide_text, notes_text in extracted_rows:
            preview_chunks.append(
                f"Slide {slide_number}\n"
                f"Slide Text: {slide_text or '[empty]'}\n"
                f"Notes: {notes_text or '[empty]'}"
            )

        self.imported_text = "\n\n".join(
            row[2] or row[1] for row in extracted_rows if row[1] or row[2]
        )
        self.view.previewTextEdit.setPlainText("\n\n---\n\n".join(preview_chunks))
        logger.info(
            "Loaded PowerPoint import preview with {} slides.",
            len(extracted_rows),
        )

    def import_text(self):
        if not self.imported_text.strip():
            QMessageBox.information(
                self.view,
                "Nothing To Import",
                "Load a PowerPoint file first.",
            )
            return

        self.view.textImported.emit(self.imported_text)
        self.view.accept()
        logger.info("Imported PowerPoint text into the main window.")
