from app.gui.settings_dialog import SettingsEditor
from app.model.app_settings import AppSettings


def test_settings_editor_switches_provider_specific_controls(qt_app):
    del qt_app
    editor = SettingsEditor(AppSettings(tts_provider="azure"))

    editor.provider_combo.setCurrentIndex(editor.provider_combo.findData("gemini"))

    assert editor.voice_combo.isEnabled()
    assert not editor.gemini_model_edit.isHidden()
    assert not editor.gemini_language_code_edit.isHidden()
    assert not editor.gemini_style_prompt_edit.isHidden()
    assert editor.polly_engine_combo.isHidden()
    assert editor.advanced_group.isHidden()
    assert "plain-text synthesis" in editor.provider_help_label.text()


def test_settings_editor_persists_provider_specific_values(qt_app):
    del qt_app
    editor = SettingsEditor(AppSettings(output_dir="data/dynamic/audio"))

    editor.provider_combo.setCurrentIndex(editor.provider_combo.findData("polly"))
    editor.voice_combo.setCurrentText("Joanna")
    editor.provider_config_edit.setText(".polly.env")
    editor.polly_engine_combo.setCurrentText("standard")
    editor.output_dir_edit.setText("data/dynamic/audio")

    updated_settings = editor.get_settings()

    assert updated_settings.tts_provider == "polly"
    assert updated_settings.voice == "Joanna"
    assert updated_settings.polly_config_path == ".polly.env"
    assert updated_settings.polly_engine == "standard"


def test_settings_editor_preserves_provider_values_while_switching(qt_app):
    del qt_app
    editor = SettingsEditor(AppSettings(output_dir="data/dynamic/audio"))

    editor.provider_combo.setCurrentIndex(editor.provider_combo.findData("polly"))
    editor.provider_config_edit.setText("custom-polly.env")
    editor.polly_engine_combo.setCurrentText("standard")

    editor.provider_combo.setCurrentIndex(editor.provider_combo.findData("gemini"))
    editor.provider_config_edit.setText("custom-gemini.env")
    editor.gemini_model_edit.setText("gemini-2.5-pro-tts")
    editor.gemini_style_prompt_edit.setPlainText("Narrate with gentle pacing.")

    editor.provider_combo.setCurrentIndex(editor.provider_combo.findData("polly"))

    assert editor.provider_config_edit.text() == "custom-polly.env"
    assert editor.polly_engine_combo.currentText() == "standard"

    editor.provider_combo.setCurrentIndex(editor.provider_combo.findData("gemini"))
    updated_settings = editor.get_settings()

    assert updated_settings.gemini_config_path == "custom-gemini.env"
    assert updated_settings.gemini_model == "gemini-2.5-pro-tts"
    assert updated_settings.gemini_style_prompt == "Narrate with gentle pacing."
    assert updated_settings.polly_config_path == "custom-polly.env"
    assert updated_settings.polly_engine == "standard"
