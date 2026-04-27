"""Background workers for expensive controller operations."""

from pathlib import Path
from xml.sax.saxutils import escape

from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger

from app.model.app_settings import AppSettings
from app.model.scraper.document_scraper import DocumentScraper
from app.model.ssml.text_to_ssml import TextToSSML
from app.model.tts_providers import get_provider_display_name
from app.utils.text_cleaner import TextCleaner


def create_tts_processor(provider_config):
    """Create the TTS processor only when audio generation is requested."""
    from app.model.processors.tts_processor import TTSProcessor

    return TTSProcessor(provider_config=provider_config)


def sanitize_batch_name(value):
    """Create a filesystem-safe token for generated batch audio names."""
    sanitized = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in str(value).strip().lower()
    )
    sanitized = sanitized.strip("_")
    return sanitized or "item"


def build_ssml_document(text, settings, cleaner=None):
    """Build the SSML document used by both UI and worker-thread generation."""
    working_text = text
    text_cleaner = cleaner or TextCleaner()
    if settings.auto_clean_text:
        working_text = text_cleaner.clean_all(working_text)

    ssml_content = escape(working_text)

    if settings.pause_duration != "none":
        pause_tag = f'<break time="{settings.pause_duration}"/>'
        if settings.pause_position == "before":
            ssml_content = f"{pause_tag}{ssml_content}"
        else:
            ssml_content = f"{ssml_content}{pause_tag}"

    if settings.emphasis_level != "none":
        ssml_content = (
            f'<emphasis level="{settings.emphasis_level}">{ssml_content}</emphasis>'
        )

    prosody_attributes = [
        f'rate="{settings.speaking_rate}"',
        f'volume="{settings.synthesis_volume}"',
    ]
    if settings.pitch != "default":
        prosody_attributes.append(f'pitch="{settings.pitch}"')
    if settings.pitch_range != "default":
        prosody_attributes.append(f'range="{settings.pitch_range}"')

    prosody_text = f"<prosody {' '.join(prosody_attributes)}>{ssml_content}</prosody>"
    return TextToSSML(voice_name=settings.voice).convert(prosody_text)


class DocumentParseWorker(QObject):
    """Parse a document or source payload away from the UI thread."""

    finished = pyqtSignal(object)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, source, source_kind="file"):
        super().__init__()
        self.source = source
        self.source_kind = source_kind
        self._cancel_requested = False

    def request_cancel(self):
        self._cancel_requested = True

    def run(self):
        if self._cancel_requested:
            self.cancelled.emit()
            return

        try:
            scraper = DocumentScraper()
            if self.source_kind == "file":
                rows = scraper.scrape_file(self.source)
            elif self.source_kind == "url":
                rows = scraper.scrape_url(self.source)
            elif self.source_kind == "html":
                rows = scraper.scrape_html_text(self.source)
            else:
                raise ValueError(f"Unsupported document source: {self.source_kind}")
        except Exception as error:
            logger.exception(
                "Document parsing failed for {} source: {}",
                self.source_kind,
                error,
            )
            self.failed.emit(str(error))
            return

        if self._cancel_requested:
            self.cancelled.emit()
            return

        self.finished.emit(rows)


class BatchExportWorker(QObject):
    """Generate a batch of audio files away from the UI thread."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)
    failed = pyqtSignal(str, object)
    cancelled = pyqtSignal(object)

    def __init__(self, rows, output_dir, settings, provider_config):
        super().__init__()
        self.rows = [dict(row) for row in rows]
        self.output_dir = Path(output_dir)
        self.settings = AppSettings(**vars(settings))
        self.provider_config = provider_config
        self._cancel_requested = False

    def request_cancel(self):
        self._cancel_requested = True

    def run(self):
        exported_files = []
        try:
            if self._cancel_requested:
                self.cancelled.emit(exported_files)
                return

            if self.provider_config is None:
                provider_name = get_provider_display_name(
                    getattr(self.settings, "tts_provider", "azure")
                )
                raise RuntimeError(f"{provider_name} credentials are required.")

            exportable_rows = [
                row for row in self.rows if (row.get("resolved_text") or "").strip()
            ]
            if not exportable_rows:
                self.finished.emit(exported_files)
                return

            self.output_dir.mkdir(parents=True, exist_ok=True)
            processor = create_tts_processor(self.provider_config)
            cleaner = TextCleaner()
            total_rows = len(exportable_rows)

            for row_index, row in enumerate(exportable_rows, start=1):
                if self._cancel_requested:
                    self.cancelled.emit(exported_files)
                    return

                resolved_text = (row.get("resolved_text") or "").strip()
                ssml = build_ssml_document(resolved_text, self.settings, cleaner)
                audio_data = processor.text_to_speech(ssml, use_ssml=True)

                if self._cancel_requested:
                    self.cancelled.emit(exported_files)
                    return

                mode_name = sanitize_batch_name(
                    row.get("content_mode", "prefer_secondary")
                )
                title_name = sanitize_batch_name(
                    row.get("title", f"item_{row.get('item_number', 0)}")
                )
                item_number = int(row.get("item_number", row_index) or row_index)
                file_name = f"item_{item_number:02d}_{title_name}_{mode_name}.mp3"
                file_path = self.output_dir / file_name

                with open(file_path, "wb") as file:
                    file.write(audio_data)

                exported_files.append(str(file_path))
                self.progress.emit(row_index, total_rows, str(file_path))
        except Exception as error:
            logger.exception("Batch export failed: {}", error)
            self.failed.emit(str(error), exported_files)
            return

        self.finished.emit(exported_files)
