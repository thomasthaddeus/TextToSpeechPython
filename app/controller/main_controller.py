import json
from pathlib import Path
import tempfile
from datetime import datetime
from xml.sax.saxutils import escape

from PyQt6.QtCore import QObject, Qt, QThread, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QListWidgetItem,
    QMenu,
    QMessageBox,
)

try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
except ImportError:  # pragma: no cover - optional multimedia backend
    QAudioOutput = None
    QMediaPlayer = None

from app.controller.background_workers import (
    BatchExportWorker,
    DocumentParseWorker,
    build_ssml_document,
    sanitize_batch_name,
)
from app.controller.second_controller import SecondController
from app.controller.settings_controller import SettingsController
from app.gui.second_window import SecondApp
from app.model.api.api_config import get_api_settings
from app.model.app_settings import AppSettings
from app.model.processors.tts_processor import TTSProcessor
from app.model.scraper.document_scraper import DocumentScraper
from app.model.ssml.ssml_config import SSMLConfig
from app.utils.logging_config import configure_logging
from app.utils.text_cleaner import TextCleaner
from loguru import logger


class MainController(QObject):
    SETTINGS_PATH = Path("data/dynamic/app_settings.json")
    AUDIO_HISTORY_PATH = Path("data/dynamic/audio_history.json")
    MAX_HISTORY_ITEMS = 10
    HISTORY_SETTINGS_FIELDS = (
        "voice",
        "speaking_rate",
        "synthesis_volume",
        "emphasis_level",
        "pitch",
        "pitch_range",
        "pause_duration",
        "pause_position",
        "auto_clean_text",
        "output_dir",
    )

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.cleaner = TextCleaner()
        self.settings = AppSettings.load(self.SETTINGS_PATH)
        self.voice_config = SSMLConfig()
        self.document_scraper = DocumentScraper()
        self.tts_processor = None
        self.settings_controller = SettingsController(self.view)
        self.second_window = None
        self.second_controller = None
        self.latest_audio_path = None
        self.preview_audio_path = None
        self.playing_history_audio_path = None
        self.audio_output = None
        self.media_player = None
        self.document_parse_thread = None
        self.document_parse_worker = None
        self.document_parse_path = None
        self.batch_export_thread = None
        self.batch_export_worker = None
        self.batch_export_active = False
        self._updating_ui_state = False
        self.audio_history = self._load_audio_history()
        self._setup_media_backend()
        self._connect_signals()
        self._refresh_ui_state()
        self._refresh_history_panel()
        self.update_ssml_preview()
        self._surface_document_dependency_status()
        logger.info("Main controller initialized.")

    def _setup_media_backend(self):
        if QMediaPlayer is None or QAudioOutput is None:
            return

        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(self.settings.playback_volume / 100)

    def _connect_signals(self):
        self.view.openSecondWindowButton.clicked.connect(self.open_second_window)
        self.view.openSettingsButton.clicked.connect(self.open_settings)
        self.view.previewButton.clicked.connect(self.update_ssml_preview)
        self.view.cleanTextButton.clicked.connect(self.clean_text)
        self.view.playButton.clicked.connect(self.generate_and_play_audio)
        self.view.generateButton.clicked.connect(self.export_audio_file)
        self.view.stopButton.clicked.connect(self.stop_audio)
        self.view.cancelTaskButton.clicked.connect(self.cancel_background_work)
        self.view.playbackVolumeSlider.valueChanged.connect(
            self.update_playback_volume
        )
        self.view.actionOpenText.triggered.connect(self.open_document_file)
        self.view.actionOpenUrl.triggered.connect(self.open_url_source)
        self.view.actionOpenRawHtml.triggered.connect(self.open_raw_html_source)
        self.view.actionExportEditorText.triggered.connect(self.export_editor_text)
        self.view.actionExportAudio.triggered.connect(self.export_audio_file)
        self.view.actionExit.triggered.connect(self.view.close)
        self.view.actionSettings.triggered.connect(self.open_settings)
        self.view.actionOpenScraper.triggered.connect(self.open_second_window)
        self.view.actionAbout.triggered.connect(self.show_about)
        self.view.textEdit.textChanged.connect(self._handle_editor_text_changed)
        self.view.historyList.itemDoubleClicked.connect(
            self.play_selected_history_audio
        )
        self.view.historyList.customContextMenuRequested.connect(
            self.show_history_context_menu
        )

    def _sanitize_batch_name(self, value):
        return sanitize_batch_name(value)

    def _refresh_ui_state(self):
        self._updating_ui_state = True
        self.view.voiceSummaryLabel.setText(f"Voice: {self.settings.voice}")
        self.view.rateSummaryLabel.setText(
            f"Rate: {self.settings.speaking_rate}"
        )
        self.view.volumeSummaryLabel.setText(
            f"Speech Volume: {self.settings.synthesis_volume}"
        )
        self.view.outputSummaryLabel.setText(
            f"Output: {self.settings.output_dir}"
        )
        self.view.playbackVolumeSlider.setValue(self.settings.playback_volume)
        self.view.playbackVolumeValueLabel.setText(
            f"{self.settings.playback_volume}%"
        )
        self._refresh_action_states()
        azure_key, azure_region = self._resolve_azure_credentials()
        if azure_key and azure_region:
            self.view.statusbar.showMessage("Ready")
        else:
            self.view.statusbar.showMessage(
                "Ready, but Azure Speech is not configured."
            )
        self._updating_ui_state = False

    def _surface_document_dependency_status(self):
        dependency_message = self.document_scraper.dependency_status_message()
        if not dependency_message:
            return

        logger.warning("Document parser dependency check: {}", dependency_message)
        self.view.statusbar.showMessage(
            "Some import formats are unavailable. Run `poetry install` to install all parser dependencies."
        )

    def _current_editor_text(self):
        return self.view.textEdit.toPlainText().strip()

    def _set_inline_hint(self, text):
        self.view.actionHintLabel.setText(text)

    def _refresh_action_states(self):
        has_text = bool(self._current_editor_text())
        multimedia_available = (
            self.media_player is not None and self.audio_output is not None
        )
        has_preview_audio = bool(
            self.preview_audio_path
            or self.__dict__.get("playing_history_audio_path")
        )
        background_work_active = self.__dict__.get("batch_export_active", False) or (
            self.__dict__.get("document_parse_thread") is not None
        )

        self.view.previewButton.setEnabled(has_text)
        self.view.cleanTextButton.setEnabled(has_text)
        self.view.playButton.setEnabled(has_text)
        self.view.generateButton.setEnabled(has_text)
        self.view.actionExportAudio.setEnabled(has_text)
        self.view.stopButton.setEnabled(multimedia_available and has_preview_audio)
        self.view.playbackVolumeSlider.setEnabled(multimedia_available)
        self.view.cancelTaskButton.setEnabled(background_work_active)

        if multimedia_available:
            self.view.playButton.setText("Generate && Play")
            self.view.playButton.setToolTip(
                "Generate speech and play it immediately."
            )
        else:
            self.view.playButton.setText("Generate Preview File")
            self.view.playButton.setToolTip(
                "Generate a preview file. Live playback is unavailable in this environment."
            )

        if background_work_active:
            self.view.previewButton.setEnabled(False)
            self.view.cleanTextButton.setEnabled(False)
            self.view.playButton.setEnabled(False)
            self.view.generateButton.setEnabled(False)
            self.view.actionExportAudio.setEnabled(False)
            self.view.stopButton.setEnabled(False)
            self.view.openSecondWindowButton.setEnabled(False)
            self._set_inline_hint(
                "Background work is running. Use Cancel Task if you need to stop it."
            )
            return

        self.view.openSecondWindowButton.setEnabled(True)

        if not has_text:
            self._set_inline_hint(
                "Type or import text to enable preview and generation actions."
            )
            return

        advanced_chunks = []
        if self.settings.emphasis_level != "none":
            advanced_chunks.append(f"emphasis={self.settings.emphasis_level}")
        if self.settings.pitch != "default":
            advanced_chunks.append(f"pitch={self.settings.pitch}")
        if self.settings.pitch_range != "default":
            advanced_chunks.append(f"range={self.settings.pitch_range}")
        if self.settings.pause_duration != "none":
            advanced_chunks.append(
                f"pause={self.settings.pause_duration} ({self.settings.pause_position})"
            )
        advanced_summary = (
            ", ".join(advanced_chunks)
            if advanced_chunks
            else "default advanced SSML settings"
        )

        if not multimedia_available:
            self._set_inline_hint(
                f"Text is ready and using {advanced_summary}. Preview generation works, but playback controls are disabled because multimedia support is unavailable."
            )
        elif has_preview_audio:
            self._set_inline_hint(
                f"Preview audio is ready. Current SSML uses {advanced_summary}."
            )
        else:
            self._set_inline_hint(
                f"Text is ready. Current SSML uses {advanced_summary}."
            )

    def _handle_editor_text_changed(self):
        self._refresh_action_states()
        self.update_ssml_preview()

    def _load_audio_history(self):
        if not self.AUDIO_HISTORY_PATH.exists():
            return []

        try:
            with open(self.AUDIO_HISTORY_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            logger.warning("Unable to load audio history: {}", error)
            return []

        if not isinstance(data, list):
            return []

        cleaned_history = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            cleaned_history.append(
                {
                    "filename": str(entry.get("filename", "")),
                    "output_path": str(entry.get("output_path", "")),
                    "voice": str(entry.get("voice", self.settings.voice)),
                    "generated_at": str(entry.get("generated_at", "")),
                    "source": str(entry.get("source", "export")),
                    "source_text": str(entry.get("source_text", "")),
                    "settings": dict(entry.get("settings") or {}),
                }
            )
        return cleaned_history[: self.MAX_HISTORY_ITEMS]

    def _save_audio_history(self):
        self.AUDIO_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.AUDIO_HISTORY_PATH, "w", encoding="utf-8") as file:
            json.dump(self.audio_history, file, indent=2)

    def _format_history_entry(self, entry):
        source = "Preview" if entry["source"] == "preview" else "Export"
        return (
            f'{entry["generated_at"]} | {source} | {entry["voice"]} | '
            f'{entry["filename"]} | {entry["output_path"]}'
        )

    def _refresh_history_panel(self):
        self.view.historyList.clear()
        if not self.audio_history:
            self.view.historyList.addItem(
                "No generated audio yet. Preview or export speech to populate history."
            )
            return

        for entry in self.audio_history:
            item = QListWidgetItem(self._format_history_entry(entry))
            item.setToolTip(
                "Double-click to play. Right-click for more history actions."
            )
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.view.historyList.addItem(item)

    def _history_settings_snapshot(self):
        return {
            field_name: getattr(self.settings, field_name)
            for field_name in self.HISTORY_SETTINGS_FIELDS
            if hasattr(self.settings, field_name)
        }

    def _record_audio_history(self, file_path, source, source_text=None):
        audio_path = Path(file_path)
        if source_text is None and hasattr(self.view, "textEdit"):
            source_text = self._current_editor_text()
        entry = {
            "filename": audio_path.name,
            "output_path": str(audio_path.resolve()),
            "voice": self.settings.voice,
            "generated_at": datetime.now().strftime("%Y%m%d%H%M%S"),
            "source": source,
            "source_text": source_text or "",
            "settings": self._history_settings_snapshot(),
        }
        self.audio_history = [
            item
            for item in self.audio_history
            if not (
                item.get("output_path") == entry["output_path"]
                and item.get("source") == entry["source"]
            )
        ]
        self.audio_history.insert(0, entry)
        self.audio_history = self.audio_history[: self.MAX_HISTORY_ITEMS]
        self._save_audio_history()
        self._refresh_history_panel()
        logger.info("Recorded {} audio history entry for {}", source, file_path)

    def _selected_history_entry(self):
        current_item = self.view.historyList.currentItem()
        if current_item is not None:
            entry = current_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(entry, dict):
                return entry

        current_row = self.view.historyList.currentRow()
        if 0 <= current_row < len(self.audio_history):
            return self.audio_history[current_row]
        return None

    def show_history_context_menu(self, position):
        entry = self._selected_history_entry()
        if not entry:
            return

        menu = QMenu(self.view)
        play_action = menu.addAction("Play Audio")
        open_folder_action = menu.addAction("Open Containing Folder")
        copy_path_action = menu.addAction("Copy Audio Path")
        restore_action = menu.addAction("Restore Text && Settings")

        selected_action = menu.exec(self.view.historyList.mapToGlobal(position))
        if selected_action == play_action:
            self.play_selected_history_audio()
        elif selected_action == open_folder_action:
            self.open_selected_history_folder()
        elif selected_action == copy_path_action:
            self.copy_selected_history_path()
        elif selected_action == restore_action:
            self.restore_selected_history_context()

    def play_selected_history_audio(self, *_args):
        entry = self._selected_history_entry()
        if not entry:
            self.view.statusbar.showMessage("Select a history item first.")
            return

        audio_path = Path(entry.get("output_path", ""))
        if not audio_path.exists():
            QMessageBox.warning(
                self.view,
                "Audio Missing",
                f"The saved audio file could not be found:\n\n{audio_path}",
            )
            self.view.statusbar.showMessage("History audio file is missing.")
            return

        self.latest_audio_path = str(audio_path)
        if self.media_player is None or self.audio_output is None:
            QMessageBox.information(
                self.view,
                "Playback Unavailable",
                "Multimedia playback is unavailable in this environment.",
            )
            self.view.statusbar.showMessage(f"Selected history audio: {audio_path}")
            return

        self.playing_history_audio_path = str(audio_path)
        self.media_player.setSource(QUrl.fromLocalFile(str(audio_path)))
        self.media_player.play()
        self._refresh_action_states()
        self.view.statusbar.showMessage(f"Playing history audio: {audio_path.name}")
        logger.info("Playing history audio from {}", audio_path)

    def open_selected_history_folder(self):
        entry = self._selected_history_entry()
        if not entry:
            self.view.statusbar.showMessage("Select a history item first.")
            return

        audio_path = Path(entry.get("output_path", ""))
        folder_path = audio_path.parent
        if not folder_path.exists():
            QMessageBox.warning(
                self.view,
                "Folder Missing",
                f"The containing folder could not be found:\n\n{folder_path}",
            )
            self.view.statusbar.showMessage("History folder is missing.")
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder_path)))
        self.view.statusbar.showMessage(f"Opened folder: {folder_path}")
        logger.info("Opened history audio folder {}", folder_path)

    def copy_selected_history_path(self):
        entry = self._selected_history_entry()
        if not entry:
            self.view.statusbar.showMessage("Select a history item first.")
            return

        audio_path = entry.get("output_path", "")
        QApplication.clipboard().setText(audio_path)
        self.view.statusbar.showMessage("Copied history audio path.")

    def restore_selected_history_context(self):
        entry = self._selected_history_entry()
        if not entry:
            self.view.statusbar.showMessage("Select a history item first.")
            return

        source_text = entry.get("source_text", "")
        settings_snapshot = entry.get("settings") or {}
        if not source_text and not settings_snapshot:
            QMessageBox.information(
                self.view,
                "No History Context",
                "This history item does not include reusable text or settings.",
            )
            self.view.statusbar.showMessage("No reusable history context available.")
            return

        for field_name in self.HISTORY_SETTINGS_FIELDS:
            if field_name in settings_snapshot and hasattr(self.settings, field_name):
                setattr(self.settings, field_name, settings_snapshot[field_name])

        if source_text:
            self.view.textEdit.setPlainText(source_text)

        self.settings.save(self.SETTINGS_PATH)
        self.tts_processor = None
        self._refresh_ui_state()
        self.update_ssml_preview()
        self.view.statusbar.showMessage("Restored history text and settings.")
        logger.info("Restored text/settings from audio history entry.")

    def _resolve_azure_credentials(self):
        if self.settings.azure_key and self.settings.azure_region:
            return self.settings.azure_key, self.settings.azure_region

        try:
            return get_api_settings(".env")
        except Exception as error:
            logger.warning("Azure config unavailable: {}", error)
            return None, None

    def _ensure_tts_processor(self):
        azure_key, azure_region = self._resolve_azure_credentials()
        if not azure_key or not azure_region:
            return None

        if self.tts_processor is None:
            self.tts_processor = TTSProcessor(
                azure_key=azure_key,
                azure_region=azure_region,
            )
        return self.tts_processor

    def _build_ssml(self, text):
        return build_ssml_document(text, self.settings, self.cleaner)

    def _combine_document_rows(self, rows, content_mode="prefer_secondary"):
        chunks = []
        for row in rows:
            primary_text = (row.get("primary_text") or "").strip()
            secondary_text = (row.get("secondary_text") or "").strip()

            if content_mode == "secondary_only":
                resolved_text = secondary_text
            elif content_mode == "primary_only":
                resolved_text = primary_text
            elif content_mode == "combine":
                resolved_parts = [part for part in (primary_text, secondary_text) if part]
                resolved_text = "\n\n".join(resolved_parts)
            else:
                resolved_text = secondary_text or primary_text

            if resolved_text:
                chunks.append(resolved_text)

        return "\n\n".join(chunks)

    def update_ssml_preview(self):
        text = self._current_editor_text()
        if not text:
            self.view.ssmlPreview.clear()
            self._refresh_action_states()
            self.view.statusbar.showMessage("Enter text to preview SSML.")
            return

        self.view.ssmlPreview.setPlainText(self._build_ssml(text))
        self._refresh_action_states()
        self.view.statusbar.showMessage("SSML preview updated.")
        logger.info("SSML preview updated.")

    def clean_text(self):
        text = self._current_editor_text()
        if not text:
            QMessageBox.information(
                self.view,
                "No Text",
                "Paste or type text before cleaning it.",
            )
            return

        cleaned = self.cleaner.clean_all(text)
        self.view.textEdit.setPlainText(cleaned)
        self.view.statusbar.showMessage("Text cleaned for speech synthesis.")
        logger.info("Editor text cleaned for synthesis.")

    def generate_audio_bytes(self):
        text = self._current_editor_text()
        if not text:
            QMessageBox.information(
                self.view,
                "No Text",
                "Paste or type text before generating audio.",
            )
            return None

        return self._synthesize_text(text)

    def _synthesize_text(self, text):
        tts_processor = self._ensure_tts_processor()
        if tts_processor is None:
            QMessageBox.warning(
                self.view,
                "Azure Setup Required",
                (
                    "The application could not find valid Azure Speech credentials.\n\n"
                    "Open Tools > Settings and enter your Azure key and region, "
                    "or create a valid .env file."
                ),
            )
            self.view.statusbar.showMessage(
                "Azure credentials are required before generating speech."
            )
            return None

        try:
            return tts_processor.text_to_speech(
                self._build_ssml(text),
                use_ssml=True,
            )
        except Exception as error:
            logger.exception("Speech generation failed: {}", error)
            QMessageBox.critical(
                self.view,
                "Generation Error",
                f"Unable to synthesize speech.\n\n{error}",
            )
            self.view.statusbar.showMessage("Speech generation failed.")
            return None

    def generate_and_play_audio(self):
        audio_data = self.generate_audio_bytes()
        if audio_data is None:
            return

        self._cleanup_preview_audio()

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3",
        ) as temp_file:
            temp_file.write(audio_data)
            self.preview_audio_path = temp_file.name
            self.latest_audio_path = temp_file.name

        self._record_audio_history(self.preview_audio_path, "preview")
        self._refresh_action_states()

        if self.media_player is None or self.audio_output is None:
            QMessageBox.information(
                self.view,
                "Playback Unavailable",
                "Audio was generated, but multimedia playback is unavailable in this environment.",
            )
            self.view.statusbar.showMessage(
                f"Audio generated at {self.latest_audio_path}"
            )
            logger.info(
                "Generated preview audio without playback support: {}",
                self.latest_audio_path,
            )
            return

        self.media_player.setSource(QUrl.fromLocalFile(self.preview_audio_path))
        self.playing_history_audio_path = None
        self.media_player.play()
        self.view.statusbar.showMessage("Playing generated audio.")
        logger.info("Playing generated audio from {}", self.preview_audio_path)

    def stop_audio(self):
        if self.media_player is not None:
            self.media_player.stop()
        self.playing_history_audio_path = None
        self._refresh_action_states()
        self.view.statusbar.showMessage("Playback stopped.")
        logger.info("Playback stopped.")

    def export_audio_file(self):
        audio_data = self.generate_audio_bytes()
        if audio_data is None:
            return

        output_dir = Path(self.settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Save Audio File",
            str(output_dir / "speech_output.mp3"),
            "MP3 Files (*.mp3)",
        )
        if not file_path:
            self.view.statusbar.showMessage("Audio export canceled.")
            return

        with open(file_path, "wb") as file:
            file.write(audio_data)

        self.latest_audio_path = file_path
        self._record_audio_history(file_path, "export")
        self.view.statusbar.showMessage(f"Saved audio to {file_path}")
        logger.info("Saved audio export to {}", file_path)

    def batch_export_imported_rows(self, rows):
        if self.batch_export_active:
            QMessageBox.information(
                self.view,
                "Batch Export Running",
                "A batch export is already running. Wait for it to finish before starting another one.",
            )
            return

        if not rows:
            QMessageBox.information(
                self.view,
                "Nothing To Export",
                "Select one or more imported document rows before batch exporting.",
            )
            return

        azure_key, azure_region = self._resolve_azure_credentials()
        if not azure_key or not azure_region:
            QMessageBox.warning(
                self.view,
                "Azure Setup Required",
                (
                    "The application could not find valid Azure Speech credentials.\n\n"
                    "Open Tools > Settings and enter your Azure key and region, "
                    "or create a valid .env file."
                ),
            )
            self.view.statusbar.showMessage(
                "Azure credentials are required before batch export."
            )
            return

        output_dir = Path(self.settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        selected_dir = QFileDialog.getExistingDirectory(
            self.view,
            "Choose Batch Export Folder",
            str(output_dir),
        )
        if not selected_dir:
            self.view.statusbar.showMessage("Batch export canceled.")
            return

        self.batch_export_active = True
        self._refresh_action_states()
        self.view.statusbar.showMessage("Batch export started in the background.")

        self.batch_export_thread = QThread(self.view)
        self.batch_export_worker = BatchExportWorker(
            rows=rows,
            output_dir=selected_dir,
            settings=self.settings,
            azure_key=azure_key,
            azure_region=azure_region,
        )
        self.batch_export_worker.moveToThread(self.batch_export_thread)
        self.batch_export_thread.started.connect(self.batch_export_worker.run)
        self.batch_export_worker.progress.connect(self._handle_batch_export_progress)
        self.batch_export_worker.finished.connect(self._handle_batch_export_finished)
        self.batch_export_worker.failed.connect(self._handle_batch_export_failed)
        self.batch_export_worker.cancelled.connect(self._handle_batch_export_cancelled)
        self.batch_export_worker.finished.connect(self.batch_export_thread.quit)
        self.batch_export_worker.failed.connect(self.batch_export_thread.quit)
        self.batch_export_worker.cancelled.connect(self.batch_export_thread.quit)
        self.batch_export_worker.finished.connect(self.batch_export_worker.deleteLater)
        self.batch_export_worker.failed.connect(self.batch_export_worker.deleteLater)
        self.batch_export_worker.cancelled.connect(
            self.batch_export_worker.deleteLater
        )
        self.batch_export_thread.finished.connect(self.batch_export_thread.deleteLater)
        self.batch_export_thread.finished.connect(self._clear_batch_export_worker)
        self.batch_export_thread.start()
        logger.info("Started background batch export to {}", selected_dir)

    def _handle_batch_export_progress(self, completed, total, file_path):
        self.latest_audio_path = file_path
        self.view.statusbar.showMessage(
            f"Batch export progress: {completed}/{total} files generated."
        )

    def _handle_batch_export_finished(self, exported_files):
        exported_paths = [Path(file_path) for file_path in exported_files]
        self.batch_export_active = False

        if not exported_paths:
            QMessageBox.information(
                self.view,
                "No Content",
                "The selected rows did not contain exportable content.",
            )
            self.view.statusbar.showMessage("Batch export finished with no content.")
            return

        for file_path in exported_paths:
            self.latest_audio_path = str(file_path)
            self._record_audio_history(file_path, "export")

        selected_path = exported_paths[0].parent
        self.view.statusbar.showMessage(
            f"Batch exported {len(exported_paths)} audio files to {selected_path}"
        )
        QMessageBox.information(
            self.view,
            "Batch Export Complete",
            (
                f"Created {len(exported_paths)} audio files in:\n\n"
                f"{selected_path}"
            ),
        )
        logger.info(
            "Batch exported {} document audio files to {}",
            len(exported_paths),
            selected_path,
        )

    def _handle_batch_export_failed(self, message, exported_files):
        self.batch_export_active = False
        exported_paths = [Path(file_path) for file_path in exported_files]
        for file_path in exported_paths:
            self.latest_audio_path = str(file_path)
            self._record_audio_history(file_path, "export")

        if exported_paths:
            self.view.statusbar.showMessage(
                f"Batch export stopped after {len(exported_paths)} files."
            )
        else:
            self.view.statusbar.showMessage("Batch export failed.")

        QMessageBox.critical(
            self.view,
            "Batch Export Error",
            f"Unable to finish batch export.\n\n{message}",
        )

    def _handle_batch_export_cancelled(self, exported_files):
        self.batch_export_active = False
        exported_paths = [Path(file_path) for file_path in exported_files]
        for file_path in exported_paths:
            self.latest_audio_path = str(file_path)
            self._record_audio_history(file_path, "export")

        self.view.statusbar.showMessage(
            f"Batch export canceled after {len(exported_paths)} completed file(s)."
        )
        QMessageBox.information(
            self.view,
            "Batch Export Canceled",
            f"Created {len(exported_paths)} audio file(s) before cancellation.",
        )
        logger.info(
            "Batch export canceled after {} completed files.",
            len(exported_paths),
        )

    def _clear_batch_export_worker(self):
        self.batch_export_thread = None
        self.batch_export_worker = None
        self.batch_export_active = False
        self._refresh_action_states()

    def cancel_background_work(self):
        cancel_requested = False

        if self.batch_export_worker is not None:
            self.batch_export_worker.request_cancel()
            cancel_requested = True

        if self.document_parse_worker is not None:
            self.document_parse_worker.request_cancel()
            cancel_requested = True

        if not cancel_requested:
            self.view.statusbar.showMessage("No background task is running.")
            self._refresh_action_states()
            return

        self.view.cancelTaskButton.setEnabled(False)
        self.view.statusbar.showMessage(
            "Cancel requested. The current worker step will stop when safe."
        )
        logger.info("Requested cancellation for active background work.")

    def update_playback_volume(self, value):
        self.settings.playback_volume = value
        self.view.playbackVolumeValueLabel.setText(f"{value}%")
        if self.audio_output is not None:
            self.audio_output.setVolume(value / 100)
        if not self._updating_ui_state:
            self.settings.save(self.SETTINGS_PATH)
        logger.info("Playback volume changed to {}%", value)

    def open_document_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Open Document",
            str(Path.cwd()),
            self.document_scraper.SUPPORTED_FILTER,
        )
        if not file_path:
            return

        self._start_document_parse(
            source=file_path,
            source_kind="file",
            source_label=file_path,
            status_message="Loading document in the background.",
        )

    def open_url_source(self):
        url, accepted = QInputDialog.getText(
            self.view,
            "Open URL",
            "Enter an http or https URL to import:",
        )
        if not accepted or not url.strip():
            return

        self._start_document_parse(
            source=url.strip(),
            source_kind="url",
            source_label=url.strip(),
            status_message="Loading URL in the background.",
        )

    def open_raw_html_source(self):
        html, accepted = QInputDialog.getMultiLineText(
            self.view,
            "Import Raw HTML",
            "Paste raw HTML to import:",
        )
        if not accepted or not html.strip():
            return

        self._start_document_parse(
            source=html,
            source_kind="html",
            source_label="pasted raw HTML",
            status_message="Loading raw HTML in the background.",
        )

    def _start_document_parse(self, source, source_kind, source_label, status_message):
        if self.document_parse_thread is not None:
            QMessageBox.information(
                self.view,
                "Document Loading",
                "A document source is already loading. Wait for it to finish before opening another one.",
            )
            return

        self.document_parse_path = source_label
        self.document_parse_thread = QThread(self.view)
        self.document_parse_worker = DocumentParseWorker(source, source_kind)
        self.document_parse_worker.moveToThread(self.document_parse_thread)
        self.document_parse_thread.started.connect(self.document_parse_worker.run)
        self.document_parse_worker.finished.connect(
            self._handle_document_parse_finished
        )
        self.document_parse_worker.failed.connect(self._handle_document_parse_failed)
        self.document_parse_worker.cancelled.connect(
            self._handle_document_parse_cancelled
        )
        self.document_parse_worker.finished.connect(self.document_parse_thread.quit)
        self.document_parse_worker.failed.connect(self.document_parse_thread.quit)
        self.document_parse_worker.cancelled.connect(self.document_parse_thread.quit)
        self.document_parse_worker.finished.connect(
            self.document_parse_worker.deleteLater
        )
        self.document_parse_worker.failed.connect(
            self.document_parse_worker.deleteLater
        )
        self.document_parse_worker.cancelled.connect(
            self.document_parse_worker.deleteLater
        )
        self.document_parse_thread.finished.connect(
            self.document_parse_thread.deleteLater
        )
        self.document_parse_thread.finished.connect(self._clear_document_parse_worker)
        self._refresh_action_states()
        self.view.statusbar.showMessage(status_message)
        self.document_parse_thread.start()
        logger.info(
            "Started background {} document load for {}",
            source_kind,
            source_label,
        )

    def _handle_document_parse_finished(self, rows):
        imported_text = self._combine_document_rows(rows)
        file_path = self.document_parse_path
        if not imported_text.strip():
            QMessageBox.information(
                self.view,
                "No Content",
                "The selected document did not contain readable text.",
            )
            self.view.statusbar.showMessage(
                "Document load finished with no readable text."
            )
            return

        self.view.textEdit.setPlainText(imported_text)
        self._refresh_action_states()
        self.view.statusbar.showMessage(
            f"Loaded {len(rows)} document section(s) from {file_path}"
        )
        logger.info("Loaded document {}", file_path)

    def _handle_document_parse_failed(self, message):
        logger.error("Failed to open document: {}", message)
        QMessageBox.critical(
            self.view,
            "Open Error",
            f"Unable to read the selected document.\n\n{message}",
        )
        self.view.statusbar.showMessage("Document load failed.")

    def _handle_document_parse_cancelled(self):
        self.view.statusbar.showMessage("Document load canceled.")
        logger.info("Document load canceled.")

    def _clear_document_parse_worker(self):
        self.document_parse_thread = None
        self.document_parse_worker = None
        self.document_parse_path = None
        self._refresh_action_states()

    def export_editor_text(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Export Editor Text",
            str(Path.cwd() / "speech_input.txt"),
            "Text Files (*.txt);;Markdown Files (*.md);;HTML Files (*.html)",
        )
        if not file_path:
            return

        output_text = self.view.textEdit.toPlainText()
        if file_path.lower().endswith(".html"):
            escaped_text = escape(output_text).replace("\n", "<br/>\n")
            output_text = (
                "<!DOCTYPE html>\n"
                "<html>\n"
                "<head><meta charset=\"utf-8\"><title>Speech Input</title></head>\n"
                f"<body><p>{escaped_text}</p></body>\n"
                "</html>\n"
            )

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(output_text)
        self.view.statusbar.showMessage(
            f"Exported editor text to {file_path}. Source documents are not round-tripped."
        )
        logger.info("Exported editor contents to {}", file_path)

    def open_settings(self):
        updated_settings = self.settings_controller.edit_settings(self.settings)
        if updated_settings is None:
            return

        self.settings = updated_settings
        self.settings.save(self.SETTINGS_PATH)
        self.tts_processor = None
        log_file = configure_logging(self.settings.logging_enabled)
        self._refresh_ui_state()
        self.update_ssml_preview()
        self.view.statusbar.showMessage("Settings updated.")
        if self.settings.logging_enabled and log_file is not None:
            logger.info("Settings updated and logging enabled at {}", log_file)

    def open_second_window(self):
        if self.second_window and self.second_window.isVisible():
            self.second_window.raise_()
            self.second_window.activateWindow()
            return

        self.second_window = SecondApp(self.view)
        self.second_controller = SecondController(self.second_window)
        self.second_window.textImported.connect(self.import_text_from_scraper)
        self.second_window.batchRequested.connect(
            self.batch_export_imported_rows
        )
        self.second_window.show()
        logger.info("Opened document import dialog.")

    def import_text_from_scraper(self, text):
        self.view.textEdit.setPlainText(text)
        self._refresh_action_states()
        self.view.statusbar.showMessage("Imported text from document.")
        logger.info("Imported text from document into main editor.")

    def show_about(self):
        QMessageBox.information(
            self.view,
            "About Text To Speech",
            (
                "Text To Speech is a PyQt desktop app for experimenting with "
                "Azure speech synthesis, SSML previewing, and multi-format document imports."
            ),
        )

    def _cleanup_preview_audio(self):
        if not self.preview_audio_path:
            return

        if self.media_player is not None:
            self.media_player.stop()
            self.media_player.setSource(QUrl())

        preview_path = Path(self.preview_audio_path)
        if preview_path.exists():
            preview_path.unlink(missing_ok=True)
            logger.info("Removed preview audio file {}", preview_path)

        self.preview_audio_path = None
        self._refresh_action_states()

    def shutdown(self):
        self._cleanup_preview_audio()
