from pathlib import Path

from app.controller.background_workers import BatchExportWorker, DocumentParseWorker
from app.model.app_settings import AppSettings
from app.model.tts_providers.models import TTSProviderConfig


class FakeTTSProcessor:
    def __init__(self, provider_config):
        self.provider_config = provider_config

    def text_to_speech(self, text, use_ssml=False):
        return f"audio:{use_ssml}:{text}".encode("utf-8")


def fake_tts_processor(provider_config):
    return FakeTTSProcessor(provider_config)


def test_document_parse_worker_can_cancel_before_parsing():
    cancelled = []
    finished = []
    failed = []
    worker = DocumentParseWorker("does-not-need-to-exist.txt")
    worker.cancelled.connect(lambda: cancelled.append(True))
    worker.finished.connect(finished.append)
    worker.failed.connect(failed.append)

    worker.request_cancel()
    worker.run()

    assert cancelled == [True]
    assert not finished
    assert not failed


def test_document_parse_worker_can_parse_raw_html_sources():
    finished = []
    failed = []
    worker = DocumentParseWorker(
        "<html><body><h1>Worker HTML</h1><p>Unique worker HTML body.</p></body></html>",
        source_kind="html",
    )
    worker.finished.connect(finished.append)
    worker.failed.connect(failed.append)

    worker.run()

    assert not failed
    assert len(finished) == 1
    assert finished[0][0]["source_type"] == "html"
    assert "Unique worker HTML body." in finished[0][0]["primary_text"]


def test_batch_export_worker_writes_files_and_reports_progress(
    runtime_tmp_path, monkeypatch
):
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
    monkeypatch.setattr(
        "app.controller.background_workers.create_tts_processor",
        fake_tts_processor,
    )
    worker = BatchExportWorker(
        rows=rows,
        output_dir=runtime_tmp_path,
        settings=AppSettings(auto_clean_text=False),
        provider_config=TTSProviderConfig(
            provider_name="azure",
            credentials={
                "subscription_key": "fake-key",
                "region": "fake-region",
            },
        ),
    )
    worker.finished.connect(finished.append)
    worker.failed.connect(lambda message, files: failed.append((message, files)))
    worker.progress.connect(
        lambda completed, total, path: progress.append(
            (completed, total, Path(path).name)
        )
    )

    worker.run()

    assert not failed
    assert len(finished) == 1
    assert len(finished[0]) == 1
    assert progress == [(1, 1, "item_01_opening_context_combine.mp3")]
    exported_file = runtime_tmp_path / "item_01_opening_context_combine.mp3"
    assert exported_file.exists()
    assert b"Unique batch worker sample text" in exported_file.read_bytes()


def test_batch_export_worker_can_cancel_between_rows(runtime_tmp_path, monkeypatch):
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
    monkeypatch.setattr(
        "app.controller.background_workers.create_tts_processor",
        fake_tts_processor,
    )
    worker = BatchExportWorker(
        rows=rows,
        output_dir=runtime_tmp_path,
        settings=AppSettings(auto_clean_text=False),
        provider_config=TTSProviderConfig(
            provider_name="azure",
            credentials={
                "subscription_key": "fake-key",
                "region": "fake-region",
            },
        ),
    )
    worker.finished.connect(finished.append)
    worker.cancelled.connect(cancelled.append)

    def cancel_after_first_file(completed, total, path):
        progress.append((completed, total, Path(path).name))
        worker.request_cancel()

    worker.progress.connect(cancel_after_first_file)

    worker.run()

    assert not finished
    assert progress == [(1, 2, "item_01_first_combine.mp3")]
    assert len(cancelled) == 1
    assert len(cancelled[0]) == 1
    assert (runtime_tmp_path / "item_01_first_combine.mp3").exists()
    assert not (runtime_tmp_path / "item_02_second_combine.mp3").exists()
