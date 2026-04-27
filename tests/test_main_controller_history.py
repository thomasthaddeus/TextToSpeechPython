import json

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


def test_record_audio_history_persists_and_updates_view(runtime_tmp_path):
    audio_path = runtime_tmp_path / "sample.mp3"
    audio_path.write_bytes(b"audio")
    controller = MainController.__new__(MainController)
    controller.settings = AppSettings(voice="en-US-GuyNeural")
    controller.view = ViewStub()
    controller.audio_history = []
    controller.AUDIO_HISTORY_PATH = runtime_tmp_path / "audio_history.json"
    controller.MAX_HISTORY_ITEMS = 3

    controller._record_audio_history(
        audio_path,
        "export",
        source_text="Unique history source text.",
    )

    assert len(controller.audio_history) == 1
    assert controller.audio_history[0]["filename"] == "sample.mp3"
    assert controller.audio_history[0]["voice"] == "en-US-GuyNeural"
    assert controller.audio_history[0]["source_text"] == "Unique history source text."
    assert controller.audio_history[0]["settings"]["voice"] == "en-US-GuyNeural"
    assert "Export" in controller.view.historyList.items[0].text()

    saved_history = json.loads(
        controller.AUDIO_HISTORY_PATH.read_text(encoding="utf-8")
    )
    assert saved_history[0]["filename"] == "sample.mp3"
    assert saved_history[0]["output_path"] == str(audio_path.resolve())
    assert saved_history[0]["source_text"] == "Unique history source text."


def test_restore_selected_history_context_reuses_text_and_settings(runtime_tmp_path):
    controller = MainController.__new__(MainController)
    controller.settings = AppSettings(
        voice="en-US-GuyNeural",
        speaking_rate="medium",
    )
    controller.view = ViewStub()
    controller.AUDIO_HISTORY_PATH = runtime_tmp_path / "audio_history.json"
    controller.SETTINGS_PATH = runtime_tmp_path / "app_settings.json"
    controller.tts_processor = object()
    controller.audio_history = [
        {
            "filename": "sample.mp3",
            "output_path": str(runtime_tmp_path / "sample.mp3"),
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

    assert controller.view.textEdit.text == "Restore this narration text."
    assert controller.settings.voice == "en-US-JennyNeural"
    assert controller.settings.speaking_rate == "slow"
    assert controller.tts_processor is None
    assert controller.view.statusbar.message == "Restored history text and settings."
