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
        self.current_row = 0

    def clear(self):
        self.items.clear()

    def addItem(self, item):
        self.items.append(item)

    def currentItem(self):
        if 0 <= self.current_row < len(self.items):
            return self.items[self.current_row]
        return None

    def currentRow(self):
        return self.current_row


class StatusBarStub:
    def __init__(self):
        self.message = ""

    def showMessage(self, message):
        self.message = message


class TextEditStub:
    def __init__(self):
        self.text = ""

    def setPlainText(self, text):
        self.text = text


class ViewStub:
    def __init__(self):
        self.historyList = HistoryListStub()
        self.statusbar = StatusBarStub()
        self.textEdit = TextEditStub()


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

            controller._record_audio_history(
                audio_path,
                "export",
                source_text="Unique history source text.",
            )

            self.assertEqual(len(controller.audio_history), 1)
            self.assertEqual(controller.audio_history[0]["filename"], "sample.mp3")
            self.assertEqual(controller.audio_history[0]["voice"], "en-US-GuyNeural")
            self.assertEqual(
                controller.audio_history[0]["source_text"],
                "Unique history source text.",
            )
            self.assertEqual(
                controller.audio_history[0]["settings"]["voice"],
                "en-US-GuyNeural",
            )
            self.assertIn("Export", controller.view.historyList.items[0].text())

            saved_history = json.loads(
                controller.AUDIO_HISTORY_PATH.read_text(encoding="utf-8")
            )
            self.assertEqual(saved_history[0]["filename"], "sample.mp3")
            self.assertEqual(saved_history[0]["output_path"], str(audio_path.resolve()))
            self.assertEqual(
                saved_history[0]["source_text"],
                "Unique history source text.",
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_restore_selected_history_context_reuses_text_and_settings(self):
        temp_dir = Path("data/dynamic/tmp/history_restore_test")
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        try:
            controller = MainController.__new__(MainController)
            controller.settings = AppSettings(
                voice="en-US-GuyNeural",
                speaking_rate="medium",
            )
            controller.view = ViewStub()
            controller.AUDIO_HISTORY_PATH = temp_dir / "audio_history.json"
            controller.SETTINGS_PATH = temp_dir / "app_settings.json"
            controller.tts_processor = object()
            controller.audio_history = [
                {
                    "filename": "sample.mp3",
                    "output_path": str(temp_dir / "sample.mp3"),
                    "voice": "en-US-JennyNeural",
                    "generated_at": "20260427010101",
                    "source": "export",
                    "source_text": "Restore this narration text.",
                    "settings": {
                        "voice": "en-US-JennyNeural",
                        "speaking_rate": "slow",
                    },
                }
            ]
            controller._refresh_ui_state = lambda: None
            controller.update_ssml_preview = lambda: None
            controller._refresh_history_panel()

            controller.restore_selected_history_context()

            self.assertEqual(controller.view.textEdit.text, "Restore this narration text.")
            self.assertEqual(controller.settings.voice, "en-US-JennyNeural")
            self.assertEqual(controller.settings.speaking_rate, "slow")
            self.assertIsNone(controller.tts_processor)
            self.assertEqual(
                controller.view.statusbar.message,
                "Restored history text and settings.",
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
