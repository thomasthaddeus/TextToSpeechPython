from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtWidgets import QTableWidgetItem

from app.controller.background_workers import DocumentParseWorker
from app.model.scraper.document_scraper import DocumentScraper
from app.utils.text_cleaner import TextCleaner
from loguru import logger


class SecondController(QObject):
    CONTENT_MODES = {
        "prefer_secondary": {
            "primary_label": "Main Text",
            "secondary_label": "Context",
            "label": "Prefer Context When Available",
        },
        "secondary_only": {
            "primary_label": "Main Text",
            "secondary_label": "Context",
            "label": "Context Only",
        },
        "primary_only": {
            "primary_label": "Main Text",
            "secondary_label": "Context",
            "label": "Main Text Only",
        },
        "combine": {
            "primary_label": "Main Text",
            "secondary_label": "Context",
            "label": "Combine Main Text and Context",
        },
    }
    FORMAT_PROFILES = {
        "pptx": {
            "primary_label": "Slide Text",
            "secondary_label": "Speaker Notes",
            "modes": [
                ("prefer_secondary", "Prefer Speaker Notes"),
                ("secondary_only", "Speaker Notes Only"),
                ("primary_only", "Slide Text Only"),
                ("combine", "Combine Slide Text and Speaker Notes"),
            ],
            "help": "Select slides and choose whether to import slide text, speaker notes, or both:",
        },
        "pdf": {
            "primary_label": "Page Text",
            "secondary_label": "Page Context",
            "modes": [
                ("primary_only", "Page Text Only"),
                ("combine", "Include Page Context"),
            ],
            "help": "Select pages and choose what page content to import or batch export:",
        },
        "docx": {
            "primary_label": "Body / Section Text",
            "secondary_label": "Structure Context",
            "modes": [
                ("primary_only", "Body Text Only"),
                ("combine", "Include Structure Context"),
            ],
            "help": "Select document sections and choose what body content to import or batch export:",
        },
        "html": {
            "primary_label": "Section Text",
            "secondary_label": "HTML Context",
            "modes": [
                ("primary_only", "Section Text Only"),
                ("combine", "Include HTML Context"),
            ],
            "help": "Select HTML sections and choose what content to import or batch export:",
        },
        "htm": {
            "primary_label": "Section Text",
            "secondary_label": "HTML Context",
            "modes": [
                ("primary_only", "Section Text Only"),
                ("combine", "Include HTML Context"),
            ],
            "help": "Select HTML sections and choose what content to import or batch export:",
        },
        "epub": {
            "primary_label": "Chapter Text",
            "secondary_label": "Chapter Context",
            "modes": [
                ("primary_only", "Chapter Text Only"),
                ("combine", "Include Chapter Context"),
            ],
            "help": "Select chapters and choose what chapter content to import or batch export:",
        },
        "csv": {
            "primary_label": "Row Text",
            "secondary_label": "Sheet / Column Context",
            "modes": [
                ("primary_only", "Row Text Only"),
                ("combine", "Include Column Context"),
            ],
            "help": "Select rows and choose whether to include column context:",
        },
        "xlsx": {
            "primary_label": "Row Text",
            "secondary_label": "Sheet / Column Context",
            "modes": [
                ("primary_only", "Row Text Only"),
                ("combine", "Include Sheet and Column Context"),
            ],
            "help": "Select spreadsheet rows and choose whether to include sheet/column context:",
        },
        "xls": {
            "primary_label": "Row Text",
            "secondary_label": "Sheet / Column Context",
            "modes": [
                ("primary_only", "Row Text Only"),
                ("combine", "Include Sheet and Column Context"),
            ],
            "help": "Select spreadsheet rows and choose whether to include sheet/column context:",
        },
        "rtf": {
            "primary_label": "Rich Text",
            "secondary_label": "Context",
            "modes": [
                ("primary_only", "Rich Text Only"),
                ("combine", "Include Context"),
            ],
            "help": "Select rich text blocks and choose what content to import or batch export:",
        },
        "txt": {
            "primary_label": "Text Block",
            "secondary_label": "Context",
            "modes": [
                ("primary_only", "Text Block Only"),
                ("combine", "Include Context"),
            ],
            "help": "Select text blocks and choose what content to import or batch export:",
        },
        "image": {
            "primary_label": "OCR Text",
            "secondary_label": "OCR Context",
            "modes": [
                ("primary_only", "OCR Text Only"),
                ("combine", "Include OCR Context"),
            ],
            "help": "Select OCR rows and choose what text to import or batch export:",
        },
    }
    IMAGE_TYPES = {"png", "jpg", "jpeg", "tif", "tiff", "bmp", "webp"}

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.scraper = DocumentScraper()
        self.import_rows = []
        self.load_thread = None
        self.load_worker = None
        self.current_mode_map = {}
        self.text_cleaner = TextCleaner()
        self._updating_table = False
        self.view.browseButton.clicked.connect(self.choose_file)
        self.view.loadButton.clicked.connect(self.load_file)
        self.view.cancelLoadButton.clicked.connect(self.cancel_load)
        self.view.importButton.clicked.connect(self.import_text)
        self.view.batchExportButton.clicked.connect(self.batch_export)
        self.view.selectAllButton.clicked.connect(self.view.previewTable.selectAll)
        self.view.clearSelectionButton.clicked.connect(
            self.view.previewTable.clearSelection
        )
        self.view.cleanSelectedButton.clicked.connect(self.clean_selected_rows)
        self.view.splitSelectedButton.clicked.connect(self.split_selected_rows)
        self.view.mergeSelectedButton.clicked.connect(self.merge_selected_rows)
        self.view.duplicateSelectedButton.clicked.connect(
            self.duplicate_selected_rows
        )
        self.view.deleteSelectedButton.clicked.connect(self.delete_selected_rows)
        self.view.restoreSelectedButton.clicked.connect(self.restore_selected_rows)
        self.view.previewTable.itemChanged.connect(self._handle_preview_item_changed)
        self.view.closeButton.clicked.connect(self.view.close)
        self._apply_format_profile(None)
        self._surface_document_dependency_status()

    def _normalize_row(self, row):
        normalized = dict(row)
        normalized["title"] = str(normalized.get("title", ""))
        normalized["primary_text"] = str(normalized.get("primary_text", ""))
        normalized["secondary_text"] = str(normalized.get("secondary_text", ""))
        normalized.setdefault("original_title", normalized["title"])
        normalized.setdefault("original_primary_text", normalized["primary_text"])
        normalized.setdefault("original_secondary_text", normalized["secondary_text"])
        return normalized

    def _sync_rows_from_table(self):
        if self._updating_table:
            return
        for row_index, row in enumerate(self.import_rows):
            if row_index >= self.view.previewTable.rowCount():
                break
            for column_index, field_name in (
                (0, "title"),
                (1, "primary_text"),
                (2, "secondary_text"),
            ):
                item = self.view.previewTable.item(row_index, column_index)
                if item is not None:
                    row[field_name] = item.text()

    def _handle_preview_item_changed(self, item):
        if self._updating_table:
            return
        if item is None:
            return
        row_index = item.row()
        if not 0 <= row_index < len(self.import_rows):
            return
        field_name = {0: "title", 1: "primary_text", 2: "secondary_text"}.get(
            item.column()
        )
        if field_name:
            self.import_rows[row_index][field_name] = item.text()

    def _selected_row_indexes(self):
        return sorted(
            {index.row() for index in self.view.previewTable.selectionModel().selectedRows()}
        )

    def _selected_rows(self):
        self._sync_rows_from_table()
        indexes = self.view.previewTable.selectionModel().selectedRows()
        selected = []
        for index in indexes:
            row_data = self.import_rows[index.row()]
            selected.append(dict(row_data))
        return selected

    def _resolve_text_for_row(self, row, content_mode):
        primary_text = (row.get("primary_text") or "").strip()
        secondary_text = (row.get("secondary_text") or "").strip()

        if content_mode == "secondary_only":
            return secondary_text
        if content_mode == "primary_only":
            return primary_text
        if content_mode == "combine":
            parts = [part for part in (primary_text, secondary_text) if part]
            return "\n\n".join(parts)
        return secondary_text or primary_text

    def _build_import_payload(self, selected_rows):
        content_mode = self.current_mode_map[
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
        self._updating_table = True
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
        self._updating_table = False

    def _replace_rows_and_reselect(self, rows, selected_indexes=None):
        self.import_rows = [self._normalize_row(row) for row in rows]
        self._populate_preview_table()
        self.view.previewTable.clearSelection()
        for row_index in selected_indexes or []:
            if 0 <= row_index < self.view.previewTable.rowCount():
                self.view.previewTable.selectRow(row_index)

    def clean_selected_rows(self):
        self._sync_rows_from_table()
        selected_indexes = self._selected_row_indexes()
        if not selected_indexes:
            self.view.infoLabel.setText("Select rows before cleaning them.")
            return
        for row_index in selected_indexes:
            row = self.import_rows[row_index]
            row["primary_text"] = self.text_cleaner.clean_all(row["primary_text"])
            row["secondary_text"] = self.text_cleaner.clean_all(row["secondary_text"])
        self._replace_rows_and_reselect(self.import_rows, selected_indexes)
        self.view.infoLabel.setText(f"Cleaned {len(selected_indexes)} selected row(s).")

    def duplicate_selected_rows(self):
        self._sync_rows_from_table()
        selected_indexes = self._selected_row_indexes()
        if not selected_indexes:
            self.view.infoLabel.setText("Select rows before duplicating them.")
            return
        rows = [dict(row) for row in self.import_rows]
        offset = 0
        new_selection = []
        for row_index in selected_indexes:
            insert_at = row_index + 1 + offset
            duplicate = dict(rows[row_index + offset])
            duplicate["title"] = f'{duplicate.get("title", "Item")} Copy'
            rows.insert(insert_at, duplicate)
            new_selection.append(insert_at)
            offset += 1
        self._replace_rows_and_reselect(rows, new_selection)
        self.view.infoLabel.setText(f"Duplicated {len(new_selection)} row(s).")

    def delete_selected_rows(self):
        self._sync_rows_from_table()
        selected_indexes = self._selected_row_indexes()
        if not selected_indexes:
            self.view.infoLabel.setText("Select rows before deleting them.")
            return
        remaining_rows = [
            row for row_index, row in enumerate(self.import_rows)
            if row_index not in set(selected_indexes)
        ]
        self._replace_rows_and_reselect(remaining_rows)
        self.view.infoLabel.setText(f"Deleted {len(selected_indexes)} selected row(s).")

    def restore_selected_rows(self):
        self._sync_rows_from_table()
        selected_indexes = self._selected_row_indexes()
        if not selected_indexes:
            self.view.infoLabel.setText("Select rows before restoring them.")
            return
        for row_index in selected_indexes:
            row = self.import_rows[row_index]
            row["title"] = row.get("original_title", row.get("title", ""))
            row["primary_text"] = row.get(
                "original_primary_text",
                row.get("primary_text", ""),
            )
            row["secondary_text"] = row.get(
                "original_secondary_text",
                row.get("secondary_text", ""),
            )
        self._replace_rows_and_reselect(self.import_rows, selected_indexes)
        self.view.infoLabel.setText(f"Restored {len(selected_indexes)} row(s).")

    def split_selected_rows(self):
        self._sync_rows_from_table()
        selected_indexes = self._selected_row_indexes()
        if not selected_indexes:
            self.view.infoLabel.setText("Select a row before splitting it.")
            return

        rows = [dict(row) for row in self.import_rows]
        new_selection = []
        offset = 0
        for row_index in selected_indexes:
            active_index = row_index + offset
            row = rows[active_index]
            parts = self._split_text_for_row(row.get("primary_text", ""))
            if len(parts) < 2:
                continue
            row["primary_text"] = parts[0]
            new_row = dict(row)
            new_row["title"] = f'{row.get("title", "Item")} Part 2'
            new_row["primary_text"] = parts[1]
            rows.insert(active_index + 1, new_row)
            new_selection.extend([active_index, active_index + 1])
            offset += 1

        if not new_selection:
            self.view.infoLabel.setText(
                "Selected row text could not be split. Add a blank line or more text first."
            )
            return
        self._replace_rows_and_reselect(rows, new_selection)
        self.view.infoLabel.setText("Split selected row text into separate rows.")

    def _split_text_for_row(self, text):
        normalized = (text or "").strip()
        if "\n\n" in normalized:
            first, rest = normalized.split("\n\n", 1)
            return [first.strip(), rest.strip()]
        sentences = [part.strip() for part in normalized.split(". ") if part.strip()]
        if len(sentences) > 1:
            return [sentences[0] + ".", ". ".join(sentences[1:])]
        words = normalized.split()
        if len(words) < 2:
            return [normalized]
        midpoint = len(words) // 2
        return [" ".join(words[:midpoint]), " ".join(words[midpoint:])]

    def merge_selected_rows(self):
        self._sync_rows_from_table()
        selected_indexes = self._selected_row_indexes()
        if len(selected_indexes) < 2:
            self.view.infoLabel.setText("Select at least two rows before merging.")
            return

        rows = [dict(row) for row in self.import_rows]
        first_index = selected_indexes[0]
        selected_rows = [rows[index] for index in selected_indexes]
        merged_row = dict(selected_rows[0])
        merged_row["title"] = " + ".join(
            row.get("title", f"Item {index + 1}")
            for index, row in zip(selected_indexes, selected_rows)
            if row.get("title")
        ) or selected_rows[0].get("title", "Merged Row")
        merged_row["primary_text"] = "\n\n".join(
            row.get("primary_text", "").strip()
            for row in selected_rows
            if row.get("primary_text", "").strip()
        )
        merged_row["secondary_text"] = "\n\n".join(
            row.get("secondary_text", "").strip()
            for row in selected_rows
            if row.get("secondary_text", "").strip()
        )
        for row_index in reversed(selected_indexes):
            rows.pop(row_index)
        rows.insert(first_index, merged_row)
        self._replace_rows_and_reselect(rows, [first_index])
        self.view.infoLabel.setText(f"Merged {len(selected_indexes)} selected row(s).")

    def _source_type_for_rows(self, rows):
        source_types = {
            str(row.get("source_type", "")).lower()
            for row in rows
            if row.get("source_type")
        }
        if len(source_types) != 1:
            return None

        source_type = next(iter(source_types))
        return "image" if source_type in self.IMAGE_TYPES else source_type

    def _profile_for_source_type(self, source_type):
        return self.FORMAT_PROFILES.get(
            source_type,
            {
                "primary_label": "Main Text",
                "secondary_label": "Context",
                "modes": [
                    ("prefer_secondary", "Prefer Context When Available"),
                    ("secondary_only", "Context Only"),
                    ("primary_only", "Main Text Only"),
                    ("combine", "Combine Main Text and Context"),
                ],
                "help": "Select document rows and choose what to import or batch export:",
            },
        )

    def _apply_format_profile(self, source_type):
        profile = self._profile_for_source_type(source_type)
        self.view.previewTable.setHorizontalHeaderLabels(
            [
                "Item",
                profile["primary_label"],
                profile["secondary_label"],
            ]
        )
        self.view.selectionHelpLabel.setText(profile["help"])
        self.view.contentModeComboBox.clear()
        self.current_mode_map = {}
        for mode_value, mode_label in profile["modes"]:
            self.view.contentModeComboBox.addItem(mode_label)
            self.current_mode_map[mode_label] = mode_value

    def _set_loading_state(self, is_loading):
        for button_name in (
            "browseButton",
            "loadButton",
            "importButton",
            "batchExportButton",
            "selectAllButton",
            "clearSelectionButton",
            "cleanSelectedButton",
            "splitSelectedButton",
            "mergeSelectedButton",
            "duplicateSelectedButton",
            "deleteSelectedButton",
            "restoreSelectedButton",
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
        self.import_rows = [self._normalize_row(row) for row in extracted_rows]
        self._apply_format_profile(self._source_type_for_rows(extracted_rows))
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
