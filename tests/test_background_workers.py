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

from app.controller.background_workers import BatchExportWorker, DocumentParseWorker
from app.model.app_settings import AppSettings


class FakeTTSProcessor:
    def __init__(self, azure_key, azure_region):
        self.azure_key = azure_key
        self.azure_region = azure_region

    def text_to_speech(self, text, use_ssml=False):
        return f"audio:{use_ssml}:{text}".encode("utf-8")


class BackgroundWorkerTests(unittest.TestCase):
    def test_document_parse_worker_can_cancel_before_parsing(self):
        cancelled = []
        finished = []
        failed = []
        worker = DocumentParseWorker("does-not-need-to-exist.txt")
        worker.cancelled.connect(lambda: cancelled.append(True))
        worker.finished.connect(finished.append)
        worker.failed.connect(failed.append)

        worker.request_cancel()
        worker.run()

        self.assertEqual(cancelled, [True])
        self.assertFalse(finished)
        self.assertFalse(failed)

    def test_document_parse_worker_can_parse_raw_html_sources(self):
        finished = []
        failed = []
        worker = DocumentParseWorker(
            "<html><body><h1>Worker HTML</h1><p>Unique worker HTML body.</p></body></html>",
            source_kind="html",
        )
        worker.finished.connect(finished.append)
        worker.failed.connect(failed.append)

        worker.run()

        self.assertFalse(failed)
        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0][0]["source_type"], "html")
        self.assertIn("Unique worker HTML body.", finished[0][0]["primary_text"])

    def test_batch_export_worker_writes_files_and_reports_progress(self):
        temp_dir = Path("data/dynamic/tmp/batch_worker_test")
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        rows = [
            {
                "item_number": 1,
                "title": "Opening Context",
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
            self.assertEqual(progress, [(1, 1, "item_01_opening_context_combine.mp3")])
            exported_file = temp_dir / "item_01_opening_context_combine.mp3"
            self.assertTrue(exported_file.exists())
            self.assertIn(
                b"Unique batch worker sample text",
                exported_file.read_bytes(),
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_batch_export_worker_can_cancel_between_rows(self):
        temp_dir = Path("data/dynamic/tmp/batch_worker_cancel_test")
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        rows = [
            {
                "item_number": 1,
                "title": "First",
                "content_mode": "combine",
                "resolved_text": "First cancel sample.",
            },
            {
                "item_number": 2,
                "title": "Second",
                "content_mode": "combine",
                "resolved_text": "Second cancel sample.",
            },
        ]
        finished = []
        cancelled = []
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
            worker.cancelled.connect(cancelled.append)

            def cancel_after_first_file(completed, total, path):
                progress.append((completed, total, Path(path).name))
                worker.request_cancel()

            worker.progress.connect(cancel_after_first_file)

            with patch(
                "app.controller.background_workers.create_tts_processor",
                lambda azure_key, azure_region: FakeTTSProcessor(
                    azure_key,
                    azure_region,
                ),
            ):
                worker.run()

            self.assertFalse(finished)
            self.assertEqual(progress, [(1, 2, "item_01_first_combine.mp3")])
            self.assertEqual(len(cancelled), 1)
            self.assertEqual(len(cancelled[0]), 1)
            self.assertTrue((temp_dir / "item_01_first_combine.mp3").exists())
            self.assertFalse((temp_dir / "item_02_second_combine.mp3").exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
