import shutil
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

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
speech_module.SpeechSynthesisOutputFormat = speechsdk.SpeechSynthesisOutputFormat
speech_module.SpeechSynthesizer = speechsdk.SpeechSynthesizer

sys.modules.setdefault("azure", azure_module)
sys.modules.setdefault("azure.cognitiveservices", cognitiveservices_module)
sys.modules.setdefault("azure.cognitiveservices.speech", speech_module)

from app.controller.background_workers import BatchExportWorker
from app.model.app_settings import AppSettings


class FakeTTSProcessor:
    def __init__(self, azure_key, azure_region):
        self.azure_key = azure_key
        self.azure_region = azure_region

    def text_to_speech(self, text, use_ssml=False):
        return f"audio:{use_ssml}:{text}".encode("utf-8")


class BackgroundWorkerTests(unittest.TestCase):
    def test_batch_export_worker_writes_files_and_reports_progress(self):
        temp_dir = Path("data/dynamic/tmp/batch_worker_test")
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        rows = [
            {
                "item_number": 1,
                "title": "Opening Notes",
                "content_mode": "combine",
                "resolved_text": "Unique batch worker sample text.",
            }
        ]
        finished = []
        failed = []
        progress = []

        try:
            worker = BatchExportWorker(
                rows=rows,
                output_dir=temp_dir,
                settings=AppSettings(auto_clean_text=False),
                azure_key="fake-key",
                azure_region="fake-region",
            )
            worker.finished.connect(finished.append)
            worker.failed.connect(lambda message, files: failed.append((message, files)))
            worker.progress.connect(
                lambda completed, total, path: progress.append(
                    (completed, total, Path(path).name)
                )
            )

            with patch(
                "app.controller.background_workers.create_tts_processor",
                lambda azure_key, azure_region: FakeTTSProcessor(
                    azure_key,
                    azure_region,
                ),
            ):
                worker.run()

            self.assertFalse(failed)
            self.assertEqual(len(finished), 1)
            self.assertEqual(len(finished[0]), 1)
            self.assertEqual(progress, [(1, 1, "item_01_opening_notes_combine.mp3")])
            exported_file = temp_dir / "item_01_opening_notes_combine.mp3"
            self.assertTrue(exported_file.exists())
            self.assertIn(
                b"Unique batch worker sample text",
                exported_file.read_bytes(),
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
