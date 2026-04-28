"""Convenience exports for the provider-aware TTS package."""

from app.model.tts_providers.factory import (
    create_tts_provider,
    get_provider_display_name,
    resolve_tts_provider_config,
)
from app.model.tts_providers.models import (
    TTSProvider,
    TTSProviderCapabilities,
    TTSProviderConfig,
    TTSRequest,
    TTSResult,
)
from app.model.tts_providers.provider_catalog import (
    ProviderProfile,
    get_provider_profile,
    list_provider_profiles,
)
from app.model.tts_providers.voice_catalog import (
    GEMINI_VOICE_SUGGESTIONS,
    POLLY_VOICE_SUGGESTIONS,
    get_voice_suggestions,
)

__all__ = [
    "create_tts_provider",
    "get_provider_display_name",
    "resolve_tts_provider_config",
    "TTSProvider",
    "TTSProviderCapabilities",
    "TTSProviderConfig",
    "TTSRequest",
    "TTSResult",
    "ProviderProfile",
    "get_provider_profile",
    "list_provider_profiles",
    "GEMINI_VOICE_SUGGESTIONS",
    "POLLY_VOICE_SUGGESTIONS",
    "get_voice_suggestions",
]
