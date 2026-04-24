from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtWidgets import QTableWidgetItem

from app.model.scraper.pptx_scraper import PPTXScraper
from loguru import logger


class SecondController:
    CONTENT_MODE_MAP = {
        "Prefer Notes": "prefer_notes",
        "Notes Only": "notes_only",
        "Slide Text Only": "slide_text_only",
        "Combine Slide Text and Notes": "combine",
    }

    def __init__(self, view):
        self.view = view
        self.scraper = PPTXScraper()
        self.import_rows = []
        self.view.browseButton.clicked.connect(self.choose_file)
        self.view.loadButton.clicked.connect(self.load_file)
        self.view.importButton.clicked.connect(self.import_text)
        self.view.batchExportButton.clicked.connect(self.batch_export)
        self.view.selectAllButton.clicked.connect(self.view.previewTable.selectAll)
        self.view.clearSelectionButton.clicked.connect(
            self.view.previewTable.clearSelection
        )
        self.view.closeButton.clicked.connect(self.view.close)

    def _selected_rows(self):
        indexes = self.view.previewTable.selectionModel().selectedRows()
        selected = []
        for index in indexes:
            row_data = self.import_rows[index.row()]
            selected.append(dict(row_data))
        return selected

    def _resolve_text_for_row(self, row, content_mode):
        slide_text = (row.get("slide_text") or "").strip()
        notes_text = (row.get("notes_text") or "").strip()

        if content_mode == "notes_only":
            return notes_text
        if content_mode == "slide_text_only":
            return slide_text
        if content_mode == "combine":
            parts = [part for part in (slide_text, notes_text) if part]
            return "\n\n".join(parts)
        return notes_text or slide_text

    def _build_import_payload(self, selected_rows):
        content_mode = self.CONTENT_MODE_MAP[
            self.view.contentModeComboBox.currentText()
        ]
        payload_rows = []
        text_chunks = []

        for row in selected_rows:
            resolved_text = self._resolve_text_for_row(row, content_mode)
            if not resolved_text:
                continue

            payload_row = dict(row)
            payload_row["content_mode"] = content_mode
            payload_row["resolved_text"] = resolved_text
            payload_rows.append(payload_row)
            text_chunks.append(resolved_text)

        return payload_rows, "\n\n".join(text_chunks)

    def _populate_preview_table(self):
        self.view.previewTable.setRowCount(len(self.import_rows))
        for row_index, row in enumerate(self.import_rows):
            slide_item = QTableWidgetItem(str(row["slide_number"]))
            slide_item.setData(Qt.ItemDataRole.UserRole, row)
            slide_text_item = QTableWidgetItem(row["slide_text"] or "[empty]")
            notes_item = QTableWidgetItem(row["notes_text"] or "[empty]")
            self.view.previewTable.setItem(row_index, 0, slide_item)
            self.view.previewTable.setItem(row_index, 1, slide_text_item)
            self.view.previewTable.setItem(row_index, 2, notes_item)

        self.view.previewTable.resizeColumnsToContents()

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

        self.import_rows = [
            {
                "slide_number": slide_number,
                "slide_text": slide_text,
                "notes_text": notes_text,
            }
            for slide_number, slide_text, notes_text in extracted_rows
        ]
        self._populate_preview_table()
        if self.import_rows:
            self.view.previewTable.selectAll()
        logger.info(
            "Loaded PowerPoint import preview with {} slides.",
            len(extracted_rows),
        )

    def import_text(self):
        selected_rows = self._selected_rows()
        if not selected_rows:
            QMessageBox.information(
                self.view,
                "Nothing To Import",
                "Load a PowerPoint file and select at least one slide row.",
            )
            return

        payload_rows, imported_text = self._build_import_payload(selected_rows)
        if not imported_text.strip():
            QMessageBox.information(
                self.view,
                "No Content",
                "The selected rows do not contain content for the chosen mode.",
            )
            return

        self.view.textImported.emit(imported_text)
        self.view.accept()
        logger.info(
            "Imported {} PowerPoint rows into the main window.",
            len(payload_rows),
        )

    def batch_export(self):
        selected_rows = self._selected_rows()
        if not selected_rows:
            QMessageBox.information(
                self.view,
                "Nothing To Export",
                "Load a PowerPoint file and select at least one slide row.",
            )
            return

        payload_rows, _ = self._build_import_payload(selected_rows)
        if not payload_rows:
            QMessageBox.information(
                self.view,
                "No Content",
                "The selected rows do not contain content for the chosen mode.",
            )
            return

        self.view.batchRequested.emit(payload_rows)
        logger.info(
            "Requested batch export for {} PowerPoint rows.",
            len(payload_rows),
        )
