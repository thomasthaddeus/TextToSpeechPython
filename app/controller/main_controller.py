from pathlib import Path
import tempfile

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
from app.model.app_settings import AppSettings
from app.model.processors.tts_processor import TTSProcessor
from app.model.ssml.text_to_ssml import TextToSSML
from app.model.ssml.ssml_config import SSMLConfig
from app.utils.text_cleaner import TextCleaner


class MainController:
    SETTINGS_PATH = Path("data/dynamic/app_settings.json")

    def __init__(self, view):
        self.view = view
        self.cleaner = TextCleaner()
        self.settings = AppSettings.load(self.SETTINGS_PATH)
        self.voice_config = SSMLConfig()
        self.tts_processor = TTSProcessor(".env")
        self.settings_controller = SettingsController(self.view)
        self.second_window = None
        self.second_controller = None
        self.latest_audio_path = None
        self.audio_output = None
        self.media_player = None
        self._setup_media_backend()
        self._connect_signals()
        self._refresh_ui_state()
        self.update_ssml_preview()

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
        self.view.textEdit.textChanged.connect(self.update_ssml_preview)

    def _refresh_ui_state(self):
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
        self.view.statusbar.showMessage("Ready")

    def _current_editor_text(self):
        return self.view.textEdit.toPlainText().strip()

    def _build_ssml(self, text):
        working_text = text
        if self.settings.auto_clean_text:
            working_text = self.cleaner.clean_all(working_text)

        converter = TextToSSML(voice_name=self.settings.voice)
        prosody_text = (
            f'<prosody rate="{self.settings.speaking_rate}" '
            f'volume="{self.settings.synthesis_volume}">{working_text}</prosody>'
        )
        return converter.convert(prosody_text)

    def update_ssml_preview(self):
        text = self._current_editor_text()
        if not text:
            self.view.ssmlPreview.clear()
            self.view.statusbar.showMessage("Enter text to preview SSML.")
            return

        self.view.ssmlPreview.setPlainText(self._build_ssml(text))
        self.view.statusbar.showMessage("SSML preview updated.")

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

    def generate_audio_bytes(self):
        text = self._current_editor_text()
        if not text:
            QMessageBox.information(
                self.view,
                "No Text",
                "Paste or type text before generating audio.",
            )
            return None

        try:
            audio_data = self.tts_processor.text_to_speech(
                self._build_ssml(text),
                use_ssml=True,
            )
        except Exception as error:
            QMessageBox.critical(
                self.view,
                "Generation Error",
                f"Unable to synthesize speech.\n\n{error}",
            )
            self.view.statusbar.showMessage("Speech generation failed.")
            return None

        return audio_data

    def generate_and_play_audio(self):
        audio_data = self.generate_audio_bytes()
        if audio_data is None:
            return

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3",
        ) as temp_file:
            temp_file.write(audio_data)
            self.latest_audio_path = temp_file.name

        if self.media_player is None or self.audio_output is None:
            QMessageBox.information(
                self.view,
                "Playback Unavailable",
                "Audio was generated, but multimedia playback is unavailable in this environment.",
            )
            self.view.statusbar.showMessage(
                f"Audio generated at {self.latest_audio_path}"
            )
            return

        self.media_player.setSource(QUrl.fromLocalFile(self.latest_audio_path))
        self.media_player.play()
        self.view.statusbar.showMessage("Playing generated audio.")

    def stop_audio(self):
        if self.media_player is not None:
            self.media_player.stop()
        self.view.statusbar.showMessage("Playback stopped.")

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
        self.view.statusbar.showMessage(f"Saved audio to {file_path}")

    def update_playback_volume(self, value):
        self.settings.playback_volume = value
        self.view.playbackVolumeValueLabel.setText(f"{value}%")
        if self.audio_output is not None:
            self.audio_output.setVolume(value / 100)

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
        self.view.statusbar.showMessage(f"Loaded text from {file_path}")

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

    def open_settings(self):
        updated_settings = self.settings_controller.edit_settings(self.settings)
        if updated_settings is None:
            return

        self.settings = updated_settings
        self.settings.save(self.SETTINGS_PATH)
        self._refresh_ui_state()
        self.update_ssml_preview()
        self.view.statusbar.showMessage("Settings updated.")

    def open_second_window(self):
        if self.second_window and self.second_window.isVisible():
            self.second_window.raise_()
            self.second_window.activateWindow()
            return

        self.second_window = SecondApp(self.view)
        self.second_controller = SecondController(self.second_window)
        self.second_window.textImported.connect(self.import_text_from_scraper)
        self.second_window.show()

    def import_text_from_scraper(self, text):
        self.view.textEdit.setPlainText(text)
        self.view.statusbar.showMessage("Imported text from PowerPoint.")

    def show_about(self):
        QMessageBox.information(
            self.view,
            "About Text To Speech",
            (
                "Text To Speech is a PyQt desktop app for experimenting with "
                "Azure speech synthesis, SSML previewing, and PowerPoint note imports."
            ),
        )
