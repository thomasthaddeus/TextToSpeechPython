"""Settings dialog for the desktop application."""

from pathlib import Path

from PyQt6.QtCore import Qt
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
    QWidget,
)

from app.model.app_settings import AppSettings
from app.model.tts_providers import (
    TTSProviderConfig,
    TTSRequest,
    create_tts_provider,
    get_provider_display_name,
    get_voice_suggestions,
)


class SettingsEditor(QWidget):
    """
    Reusable settings editor used by both the modal dialog and main sidebar.
    """

    RATE_OPTIONS = ["x-slow", "slow", "medium", "fast", "x-fast"]
    VOLUME_OPTIONS = ["silent", "x-soft", "soft", "medium", "loud", "x-loud"]
    EMPHASIS_OPTIONS = ["none", "reduced", "moderate", "strong"]
    PITCH_OPTIONS = ["default", "x-low", "low", "medium", "high", "x-high"]
    RANGE_OPTIONS = ["default", "x-low", "low", "medium", "high", "x-high"]
    PAUSE_OPTIONS = ["none", "250ms", "500ms", "1s", "2s"]
    PAUSE_POSITION_OPTIONS = ["before", "after"]
    PROVIDERS = (
        ("azure", "Azure Speech"),
        ("polly", "Amazon Polly"),
    )
    POLLY_ENGINE_OPTIONS = ["standard", "neural", "long-form", "generative"]

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = AppSettings(**settings.__dict__)
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.provider_combo = QComboBox(self)
        for provider_name, label in self.PROVIDERS:
            self.provider_combo.addItem(label, provider_name)
        self.provider_combo.currentIndexChanged.connect(
            self._handle_provider_changed
        )
        form_layout.addRow("TTS Provider", self.provider_combo)

        self.voice_combo = QComboBox(self)
        self.voice_combo.setEditable(True)
        form_layout.addRow("Voice", self.voice_combo)

        self.azure_key_edit = QLineEdit(self)
        self.azure_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Azure Key", self.azure_key_edit)

        self.azure_region_edit = QLineEdit(self)
        self.azure_region_edit.setPlaceholderText("eastus")
        form_layout.addRow("Azure Region", self.azure_region_edit)

        polly_path_row = QHBoxLayout()
        self.polly_config_path_edit = QLineEdit(self)
        self.polly_config_path_edit.setPlaceholderText(".polly.env")
        self.polly_config_browse_button = QPushButton("Browse", self)
        self.polly_config_browse_button.clicked.connect(
            self._choose_polly_config_file
        )
        polly_path_row.addWidget(self.polly_config_path_edit)
        polly_path_row.addWidget(self.polly_config_browse_button)
        form_layout.addRow("Polly Config File", polly_path_row)

        self.polly_engine_combo = QComboBox(self)
        self.polly_engine_combo.addItems(self.POLLY_ENGINE_OPTIONS)
        self.polly_engine_combo.currentIndexChanged.connect(
            self._handle_provider_changed
        )
        form_layout.addRow("Polly Engine", self.polly_engine_combo)

        self.rate_combo = QComboBox(self)
        self.rate_combo.addItems(self.RATE_OPTIONS)
        form_layout.addRow("Speech Rate", self.rate_combo)

        self.synthesis_volume_combo = QComboBox(self)
        self.synthesis_volume_combo.addItems(self.VOLUME_OPTIONS)
        form_layout.addRow("Speech Volume", self.synthesis_volume_combo)

        self.advanced_group = QCheckBox("Show advanced SSML controls", self)
        self.advanced_group.toggled.connect(self._toggle_advanced_controls)
        form_layout.addRow("", self.advanced_group)

        self.advanced_controls_widget = QWidget(self)
        advanced_layout = QFormLayout(self.advanced_controls_widget)

        self.emphasis_combo = QComboBox(self)
        self.emphasis_combo.addItems(self.EMPHASIS_OPTIONS)
        advanced_layout.addRow("Emphasis", self.emphasis_combo)

        self.pitch_combo = QComboBox(self)
        self.pitch_combo.addItems(self.PITCH_OPTIONS)
        advanced_layout.addRow("Pitch", self.pitch_combo)

        self.range_combo = QComboBox(self)
        self.range_combo.addItems(self.RANGE_OPTIONS)
        advanced_layout.addRow("Pitch Range", self.range_combo)

        self.pause_duration_combo = QComboBox(self)
        self.pause_duration_combo.addItems(self.PAUSE_OPTIONS)
        advanced_layout.addRow("Pause Duration", self.pause_duration_combo)

        self.pause_position_combo = QComboBox(self)
        self.pause_position_combo.addItems(self.PAUSE_POSITION_OPTIONS)
        advanced_layout.addRow("Pause Position", self.pause_position_combo)

        self.advanced_container = QLabel(self.advanced_controls_widget)
        self.advanced_container.setText(
            "Advanced controls shape the SSML preview and generated speech."
        )
        advanced_layout.addRow("", self.advanced_container)
        self.advanced_controls_widget.hide()
        form_layout.addRow("Advanced", self.advanced_controls_widget)

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
        form_layout.addRow("Provider Status", connection_row)

        main_layout.addLayout(form_layout)

    def _load_settings(self):
        self._set_provider(self.settings.tts_provider)
        self.azure_key_edit.setText(self.settings.azure_key)
        self.azure_region_edit.setText(self.settings.azure_region)
        self.polly_config_path_edit.setText(self.settings.polly_config_path)
        self.polly_engine_combo.setCurrentText(self.settings.polly_engine)
        self.rate_combo.setCurrentText(self.settings.speaking_rate)
        self.synthesis_volume_combo.setCurrentText(self.settings.synthesis_volume)
        self.emphasis_combo.setCurrentText(self.settings.emphasis_level)
        self.pitch_combo.setCurrentText(self.settings.pitch)
        self.range_combo.setCurrentText(self.settings.pitch_range)
        self.pause_duration_combo.setCurrentText(self.settings.pause_duration)
        self.pause_position_combo.setCurrentText(self.settings.pause_position)
        self.playback_volume_slider.setValue(self.settings.playback_volume)
        self.output_dir_edit.setText(self.settings.output_dir)
        self.auto_clean_checkbox.setChecked(self.settings.auto_clean_text)
        self.logging_checkbox.setChecked(self.settings.logging_enabled)
        show_advanced = any(
            (
                self.settings.emphasis_level != "none",
                self.settings.pitch != "default",
                self.settings.pitch_range != "default",
                self.settings.pause_duration != "none",
            )
        )
        self.advanced_group.setChecked(show_advanced)
        self._toggle_advanced_controls(show_advanced)
        self._update_playback_label(self.settings.playback_volume)
        self._refresh_voice_options(preferred_voice=self.settings.voice)
        self._refresh_provider_controls()

    def set_settings(self, settings):
        self.settings = AppSettings(**settings.__dict__)
        self._load_settings()

    def _set_provider(self, provider_name):
        provider_index = self.provider_combo.findData(provider_name)
        if provider_index == -1:
            provider_index = 0
        self.provider_combo.setCurrentIndex(provider_index)

    def _current_provider_name(self):
        return self.provider_combo.currentData() or "azure"

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

    def _choose_polly_config_file(self):
        chosen_file, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Amazon Polly Config File",
            str(Path.cwd()),
            "INI Files (*.ini *.env *.cfg);;All Files (*.*)",
        )
        if chosen_file:
            self.polly_config_path_edit.setText(chosen_file)

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

        if self._current_provider_name() == "polly":
            polly_config_path = self.polly_config_path_edit.text().strip()
            if not polly_config_path:
                QMessageBox.warning(
                    self,
                    "Missing Polly Config",
                    "Choose the dedicated Amazon Polly config file before applying settings.",
                )
                return None

        self.settings.tts_provider = self._current_provider_name()
        self.settings.voice = self.voice_combo.currentText().strip()
        self.settings.azure_key = self.azure_key_edit.text().strip()
        self.settings.azure_region = self.azure_region_edit.text().strip()
        self.settings.polly_config_path = (
            self.polly_config_path_edit.text().strip() or ".polly.env"
        )
        self.settings.polly_engine = self.polly_engine_combo.currentText()
        self.settings.speaking_rate = self.rate_combo.currentText()
        self.settings.synthesis_volume = (
            self.synthesis_volume_combo.currentText()
        )
        self.settings.emphasis_level = self.emphasis_combo.currentText()
        self.settings.pitch = self.pitch_combo.currentText()
        self.settings.pitch_range = self.range_combo.currentText()
        self.settings.pause_duration = self.pause_duration_combo.currentText()
        self.settings.pause_position = self.pause_position_combo.currentText()
        self.settings.playback_volume = self.playback_volume_slider.value()
        self.settings.output_dir = output_dir
        self.settings.auto_clean_text = self.auto_clean_checkbox.isChecked()
        self.settings.logging_enabled = self.logging_checkbox.isChecked()
        return self.settings

    def _handle_provider_changed(self):
        self._refresh_provider_controls()
        current_voice = self.voice_combo.currentText().strip()
        suggestions = set(get_voice_suggestions(self._current_provider_name()))
        preferred_voice = current_voice if current_voice in suggestions else ""
        self._refresh_voice_options(preferred_voice=preferred_voice)
        self.connection_status_label.setText("Not tested")

    def _refresh_provider_controls(self):
        using_azure = self._current_provider_name() == "azure"
        using_polly = self._current_provider_name() == "polly"

        self.azure_key_edit.setEnabled(using_azure)
        self.azure_region_edit.setEnabled(using_azure)
        self.polly_config_path_edit.setEnabled(using_polly)
        self.polly_config_browse_button.setEnabled(using_polly)
        self.polly_engine_combo.setEnabled(using_polly)
        self.test_connection_button.setText(
            f"Test {get_provider_display_name(self._current_provider_name())}"
        )

    def _refresh_voice_options(self, preferred_voice=""):
        suggestions = list(get_voice_suggestions(self._current_provider_name()))
        current_voice = preferred_voice.strip()
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        self.voice_combo.addItems(suggestions)
        if current_voice and current_voice not in suggestions:
            self.voice_combo.addItem(current_voice)
        if current_voice:
            self.voice_combo.setCurrentText(current_voice)
        elif suggestions:
            self.voice_combo.setCurrentText(suggestions[0])
        self.voice_combo.blockSignals(False)

    def _build_provider_config(self):
        provider_name = self._current_provider_name()
        if provider_name == "azure":
            azure_key = self.azure_key_edit.text().strip()
            azure_region = self.azure_region_edit.text().strip()
            if not azure_key or not azure_region:
                raise ValueError(
                    "Enter both the Azure key and region before testing the connection."
                )
            return TTSProviderConfig(
                provider_name="azure",
                credentials={
                    "subscription_key": azure_key,
                    "region": azure_region,
                },
            )

        polly_config_path = self.polly_config_path_edit.text().strip()
        if not polly_config_path:
            raise ValueError(
                "Choose the dedicated Amazon Polly config file before testing the connection."
            )

        from app.model.api.polly_config import get_polly_settings

        return TTSProviderConfig(
            provider_name="polly",
            credentials=get_polly_settings(polly_config_path),
            api_config_path=polly_config_path,
            options={"engine": self.polly_engine_combo.currentText()},
        )

    def _test_connection(self):
        provider_name = self._current_provider_name()
        provider_display_name = get_provider_display_name(provider_name)

        try:
            provider_config = self._build_provider_config()
            provider = create_tts_provider(provider_config)
            if provider_name == "polly":
                voices = provider.list_voices(
                    engine=self.polly_engine_combo.currentText()
                )
                if voices:
                    self._refresh_voice_options(
                        preferred_voice=self.voice_combo.currentText()
                    )
                    current_voice = self.voice_combo.currentText().strip()
                    self.voice_combo.clear()
                    self.voice_combo.addItems(list(voices))
                    if current_voice and current_voice not in voices:
                        self.voice_combo.addItem(current_voice)
                    self.voice_combo.setCurrentText(current_voice or voices[0])

            voice_name = self.voice_combo.currentText().strip()
            audio_data = provider.synthesize(
                TTSRequest(
                    text="Connection test.",
                    voice=voice_name or None,
                    metadata={
                        "engine": self.polly_engine_combo.currentText(),
                    },
                )
            ).audio_data
        except Exception as error:
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"Unable to validate the {provider_display_name} configuration.\n\n{error}",
            )
            self.connection_status_label.setText("Connection failed")
            return

        if audio_data:
            self.connection_status_label.setText("Connection OK")
            QMessageBox.information(
                self,
                "Connection Successful",
                f"{provider_display_name} settings are valid.",
            )
        else:
            self.connection_status_label.setText("No audio returned")

    def _toggle_advanced_controls(self, enabled):
        self.advanced_controls_widget.setVisible(enabled)


class SettingsDialog(QDialog):
    """
    Modal dialog for editing application settings.
    """

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.editor = SettingsEditor(settings, self)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.editor)

        button_row = QHBoxLayout()
        self.save_button = QPushButton("Save", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.save_button.clicked.connect(self._accept_if_valid)
        self.cancel_button.clicked.connect(self.reject)
        button_row.addStretch(1)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.cancel_button)
        main_layout.addLayout(button_row)

    def get_settings(self):
        return self.editor.get_settings()

    def _accept_if_valid(self):
        if self.get_settings() is not None:
            self.accept()
