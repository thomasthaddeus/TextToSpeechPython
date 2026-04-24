"""Settings dialog for the desktop application."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt

from app.model.api.azure_tts_api import AzureTTSAPI
from app.model.app_settings import AppSettings
from app.model.ssml.ssml_config import SSMLConfig


class SettingsDialog(QDialog):
    """
    Modal dialog for editing application settings.
    """

    RATE_OPTIONS = ["x-slow", "slow", "medium", "fast", "x-fast"]
    VOLUME_OPTIONS = ["silent", "x-soft", "soft", "medium", "loud", "x-loud"]

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = AppSettings(**settings.__dict__)
        self.voice_config = SSMLConfig()
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.voice_combo = QComboBox(self)
        self.voice_combo.addItems(self.voice_config.list_voices())
        form_layout.addRow("Voice", self.voice_combo)

        self.azure_key_edit = QLineEdit(self)
        self.azure_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Azure Key", self.azure_key_edit)

        self.azure_region_edit = QLineEdit(self)
        self.azure_region_edit.setPlaceholderText("eastus")
        form_layout.addRow("Azure Region", self.azure_region_edit)

        self.rate_combo = QComboBox(self)
        self.rate_combo.addItems(self.RATE_OPTIONS)
        form_layout.addRow("Speech Rate", self.rate_combo)

        self.synthesis_volume_combo = QComboBox(self)
        self.synthesis_volume_combo.addItems(self.VOLUME_OPTIONS)
        form_layout.addRow("Speech Volume", self.synthesis_volume_combo)

        playback_row = QHBoxLayout()
        self.playback_volume_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.playback_volume_slider.setRange(0, 100)
        self.playback_volume_label = QLabel(self)
        self.playback_volume_slider.valueChanged.connect(
            self._update_playback_label
        )
        playback_row.addWidget(self.playback_volume_slider)
        playback_row.addWidget(self.playback_volume_label)
        form_layout.addRow("Playback Volume", playback_row)

        output_row = QHBoxLayout()
        self.output_dir_edit = QLineEdit(self)
        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self._choose_output_dir)
        output_row.addWidget(self.output_dir_edit)
        output_row.addWidget(self.browse_button)
        form_layout.addRow("Output Directory", output_row)

        self.auto_clean_checkbox = QCheckBox(
            "Clean text before generating speech",
            self,
        )
        form_layout.addRow("", self.auto_clean_checkbox)

        self.logging_checkbox = QCheckBox(
            "Enable application logging",
            self,
        )
        form_layout.addRow("", self.logging_checkbox)

        connection_row = QHBoxLayout()
        self.test_connection_button = QPushButton("Test Connection", self)
        self.connection_status_label = QLabel("Not tested", self)
        self.test_connection_button.clicked.connect(self._test_connection)
        connection_row.addWidget(self.test_connection_button)
        connection_row.addWidget(self.connection_status_label)
        form_layout.addRow("Azure Status", connection_row)

        main_layout.addLayout(form_layout)

        button_row = QHBoxLayout()
        self.save_button = QPushButton("Save", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.save_button.clicked.connect(self._accept_if_valid)
        self.cancel_button.clicked.connect(self.reject)
        button_row.addStretch(1)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.cancel_button)
        main_layout.addLayout(button_row)

    def _load_settings(self):
        self.voice_combo.setCurrentText(self.settings.voice)
        self.azure_key_edit.setText(self.settings.azure_key)
        self.azure_region_edit.setText(self.settings.azure_region)
        self.rate_combo.setCurrentText(self.settings.speaking_rate)
        self.synthesis_volume_combo.setCurrentText(self.settings.synthesis_volume)
        self.playback_volume_slider.setValue(self.settings.playback_volume)
        self.output_dir_edit.setText(self.settings.output_dir)
        self.auto_clean_checkbox.setChecked(self.settings.auto_clean_text)
        self.logging_checkbox.setChecked(self.settings.logging_enabled)
        self._update_playback_label(self.settings.playback_volume)

    def _update_playback_label(self, value):
        self.playback_volume_label.setText(f"{value}%")

    def _choose_output_dir(self):
        chosen_dir = QFileDialog.getExistingDirectory(
            self,
            "Choose Output Directory",
            self.output_dir_edit.text() or str(Path.cwd()),
        )
        if chosen_dir:
            self.output_dir_edit.setText(chosen_dir)

    def get_settings(self):
        """
        Build a validated settings object from the dialog state.
        """
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(
                self,
                "Missing Output Directory",
                "Choose a directory for generated audio files.",
            )
            return None

        self.settings.voice = self.voice_combo.currentText()
        self.settings.azure_key = self.azure_key_edit.text().strip()
        self.settings.azure_region = self.azure_region_edit.text().strip()
        self.settings.speaking_rate = self.rate_combo.currentText()
        self.settings.synthesis_volume = (
            self.synthesis_volume_combo.currentText()
        )
        self.settings.playback_volume = self.playback_volume_slider.value()
        self.settings.output_dir = output_dir
        self.settings.auto_clean_text = self.auto_clean_checkbox.isChecked()
        self.settings.logging_enabled = self.logging_checkbox.isChecked()
        return self.settings

    def _accept_if_valid(self):
        if self.get_settings() is not None:
            self.accept()

    def _test_connection(self):
        azure_key = self.azure_key_edit.text().strip()
        azure_region = self.azure_region_edit.text().strip()
        if not azure_key or not azure_region:
            QMessageBox.warning(
                self,
                "Missing Azure Settings",
                "Enter both the Azure key and region before testing the connection.",
            )
            self.connection_status_label.setText("Missing credentials")
            return

        try:
            client = AzureTTSAPI(azure_key, azure_region)
            audio_data = client.get_audio_from_text("Connection test.")
        except Exception as error:
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"Unable to validate the Azure Speech configuration.\n\n{error}",
            )
            self.connection_status_label.setText("Connection failed")
            return

        if audio_data:
            self.connection_status_label.setText("Connection OK")
            QMessageBox.information(
                self,
                "Connection Successful",
                "Azure Speech credentials are valid.",
            )
        else:
            self.connection_status_label.setText("No audio returned")
