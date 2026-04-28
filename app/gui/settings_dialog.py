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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.model.api.azure_tts_api import AzureTTSAPI
from app.model.app_settings import AppSettings
from app.model.ssml.ssml_config import SSMLConfig
from app.model.tts_providers import (
    get_provider_display_name,
    get_provider_profile,
    get_voice_suggestions,
    list_provider_profiles,
    resolve_tts_provider_config,
)


class SettingsEditor(QWidget):
    """Reusable settings editor used by both the modal dialog and main sidebar."""

    RATE_OPTIONS = ["x-slow", "slow", "medium", "fast", "x-fast"]
    VOLUME_OPTIONS = ["silent", "x-soft", "soft", "medium", "loud", "x-loud"]
    EMPHASIS_OPTIONS = ["none", "reduced", "moderate", "strong"]
    PITCH_OPTIONS = ["default", "x-low", "low", "medium", "high", "x-high"]
    RANGE_OPTIONS = ["default", "x-low", "low", "medium", "high", "x-high"]
    PAUSE_OPTIONS = ["none", "250ms", "500ms", "1s", "2s"]
    PAUSE_POSITION_OPTIONS = ["before", "after"]

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = AppSettings(**settings.__dict__)
        self.voice_config = SSMLConfig()
        self._loading_settings = False
        self._active_provider_id = self.settings.tts_provider or "azure"
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.form_layout = form_layout

        self.provider_combo = QComboBox(self)
        for profile in list_provider_profiles():
            self.provider_combo.addItem(profile.display_name, profile.provider_id)
        self.provider_combo.currentIndexChanged.connect(
            self._handle_provider_changed
        )
        form_layout.addRow("Provider", self.provider_combo)

        self.provider_help_label = QLabel(self)
        self.provider_help_label.setWordWrap(True)
        self.provider_help_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        form_layout.addRow("", self.provider_help_label)

        self.voice_combo = QComboBox(self)
        self.voice_combo.setEditable(True)
        self.voice_combo.addItems(self.voice_config.list_voices())
        form_layout.addRow("Voice", self.voice_combo)

        self.azure_key_edit = QLineEdit(self)
        self.azure_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Azure Key", self.azure_key_edit)

        self.azure_region_edit = QLineEdit(self)
        self.azure_region_edit.setPlaceholderText("eastus")
        form_layout.addRow("Azure Region", self.azure_region_edit)

        self.provider_config_label = QLabel("Provider Config", self)
        provider_config_row = QWidget(self)
        provider_config_layout = QHBoxLayout(provider_config_row)
        provider_config_layout.setContentsMargins(0, 0, 0, 0)
        self.provider_config_edit = QLineEdit(self)
        self.provider_config_browse_button = QPushButton("Browse", self)
        self.provider_config_browse_button.clicked.connect(
            self._choose_provider_config_file
        )
        provider_config_layout.addWidget(self.provider_config_edit)
        provider_config_layout.addWidget(self.provider_config_browse_button)
        self.provider_config_row = provider_config_row
        form_layout.addRow(self.provider_config_label, provider_config_row)

        self.provider_config_help = QLabel(self)
        self.provider_config_help.setWordWrap(True)
        form_layout.addRow("", self.provider_config_help)

        self.gemini_model_edit = QLineEdit(self)
        form_layout.addRow("Gemini Model", self.gemini_model_edit)

        self.gemini_language_code_edit = QLineEdit(self)
        self.gemini_language_code_edit.setPlaceholderText("en-US")
        form_layout.addRow("Gemini Language", self.gemini_language_code_edit)

        self.gemini_style_prompt_edit = QTextEdit(self)
        self.gemini_style_prompt_edit.setFixedHeight(72)
        self.gemini_style_prompt_edit.setPlaceholderText(
            "Warm, conversational, and concise."
        )
        form_layout.addRow("Style Prompt", self.gemini_style_prompt_edit)

        self.rate_combo = QComboBox(self)
        self.rate_combo.addItems(self.RATE_OPTIONS)
        form_layout.addRow("Speech Rate", self.rate_combo)

        self.synthesis_volume_combo = QComboBox(self)
        self.synthesis_volume_combo.addItems(self.VOLUME_OPTIONS)
        form_layout.addRow("Speech Volume", self.synthesis_volume_combo)

        self.polly_engine_combo = QComboBox(self)
        self.polly_engine_combo.addItems(["neural", "standard"])
        form_layout.addRow("Polly Engine", self.polly_engine_combo)

        self.local_driver_name_edit = QLineEdit(self)
        self.local_driver_name_edit.setPlaceholderText("auto")
        form_layout.addRow("Local Driver", self.local_driver_name_edit)

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
        self.advanced_container.setWordWrap(True)
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

    def _selected_provider_id(self):
        return self.provider_combo.currentData() or "azure"

    def _selected_provider_profile(self):
        return get_provider_profile(self._selected_provider_id())

    def _set_form_row_visible(self, field, visible):
        label = self.form_layout.labelForField(field)
        if label is not None:
            label.setVisible(visible)
        field.setVisible(visible)

    def _sync_voice_suggestions(self, provider_id):
        current_voice = self.voice_combo.currentText().strip()
        suggestions = list(get_voice_suggestions(provider_id))
        if not suggestions:
            suggestions = self.voice_config.list_voices()

        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        self.voice_combo.addItems(suggestions)
        if current_voice and self.voice_combo.findText(current_voice) == -1:
            self.voice_combo.addItem(current_voice)
        if current_voice:
            self.voice_combo.setCurrentText(current_voice)
        self.voice_combo.blockSignals(False)

    def _provider_config_value(self, provider_id):
        provider_fields = {
            "polly": self.settings.polly_config_path,
            "gemini": self.settings.gemini_config_path,
            "local": self.settings.local_tts_config_path,
        }
        return provider_fields.get(provider_id, "")

    def _set_provider_config_value(self, provider_id, value):
        if provider_id == "polly":
            self.settings.polly_config_path = value
        elif provider_id == "gemini":
            self.settings.gemini_config_path = value
        elif provider_id == "local":
            self.settings.local_tts_config_path = value

    def _persist_provider_specific_fields(self, provider_id):
        if provider_id in {"polly", "gemini", "local"}:
            self._set_provider_config_value(
                provider_id,
                self.provider_config_edit.text().strip(),
            )

        if provider_id == "gemini":
            self.settings.gemini_model = self.gemini_model_edit.text().strip()
            self.settings.gemini_language_code = (
                self.gemini_language_code_edit.text().strip() or "en-US"
            )
            self.settings.gemini_style_prompt = (
                self.gemini_style_prompt_edit.toPlainText().strip()
            )
        elif provider_id == "polly":
            self.settings.polly_engine = self.polly_engine_combo.currentText()
        elif provider_id == "local":
            self.settings.local_tts_driver_name = (
                self.local_driver_name_edit.text().strip() or "auto"
            )

    def _apply_provider_profile(self):
        profile = self._selected_provider_profile()
        capability_summary = [
            "SSML preview" if profile.supports_ssml else "plain-text synthesis",
        ]
        if profile.supports_advanced_ssml:
            capability_summary.append("advanced SSML controls")
        if profile.supports_style_prompt:
            capability_summary.append("style prompts")
        if profile.provider_id == "local":
            capability_summary.append("offline playback engine")
        self.provider_help_label.setText(
            "\n".join(
                (
                    profile.description,
                    "Capabilities: " + ", ".join(capability_summary),
                )
            )
        )
        self._sync_voice_suggestions(profile.provider_id)

        supports_voices = profile.supports_voice_selection
        self.voice_combo.setEnabled(supports_voices)
        if supports_voices:
            self.voice_combo.setToolTip("Voice selection is available for this provider.")
        else:
            self.voice_combo.setToolTip(
                "This provider uses its own runtime voice selection workflow."
            )

        is_azure = profile.provider_id == "azure"
        self._set_form_row_visible(self.azure_key_edit, is_azure)
        self._set_form_row_visible(self.azure_region_edit, is_azure)

        uses_config_file = profile.provider_id in {"polly", "gemini", "local"}
        self.provider_config_label.setVisible(uses_config_file)
        self.provider_config_row.setVisible(uses_config_file)
        self.provider_config_help.setVisible(uses_config_file)
        if uses_config_file:
            self.provider_config_label.setText(profile.config_label)
            self.provider_config_edit.setPlaceholderText(profile.config_placeholder)
            self.provider_config_edit.setText(
                self._provider_config_value(profile.provider_id)
            )
            self.provider_config_help.setText(profile.config_help)

        is_gemini = profile.provider_id == "gemini"
        self._set_form_row_visible(self.gemini_model_edit, is_gemini)
        self._set_form_row_visible(self.gemini_language_code_edit, is_gemini)
        self._set_form_row_visible(
            self.gemini_style_prompt_edit,
            profile.supports_style_prompt,
        )
        self._set_form_row_visible(self.polly_engine_combo, profile.provider_id == "polly")
        self._set_form_row_visible(
            self.local_driver_name_edit,
            profile.provider_id == "local",
        )

        supports_advanced = profile.supports_advanced_ssml
        self.advanced_group.setVisible(supports_advanced)
        if not supports_advanced:
            self.advanced_group.setChecked(False)
            self._toggle_advanced_controls(False)

        if profile.supports_connection_test:
            self.test_connection_button.setText("Test Connection")
            self.test_connection_button.setEnabled(True)
        else:
            self.test_connection_button.setText(
                f"Validate {get_provider_display_name(profile.provider_id)}"
            )
            self.test_connection_button.setEnabled(True)

        self.connection_status_label.setText("Not tested")

    def _handle_provider_changed(self):
        if not self._loading_settings:
            self._persist_provider_specific_fields(self._active_provider_id)
        self._active_provider_id = self._selected_provider_id()
        self._apply_provider_profile()

    def _load_settings(self):
        self._loading_settings = True
        self.provider_combo.blockSignals(True)
        self.provider_combo.setCurrentIndex(
            max(0, self.provider_combo.findData(self.settings.tts_provider))
        )
        self.provider_combo.blockSignals(False)
        self.voice_combo.setCurrentText(self.settings.voice)
        self.azure_key_edit.setText(self.settings.azure_key)
        self.azure_region_edit.setText(self.settings.azure_region)
        self.gemini_model_edit.setText(self.settings.gemini_model)
        self.gemini_language_code_edit.setText(self.settings.gemini_language_code)
        self.gemini_style_prompt_edit.setPlainText(
            self.settings.gemini_style_prompt
        )
        self.polly_engine_combo.setCurrentText(self.settings.polly_engine)
        self.local_driver_name_edit.setText(self.settings.local_tts_driver_name)
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
        self._loading_settings = False
        self._active_provider_id = self._selected_provider_id()
        self._apply_provider_profile()

    def set_settings(self, settings):
        self.settings = AppSettings(**settings.__dict__)
        self._load_settings()

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

    def _choose_provider_config_file(self):
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Provider Config File",
            str(Path.cwd()),
            "Config Files (*.env *.ini *.json *.toml *.yaml *.yml);;All Files (*)",
        )
        if selected_file:
            self.provider_config_edit.setText(selected_file)

    def get_settings(self):
        """Build a validated settings object from the dialog state."""
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(
                self,
                "Missing Output Directory",
                "Choose a directory for generated audio files.",
            )
            return None

        provider_id = self._selected_provider_id()
        self.settings.tts_provider = provider_id
        self.settings.voice = self.voice_combo.currentText()
        self.settings.azure_key = self.azure_key_edit.text().strip()
        self.settings.azure_region = self.azure_region_edit.text().strip()
        self.settings.gemini_model = self.gemini_model_edit.text().strip()
        self.settings.gemini_language_code = (
            self.gemini_language_code_edit.text().strip() or "en-US"
        )
        self.settings.gemini_style_prompt = (
            self.gemini_style_prompt_edit.toPlainText().strip()
        )
        self.settings.polly_engine = self.polly_engine_combo.currentText()
        self.settings.local_tts_driver_name = (
            self.local_driver_name_edit.text().strip() or "auto"
        )
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
        self._persist_provider_specific_fields(provider_id)
        return self.settings

    def _test_connection(self):
        profile = self._selected_provider_profile()
        if profile.provider_id == "azure":
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
            return

        provider_settings = AppSettings(**self.settings.__dict__)
        provider_settings.tts_provider = profile.provider_id
        provider_settings.voice = self.voice_combo.currentText()
        provider_settings.azure_key = self.azure_key_edit.text().strip()
        provider_settings.azure_region = self.azure_region_edit.text().strip()
        provider_settings.gemini_model = self.gemini_model_edit.text().strip()
        provider_settings.gemini_language_code = (
            self.gemini_language_code_edit.text().strip() or "en-US"
        )
        provider_settings.gemini_style_prompt = (
            self.gemini_style_prompt_edit.toPlainText().strip()
        )
        provider_settings.polly_engine = self.polly_engine_combo.currentText()
        provider_settings.local_tts_driver_name = (
            self.local_driver_name_edit.text().strip() or "auto"
        )
        if profile.provider_id == "polly":
            provider_settings.polly_config_path = (
                self.provider_config_edit.text().strip()
            )
        elif profile.provider_id == "gemini":
            provider_settings.gemini_config_path = (
                self.provider_config_edit.text().strip()
            )
        elif profile.provider_id == "local":
            provider_settings.local_tts_config_path = (
                self.provider_config_edit.text().strip()
            )

        provider_config = resolve_tts_provider_config(provider_settings, ".env")
        if provider_config is None:
            QMessageBox.warning(
                self,
                f"{profile.display_name} Setup Required",
                (
                    f"The application could not resolve a valid {profile.display_name} "
                    "configuration from the current settings."
                ),
            )
            self.connection_status_label.setText("Configuration failed")
            return

        self.connection_status_label.setText("Configuration OK")
        QMessageBox.information(
            self,
            f"{profile.display_name} Ready",
            f"{profile.display_name} settings resolved successfully.",
        )

    def _toggle_advanced_controls(self, enabled):
        self.advanced_controls_widget.setVisible(
            enabled and self._selected_provider_profile().supports_advanced_ssml
        )


class SettingsDialog(QDialog):
    """Modal dialog for editing application settings."""

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
