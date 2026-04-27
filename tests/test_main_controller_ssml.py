import pytest

from app.controller.main_controller import MainController
from app.model.app_settings import AppSettings
from app.utils.text_cleaner import TextCleaner


@pytest.fixture
def controller_factory():
    def build_controller(auto_clean_text=False, **overrides):
        controller = MainController.__new__(MainController)
        controller.settings = AppSettings(
            voice="en-US-GuyNeural",
            speaking_rate="medium",
            synthesis_volume="medium",
            auto_clean_text=auto_clean_text,
            **overrides,
        )
        controller.cleaner = TextCleaner()
        return controller

    return build_controller


def test_build_ssml_escapes_xml_characters(controller_factory):
    controller = controller_factory()

    ssml = controller._build_ssml('Fish & Chips <tag> "quoted" > done')

    assert "Fish &amp; Chips" in ssml
    assert "&lt;tag&gt;" in ssml
    assert '"quoted"' in ssml
    assert "&gt; done" in ssml


def test_build_ssml_escapes_cleaned_text(controller_factory):
    controller = controller_factory(auto_clean_text=True)

    ssml = controller._build_ssml("it's <b>great</b> & bright")

    assert "it is" in ssml
    assert "great" in ssml
    assert "<b>" not in ssml
    assert "&amp; bright" in ssml


def test_build_ssml_includes_advanced_controls(controller_factory):
    controller = controller_factory(
        emphasis_level="strong",
        pitch="high",
        pitch_range="low",
        pause_duration="500ms",
        pause_position="before",
    )

    ssml = controller._build_ssml("Speak now")

    assert 'pitch="high"' in ssml
    assert 'range="low"' in ssml
    assert '<emphasis level="strong">' in ssml
    assert '<break time="500ms"/>Speak now' in ssml


class ToggleStub:
    def __init__(self):
        self.enabled = True
        self.text = ""
        self.tooltip = ""

    def setEnabled(self, value):
        self.enabled = value

    def setText(self, value):
        self.text = value

    def setToolTip(self, value):
        self.tooltip = value


class TextEditStub:
    def __init__(self, text):
        self._text = text

    def toPlainText(self):
        return self._text

    def setPlainText(self, text):
        self._text = text


class LabelStub:
    def __init__(self):
        self.text = ""

    def setText(self, value):
        self.text = value


class StatusBarStub:
    def __init__(self):
        self.message = ""

    def showMessage(self, message):
        self.message = message


class ActionStateViewStub:
    def __init__(self, text):
        self.textEdit = TextEditStub(text)
        self.previewButton = ToggleStub()
        self.cleanTextButton = ToggleStub()
        self.playButton = ToggleStub()
        self.generateButton = ToggleStub()
        self.actionExportAudio = ToggleStub()
        self.stopButton = ToggleStub()
        self.cancelTaskButton = ToggleStub()
        self.openSecondWindowButton = ToggleStub()
        self.playbackVolumeSlider = ToggleStub()
        self.actionHintLabel = LabelStub()


class SaveExportViewStub:
    def __init__(self, text):
        self.textEdit = TextEditStub(text)
        self.statusbar = StatusBarStub()


def test_refresh_action_states_disables_generation_without_text():
    controller = MainController.__new__(MainController)
    controller.settings = AppSettings()
    controller.view = ActionStateViewStub("")
    controller.media_player = object()
    controller.audio_output = object()
    controller.preview_audio_path = None

    controller._refresh_action_states()

    assert not controller.view.previewButton.enabled
    assert not controller.view.playButton.enabled
    assert not controller.view.generateButton.enabled
    assert not controller.view.actionExportAudio.enabled
    assert "Type or import text" in controller.view.actionHintLabel.text


def test_refresh_action_states_enables_cancel_during_background_work():
    controller = MainController.__new__(MainController)
    controller.settings = AppSettings()
    controller.view = ActionStateViewStub("Hello world")
    controller.media_player = object()
    controller.audio_output = object()
    controller.preview_audio_path = None
    controller.batch_export_active = True
    controller.document_parse_thread = None

    controller._refresh_action_states()

    assert controller.view.cancelTaskButton.enabled
    assert not controller.view.generateButton.enabled
    assert not controller.view.openSecondWindowButton.enabled
    assert "Cancel Task" in controller.view.actionHintLabel.text


def test_refresh_action_states_relabels_preview_when_multimedia_unavailable():
    controller = MainController.__new__(MainController)
    controller.settings = AppSettings(
        emphasis_level="moderate",
        pitch="high",
    )
    controller.view = ActionStateViewStub("Hello world")
    controller.media_player = None
    controller.audio_output = None
    controller.preview_audio_path = None

    controller._refresh_action_states()

    assert controller.view.playButton.enabled
    assert controller.view.playButton.text == "Generate Preview File"
    assert not controller.view.stopButton.enabled
    assert not controller.view.playbackVolumeSlider.enabled
    assert "playback controls are disabled" in controller.view.actionHintLabel.text


def test_export_editor_text_exports_html_without_round_tripping_source_document(
    runtime_tmp_path, monkeypatch
):
    output_path = runtime_tmp_path / "editor_export.html"
    controller = MainController.__new__(MainController)
    controller.view = SaveExportViewStub("Fish & Chips\n<tag>")
    monkeypatch.setattr(
        "app.controller.main_controller.QFileDialog.getSaveFileName",
        lambda *_args, **_kwargs: (str(output_path), "HTML Files (*.html)"),
    )

    controller.export_editor_text()

    exported_text = output_path.read_text(encoding="utf-8")
    assert "Fish &amp; Chips" in exported_text
    assert "&lt;tag&gt;" in exported_text
    assert "Exported editor text" in controller.view.statusbar.message
    assert "not round-tripped" in controller.view.statusbar.message
