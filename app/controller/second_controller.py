from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtWidgets import QTableWidgetItem

from app.controller.background_workers import DocumentParseWorker
from app.model.scraper.document_scraper import DocumentScraper
from loguru import logger


class SecondController(QObject):
    CONTENT_MODE_MAP = {
        "Prefer Secondary Text": "prefer_notes",
        "Secondary Text Only": "notes_only",
        "Primary Text Only": "slide_text_only",
        "Combine Slide Text and Notes": "combine",
        "Combine Primary and Secondary Text": "combine",
    }

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.scraper = DocumentScraper()
        self.import_rows = []
        self.load_thread = None
        self.load_worker = None
        self.view.browseButton.clicked.connect(self.choose_file)
        self.view.loadButton.clicked.connect(self.load_file)
        self.view.cancelLoadButton.clicked.connect(self.cancel_load)
        self.view.importButton.clicked.connect(self.import_text)
        self.view.batchExportButton.clicked.connect(self.batch_export)
        self.view.selectAllButton.clicked.connect(self.view.previewTable.selectAll)
        self.view.clearSelectionButton.clicked.connect(
            self.view.previewTable.clearSelection
        )
        self.view.closeButton.clicked.connect(self.view.close)
        self._surface_document_dependency_status()

    def _selected_rows(self):
        indexes = self.view.previewTable.selectionModel().selectedRows()
        selected = []
        for index in indexes:
            row_data = self.import_rows[index.row()]
            selected.append(dict(row_data))
        return selected

    def _resolve_text_for_row(self, row, content_mode):
        primary_text = (row.get("primary_text") or "").strip()
        secondary_text = (row.get("secondary_text") or "").strip()

        if content_mode == "notes_only":
            return secondary_text
        if content_mode == "slide_text_only":
            return primary_text
        if content_mode == "combine":
            parts = [part for part in (primary_text, secondary_text) if part]
            return "\n\n".join(parts)
        return secondary_text or primary_text

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
            item_label = row.get("title") or f'Item {row["item_number"]}'
            item_cell = QTableWidgetItem(item_label)
            item_cell.setData(Qt.ItemDataRole.UserRole, row)
            primary_cell = QTableWidgetItem(row["primary_text"] or "[empty]")
            secondary_cell = QTableWidgetItem(row["secondary_text"] or "[empty]")
            self.view.previewTable.setItem(row_index, 0, item_cell)
            self.view.previewTable.setItem(row_index, 1, primary_cell)
            self.view.previewTable.setItem(row_index, 2, secondary_cell)

        self.view.previewTable.resizeColumnsToContents()

    def _set_loading_state(self, is_loading):
        for button_name in (
            "browseButton",
            "loadButton",
            "importButton",
            "batchExportButton",
            "selectAllButton",
            "clearSelectionButton",
        ):
            getattr(self.view, button_name).setEnabled(not is_loading)
        self.view.cancelLoadButton.setEnabled(is_loading)

        if is_loading:
            self.view.infoLabel.setText(
                "Loading document in the background. You can cancel this load if needed."
            )

    def _surface_document_dependency_status(self):
        dependency_message = self.scraper.dependency_status_message()
        if not dependency_message:
            return

        logger.warning("Document parser dependency check: {}", dependency_message)
        self.view.infoLabel.setText(
            "Some import formats are unavailable. Run `poetry install` to install all parser dependencies."
        )

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Choose Document File",
            str(Path.cwd()),
            self.scraper.SUPPORTED_FILTER,
        )
        if file_path:
            self.view.filePathEdit.setText(file_path)
            logger.info("Selected document file {}", file_path)

    def load_file(self):
        if self.load_thread is not None:
            self.view.infoLabel.setText("A document is already loading.")
            return

        file_path = self.view.filePathEdit.text().strip()
        if not file_path:
            QMessageBox.warning(
                self.view,
                "Missing File",
                "Choose a document file before loading.",
            )
            return

        self._set_loading_state(True)
        self.load_thread = QThread(self.view)
        self.load_worker = DocumentParseWorker(file_path)
        self.load_worker.moveToThread(self.load_thread)
        self.load_thread.started.connect(self.load_worker.run)
        self.load_worker.finished.connect(self._handle_load_finished)
        self.load_worker.failed.connect(self._handle_load_failed)
        self.load_worker.cancelled.connect(self._handle_load_cancelled)
        self.load_worker.finished.connect(self.load_thread.quit)
        self.load_worker.failed.connect(self.load_thread.quit)
        self.load_worker.cancelled.connect(self.load_thread.quit)
        self.load_worker.finished.connect(self.load_worker.deleteLater)
        self.load_worker.failed.connect(self.load_worker.deleteLater)
        self.load_worker.cancelled.connect(self.load_worker.deleteLater)
        self.load_thread.finished.connect(self.load_thread.deleteLater)
        self.load_thread.finished.connect(self._clear_load_worker)
        self.load_thread.start()
        logger.info("Started background import for document file {}", file_path)

    def cancel_load(self):
        if self.load_worker is None:
            return

        self.load_worker.request_cancel()
        self.view.cancelLoadButton.setEnabled(False)
        self.view.infoLabel.setText(
            "Cancel requested. The current parser step will stop when safe."
        )
        logger.info("Requested cancellation for document import.")

    def _handle_load_finished(self, extracted_rows):
        self.import_rows = extracted_rows
        self._populate_preview_table()
        if self.import_rows:
            self.view.previewTable.selectAll()
        self.view.infoLabel.setText(
            f"Loaded {len(extracted_rows)} document section(s)."
        )
        logger.info(
            "Loaded document import preview with {} rows.",
            len(extracted_rows),
        )

    def _handle_load_failed(self, message):
        logger.error("Failed to import document file: {}", message)
        self.view.infoLabel.setText("Document import failed.")
        QMessageBox.critical(
            self.view,
            "Import Error",
            f"Unable to read the selected document.\n\n{message}",
        )

    def _handle_load_cancelled(self):
        self.view.infoLabel.setText("Document import canceled.")
        logger.info("Document import canceled.")

    def _clear_load_worker(self):
        self.load_thread = None
        self.load_worker = None
        self._set_loading_state(False)

    def import_text(self):
        selected_rows = self._selected_rows()
        if not selected_rows:
            QMessageBox.information(
                self.view,
                "Nothing To Import",
                "Load a document file and select at least one row.",
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
            "Imported {} document rows into the main window.",
            len(payload_rows),
        )

    def batch_export(self):
        selected_rows = self._selected_rows()
        if not selected_rows:
            QMessageBox.information(
                self.view,
                "Nothing To Export",
                "Load a document file and select at least one row.",
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
            "Requested batch export for {} document rows.",
            len(payload_rows),
        )
