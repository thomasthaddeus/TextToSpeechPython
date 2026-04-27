"""Azure-backed implementation of the generic text-to-speech provider API."""

from app.model.api.azure_tts_api import AzureTTSAPI
from app.model.tts_providers.models import (
    TTSProviderCapabilities,
    TTSRequest,
    TTSResult,
)


class AzureTTSProvider:
    """Wrap Azure speech synthesis behind the shared provider interface."""

    provider_name = "azure"

    def __init__(self, subscription_key, region=None):
        self.client = AzureTTSAPI(subscription_key, region)

    def synthesize(self, request: TTSRequest) -> TTSResult:
        if request.use_ssml:
            audio_data = self.client.convert_ssml_to_audio(request.text)
        else:
            audio_data = self.client.convert_text_to_audio(request.text)

        return TTSResult(
            audio_data=audio_data,
            provider_name=self.provider_name,
            output_format=request.output_format,
            request=request,
        )

    def get_capabilities(self) -> TTSProviderCapabilities:
        return TTSProviderCapabilities(
            supports_ssml=True,
            supports_style_prompt=True,
            supports_multi_speaker=False,
            supports_offline=False,
            supports_streaming=False,
            supported_formats=("audio-16khz-32kbitrate-mono-mp3",),
            max_input_size=None,
        )
