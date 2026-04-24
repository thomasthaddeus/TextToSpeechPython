import unittest
import sys
import types

speechsdk = types.SimpleNamespace(
    SpeechConfig=object,
    SpeechSynthesisOutputFormat=types.SimpleNamespace(
        Audio16Khz32KBitRateMonoMp3="Audio16Khz32KBitRateMonoMp3"
    ),
    SpeechSynthesizer=object,
)
azure_module = types.ModuleType("azure")
cognitiveservices_module = types.ModuleType("azure.cognitiveservices")
speech_module = types.ModuleType("azure.cognitiveservices.speech")
speech_module.SpeechConfig = speechsdk.SpeechConfig
speech_module.SpeechSynthesisOutputFormat = (
    speechsdk.SpeechSynthesisOutputFormat
)
speech_module.SpeechSynthesizer = speechsdk.SpeechSynthesizer

sys.modules.setdefault("azure", azure_module)
sys.modules.setdefault("azure.cognitiveservices", cognitiveservices_module)
sys.modules.setdefault("azure.cognitiveservices.speech", speech_module)

from app.controller.main_controller import MainController
from app.model.app_settings import AppSettings
from app.utils.text_cleaner import TextCleaner


class MainControllerSSMLTests(unittest.TestCase):
    def _controller(self, auto_clean_text=False, **overrides):
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

    def test_build_ssml_escapes_xml_characters(self):
        controller = self._controller()

        ssml = controller._build_ssml('Fish & Chips <tag> "quoted" > done')

        self.assertIn("Fish &amp; Chips", ssml)
        self.assertIn("&lt;tag&gt;", ssml)
        self.assertIn('"quoted"', ssml)
        self.assertIn("&gt; done", ssml)

    def test_build_ssml_escapes_cleaned_text(self):
        controller = self._controller(auto_clean_text=True)

        ssml = controller._build_ssml("it's <b>great</b> & bright")

        self.assertIn("it is", ssml)
        self.assertIn("great", ssml)
        self.assertNotIn("<b>", ssml)
        self.assertIn("&amp; bright", ssml)

    def test_build_ssml_includes_advanced_controls(self):
        controller = self._controller(
            emphasis_level="strong",
            pitch="high",
            pitch_range="low",
            pause_duration="500ms",
            pause_position="before",
        )

        ssml = controller._build_ssml("Speak now")

        self.assertIn('pitch="high"', ssml)
        self.assertIn('range="low"', ssml)
        self.assertIn('<emphasis level="strong">', ssml)
        self.assertIn('<break time="500ms"/>Speak now', ssml)


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


class LabelStub:
    def __init__(self):
        self.text = ""

    def setText(self, value):
        self.text = value


class ActionStateViewStub:
    def __init__(self, text):
        self.textEdit = TextEditStub(text)
        self.previewButton = ToggleStub()
        self.cleanTextButton = ToggleStub()
        self.playButton = ToggleStub()
        self.generateButton = ToggleStub()
        self.actionExportAudio = ToggleStub()
        self.stopButton = ToggleStub()
        self.playbackVolumeSlider = ToggleStub()
        self.actionHintLabel = LabelStub()


class MainControllerActionStateTests(unittest.TestCase):
    def test_refresh_action_states_disables_generation_without_text(self):
        controller = MainController.__new__(MainController)
        controller.settings = AppSettings()
        controller.view = ActionStateViewStub("")
        controller.media_player = object()
        controller.audio_output = object()
        controller.preview_audio_path = None

        controller._refresh_action_states()

        self.assertFalse(controller.view.previewButton.enabled)
        self.assertFalse(controller.view.playButton.enabled)
        self.assertFalse(controller.view.generateButton.enabled)
        self.assertFalse(controller.view.actionExportAudio.enabled)
        self.assertIn("Type or import text", controller.view.actionHintLabel.text)

    def test_refresh_action_states_relabels_preview_when_multimedia_unavailable(self):
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

        self.assertTrue(controller.view.playButton.enabled)
        self.assertEqual(controller.view.playButton.text, "Generate Preview File")
        self.assertFalse(controller.view.stopButton.enabled)
        self.assertFalse(controller.view.playbackVolumeSlider.enabled)
        self.assertIn("playback controls are disabled", controller.view.actionHintLabel.text)


if __name__ == "__main__":
    unittest.main()
