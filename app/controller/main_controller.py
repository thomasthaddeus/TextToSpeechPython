import json
from pathlib import Path
import tempfile
from datetime import datetime
from xml.sax.saxutils import escape

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QFileDialog, QMessageBox

try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
except ImportError:  # pragma: no cover - optional multimedia backend
    QAudioOutput = None
    QMediaPlayer = None

from app.controller.second_controller import SecondController
from app.controller.settings_controller import SettingsController
from app.gui.second_window import SecondApp
from app.model.api.api_config import get_api_settings
from app.model.app_settings import AppSettings
from app.model.processors.tts_processor import TTSProcessor
from app.model.ssml.text_to_ssml import TextToSSML
from app.model.ssml.ssml_config import SSMLConfig
from app.utils.logging_config import configure_logging
from app.utils.text_cleaner import TextCleaner
from loguru import logger


class MainController:
    SETTINGS_PATH = Path("data/dynamic/app_settings.json")
    AUDIO_HISTORY_PATH = Path("data/dynamic/audio_history.json")
    MAX_HISTORY_ITEMS = 10

    def __init__(self, view):
        self.view = view
        self.cleaner = TextCleaner()
        self.settings = AppSettings.load(self.SETTINGS_PATH)
        self.voice_config = SSMLConfig()
        self.tts_processor = None
        self.settings_controller = SettingsController(self.view)
        self.second_window = None
        self.second_controller = None
        self.latest_audio_path = None
        self.preview_audio_path = None
        self.audio_output = None
        self.media_player = None
        self._updating_ui_state = False
        self.audio_history = self._load_audio_history()
        self._setup_media_backend()
        self._connect_signals()
        self._refresh_ui_state()
        self._refresh_history_panel()
        self.update_ssml_preview()
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
        self.view.playbackVolumeSlider.valueChanged.connect(
            self.update_playback_volume
        )
        self.view.actionOpenText.triggered.connect(self.open_text_file)
        self.view.actionSaveText.triggered.connect(self.save_text_file)
        self.view.actionExportAudio.triggered.connect(self.export_audio_file)
        self.view.actionExit.triggered.connect(self.view.close)
        self.view.actionSettings.triggered.connect(self.open_settings)
        self.view.actionOpenScraper.triggered.connect(self.open_second_window)
        self.view.actionAbout.triggered.connect(self.show_about)
        self.view.textEdit.textChanged.connect(self._handle_editor_text_changed)

    def _sanitize_batch_name(self, value):
        sanitized = "".join(
            character if character.isalnum() or character in ("-", "_") else "_"
            for character in value.strip().lower()
        )
        sanitized = sanitized.strip("_")
        return sanitized or "item"

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

    def _current_editor_text(self):
        return self.view.textEdit.toPlainText().strip()

    def _set_inline_hint(self, text):
        self.view.actionHintLabel.setText(text)

    def _refresh_action_states(self):
        has_text = bool(self._current_editor_text())
        multimedia_available = (
            self.media_player is not None and self.audio_output is not None
        )
        has_preview_audio = bool(self.preview_audio_path)

        self.view.previewButton.setEnabled(has_text)
        self.view.cleanTextButton.setEnabled(has_text)
        self.view.playButton.setEnabled(has_text)
        self.view.generateButton.setEnabled(has_text)
        self.view.actionExportAudio.setEnabled(has_text)
        self.view.stopButton.setEnabled(multimedia_available and has_preview_audio)
        self.view.playbackVolumeSlider.setEnabled(multimedia_available)

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
            self.view.historyList.addItem(self._format_history_entry(entry))

    def _record_audio_history(self, file_path, source):
        audio_path = Path(file_path)
        entry = {
            "filename": audio_path.name,
            "output_path": str(audio_path.resolve()),
            "voice": self.settings.voice,
            "generated_at": datetime.now().strftime("%Y%m%d%H%M%S"),
            "source": source,
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
        working_text = text
        if self.settings.auto_clean_text:
            working_text = self.cleaner.clean_all(working_text)

        working_text = escape(working_text)

        converter = TextToSSML(voice_name=self.settings.voice)
        ssml_content = working_text

        if self.settings.pause_duration != "none":
            pause_tag = f'<break time="{self.settings.pause_duration}"/>'
            if self.settings.pause_position == "before":
                ssml_content = f"{pause_tag}{ssml_content}"
            else:
                ssml_content = f"{ssml_content}{pause_tag}"

        if self.settings.emphasis_level != "none":
            ssml_content = (
                f'<emphasis level="{self.settings.emphasis_level}">{ssml_content}</emphasis>'
            )

        prosody_attributes = [
            f'rate="{self.settings.speaking_rate}"',
            f'volume="{self.settings.synthesis_volume}"',
        ]
        if self.settings.pitch != "default":
            prosody_attributes.append(f'pitch="{self.settings.pitch}"')
        if self.settings.pitch_range != "default":
            prosody_attributes.append(f'range="{self.settings.pitch_range}"')

        prosody_text = (
            f"<prosody {' '.join(prosody_attributes)}>{ssml_content}</prosody>"
        )
        return converter.convert(prosody_text)

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
        self.media_player.play()
        self.view.statusbar.showMessage("Playing generated audio.")
        logger.info("Playing generated audio from {}", self.preview_audio_path)

    def stop_audio(self):
        if self.media_player is not None:
            self.media_player.stop()
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
        if not rows:
            QMessageBox.information(
                self.view,
                "Nothing To Export",
                "Select one or more imported slide rows before batch exporting.",
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

        selected_path = Path(selected_dir)
        exported_files = []
        for row in rows:
            resolved_text = (row.get("resolved_text") or "").strip()
            if not resolved_text:
                continue

            audio_data = self._synthesize_text(resolved_text)
            if audio_data is None:
                if exported_files:
                    self.view.statusbar.showMessage(
                        f"Batch export stopped after {len(exported_files)} files."
                    )
                return

            mode_name = self._sanitize_batch_name(
                row.get("content_mode", "prefer_notes")
            )
            title_name = self._sanitize_batch_name(
                row.get("title", f"item_{row.get('item_number', 0)}")
            )
            file_name = (
                f"item_{int(row.get('item_number', 0)):02d}_{title_name}_{mode_name}.mp3"
            )
            file_path = selected_path / file_name
            with open(file_path, "wb") as file:
                file.write(audio_data)

            exported_files.append(file_path)
            self.latest_audio_path = str(file_path)
            self._record_audio_history(file_path, "export")

        if not exported_files:
            QMessageBox.information(
                self.view,
                "No Content",
                "The selected rows did not contain exportable content.",
            )
            return

        self.view.statusbar.showMessage(
            f"Batch exported {len(exported_files)} audio files to {selected_path}"
        )
        QMessageBox.information(
            self.view,
            "Batch Export Complete",
            (
                f"Created {len(exported_files)} audio files in:\n\n"
                f"{selected_path}"
            ),
        )
        logger.info(
            "Batch exported {} document audio files to {}",
            len(exported_files),
            selected_path,
        )

    def update_playback_volume(self, value):
        self.settings.playback_volume = value
        self.view.playbackVolumeValueLabel.setText(f"{value}%")
        if self.audio_output is not None:
            self.audio_output.setVolume(value / 100)
        if not self._updating_ui_state:
            self.settings.save(self.SETTINGS_PATH)
        logger.info("Playback volume changed to {}%", value)

    def open_text_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Open Text File",
            str(Path.cwd()),
            "Text Files (*.txt);;All Files (*.*)",
        )
        if not file_path:
            return

        with open(file_path, "r", encoding="utf-8") as file:
            self.view.textEdit.setPlainText(file.read())
        self._refresh_action_states()
        self.view.statusbar.showMessage(f"Loaded text from {file_path}")
        logger.info("Loaded text file {}", file_path)

    def save_text_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Save Text File",
            str(Path.cwd() / "speech_input.txt"),
            "Text Files (*.txt)",
        )
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.view.textEdit.toPlainText())
        self.view.statusbar.showMessage(f"Saved text to {file_path}")
        logger.info("Saved editor contents to {}", file_path)

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
