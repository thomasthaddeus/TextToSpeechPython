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
    def _controller(self, auto_clean_text=False):
        controller = MainController.__new__(MainController)
        controller.settings = AppSettings(
            voice="en-US-GuyNeural",
            speaking_rate="medium",
            synthesis_volume="medium",
            auto_clean_text=auto_clean_text,
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


if __name__ == "__main__":
    unittest.main()
