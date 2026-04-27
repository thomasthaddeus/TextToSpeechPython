"""Provider-aware text-to-speech processor."""

from app.model.processors.ssml_audio_processor import SSMLAudioProcessor
from app.model.tts_providers import (
    TTSProviderConfig,
    TTSRequest,
    create_tts_provider,
)


class TTSProcessor:
    """Bridge controller synthesis requests to a provider implementation."""

    def __init__(
        self,
        provider=None,
        provider_config=None,
        api_config_path=None,
        ssml_config_path=None,
        azure_key=None,
        azure_region=None,
    ):
        """Initialize the processor with an explicit provider or Azure fallback."""
        del ssml_config_path  # Retained for backward compatibility.

        if provider is not None:
            self.provider = provider
        elif provider_config is not None:
            self.provider = create_tts_provider(provider_config)
        elif azure_key and azure_region:
            self.provider = create_tts_provider(
                TTSProviderConfig(
                    provider_name="azure",
                    credentials={
                        "subscription_key": azure_key,
                        "region": azure_region,
                    },
                )
            )
        elif api_config_path:
            from app.model.api.api_config import get_api_settings

            resolved_key, resolved_region = get_api_settings(api_config_path)
            self.provider = create_tts_provider(
                TTSProviderConfig(
                    provider_name="azure",
                    credentials={
                        "subscription_key": resolved_key,
                        "region": resolved_region,
                    },
                    api_config_path=api_config_path,
                )
            )
        else:
            raise ValueError(
                "Provide a TTS provider, provider config, or explicit Azure settings."
            )

        self.ssml_processor = SSMLAudioProcessor()

    def synthesize(self, request):
        """Synthesize a normalized request through the configured provider."""
        provider_request = request
        if request.use_ssml:
            provider_request = TTSRequest(
                text=self.ssml_processor.process_ssml(request.text),
                use_ssml=True,
                voice=request.voice,
                output_format=request.output_format,
                metadata=dict(request.metadata),
            )
        return self.provider.synthesize(provider_request)

    def text_to_speech(self, text, use_ssml=False):
        """Backward-compatible helper that returns synthesized audio bytes."""
        result = self.synthesize(TTSRequest(text=text, use_ssml=use_ssml))
        return result.audio_data

    def get_capabilities(self):
        """Expose provider capability flags to higher-level callers."""
        return self.provider.get_capabilities()
