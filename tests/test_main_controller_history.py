import json
import shutil
import sys
import types
import unittest
from pathlib import Path

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


class HistoryListStub:
    def __init__(self):
        self.items = []

    def clear(self):
        self.items.clear()

    def addItem(self, text):
        self.items.append(text)


class ViewStub:
    def __init__(self):
        self.historyList = HistoryListStub()


class MainControllerHistoryTests(unittest.TestCase):
    def test_record_audio_history_persists_and_updates_view(self):
        temp_dir = Path("data/dynamic/tmp/history_test_artifacts")
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        try:
            audio_path = temp_dir / "sample.mp3"
            audio_path.write_bytes(b"audio")

            controller = MainController.__new__(MainController)
            controller.settings = AppSettings(voice="en-US-GuyNeural")
            controller.view = ViewStub()
            controller.audio_history = []
            controller.AUDIO_HISTORY_PATH = temp_dir / "audio_history.json"
            controller.MAX_HISTORY_ITEMS = 3

            controller._record_audio_history(audio_path, "export")

            self.assertEqual(len(controller.audio_history), 1)
            self.assertEqual(controller.audio_history[0]["filename"], "sample.mp3")
            self.assertEqual(controller.audio_history[0]["voice"], "en-US-GuyNeural")
            self.assertIn("Export", controller.view.historyList.items[0])

            saved_history = json.loads(
                controller.AUDIO_HISTORY_PATH.read_text(encoding="utf-8")
            )
            self.assertEqual(saved_history[0]["filename"], "sample.mp3")
            self.assertEqual(saved_history[0]["output_path"], str(audio_path.resolve()))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
