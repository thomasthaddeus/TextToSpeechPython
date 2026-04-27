from app.controller.background_workers import BatchExportWorker
from app.controller.main_controller import MainController
from app.model.app_settings import AppSettings
from app.model.processors.tts_processor import TTSProcessor
from app.model.tts_providers.azure_provider import AzureTTSProvider
from app.model.tts_providers.models import (
    TTSProviderCapabilities,
    TTSProviderConfig,
    TTSRequest,
    TTSResult,
)


class FakeProvider:
    provider_name = "fake"

    def __init__(self):
        self.requests = []

    def synthesize(self, request):
        self.requests.append(request)
        return TTSResult(
            audio_data=f"fake:{request.use_ssml}:{request.text}".encode("utf-8"),
            provider_name=self.provider_name,
            request=request,
        )

    def get_capabilities(self):
        return TTSProviderCapabilities(
            supports_ssml=True,
            supports_offline=True,
            supported_formats=("wav", "mp3"),
            max_input_size=4096,
        )


def test_tts_processor_supports_fake_provider_synthesis():
    provider = FakeProvider()
    processor = TTSProcessor(provider=provider)

    audio_data = processor.text_to_speech("Hello provider", use_ssml=False)
    capabilities = processor.get_capabilities()

    assert audio_data == b"fake:False:Hello provider"
    assert provider.requests[0].text == "Hello provider"
    assert not provider.requests[0].use_ssml
    assert capabilities.supports_ssml
    assert capabilities.supports_offline
    assert capabilities.supported_formats == ("wav", "mp3")
    assert capabilities.max_input_size == 4096


def test_azure_provider_wraps_azure_api(monkeypatch):
    captured = {}

    class FakeAzureTTSAPI:
        def __init__(self, subscription_key, region):
            captured["credentials"] = (subscription_key, region)

        def convert_ssml_to_audio(self, text):
            captured["ssml"] = text
            return b"azure-ssml"

        def convert_text_to_audio(self, text):
            captured["text"] = text
            return b"azure-text"

    monkeypatch.setattr(
        "app.model.tts_providers.azure_provider.AzureTTSAPI",
        FakeAzureTTSAPI,
    )

    provider = AzureTTSProvider("key-123", "eastus")
    ssml_result = provider.synthesize(TTSRequest(text="<speak>Hello</speak>", use_ssml=True))
    text_result = provider.synthesize(TTSRequest(text="Hello", use_ssml=False))
    capabilities = provider.get_capabilities()

    assert captured["credentials"] == ("key-123", "eastus")
    assert captured["ssml"] == "<speak>Hello</speak>"
    assert captured["text"] == "Hello"
    assert ssml_result.audio_data == b"azure-ssml"
    assert text_result.audio_data == b"azure-text"
    assert capabilities.supports_ssml
    assert capabilities.supports_style_prompt
    assert capabilities.supported_formats == ("audio-16khz-32kbitrate-mono-mp3",)


def test_main_controller_builds_tts_processor_from_provider_config(monkeypatch):
    captured = {}

    class FakeProcessor:
        def __init__(self, provider_config):
            captured["provider_config"] = provider_config

    controller = MainController.__new__(MainController)
    controller.settings = AppSettings(tts_provider="azure")
    controller.tts_processor = None
    monkeypatch.setattr(
        controller,
        "_resolve_tts_provider_config",
        lambda: TTSProviderConfig(
            provider_name="azure",
            credentials={
                "subscription_key": "controller-key",
                "region": "controller-region",
            },
        ),
    )
    monkeypatch.setattr(
        "app.controller.main_controller.TTSProcessor",
        FakeProcessor,
    )

    processor = controller._ensure_tts_processor()

    assert processor is controller.tts_processor
    assert captured["provider_config"].provider_name == "azure"
    assert captured["provider_config"].credentials["subscription_key"] == "controller-key"
    assert captured["provider_config"].credentials["region"] == "controller-region"


def test_batch_export_worker_uses_provider_config_for_synthesis(
    runtime_tmp_path, monkeypatch
):
    captured = {}
    rows = [
        {
            "item_number": 1,
            "title": "Architecture",
            "content_mode": "combine",
            "resolved_text": "Provider architecture export.",
        }
    ]

    class FakeProcessor:
        def text_to_speech(self, text, use_ssml=False):
            captured["synthesis"] = (text, use_ssml)
            return b"worker-audio"

    def fake_create_tts_processor(provider_config):
        captured["provider_config"] = provider_config
        return FakeProcessor()

    monkeypatch.setattr(
        "app.controller.background_workers.create_tts_processor",
        fake_create_tts_processor,
    )

    worker = BatchExportWorker(
        rows=rows,
        output_dir=runtime_tmp_path,
        settings=AppSettings(auto_clean_text=False, tts_provider="azure"),
        provider_config=TTSProviderConfig(
            provider_name="azure",
            credentials={
                "subscription_key": "worker-key",
                "region": "worker-region",
            },
        ),
    )

    worker.run()

    assert captured["provider_config"].provider_name == "azure"
    assert captured["provider_config"].credentials["subscription_key"] == "worker-key"
    assert captured["provider_config"].credentials["region"] == "worker-region"
    assert captured["synthesis"][1] is True
