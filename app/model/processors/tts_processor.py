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
            processed_ssml = self.ssml_processor.process_ssml(request.text)
            provider_request = TTSRequest(
                text=processed_ssml,
                use_ssml=True,
                voice=request.voice or self._extract_voice_name_from_ssml(processed_ssml),
                output_format=request.output_format,
                metadata=dict(request.metadata),
            )
        return self.provider.synthesize(provider_request)

    def text_to_speech(self, text, use_ssml=False, voice=None, metadata=None):
        """Backward-compatible helper that returns synthesized audio bytes."""
        result = self.synthesize(
            TTSRequest(
                text=text,
                use_ssml=use_ssml,
                voice=voice,
                metadata=dict(metadata or {}),
            )
        )
        return result.audio_data

    def get_capabilities(self):
        """Expose provider capability flags to higher-level callers."""
        return self.provider.get_capabilities()

    def list_voices(self, engine=None, language_code=None):
        """Expose provider voice discovery when supported."""
        return self.provider.list_voices(engine=engine, language_code=language_code)

    def _extract_voice_name_from_ssml(self, text):
        marker = 'name="'
        marker_index = text.find(marker)
        if marker_index == -1:
            return None
        start_index = marker_index + len(marker)
        end_index = text.find('"', start_index)
        if end_index == -1:
            return None
        voice_name = text[start_index:end_index].strip()
        return voice_name or None
