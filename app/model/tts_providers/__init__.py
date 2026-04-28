"""Provider-agnostic text-to-speech abstractions and factories."""

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
from app.model.tts_providers.voice_catalog import get_voice_suggestions

__all__ = [
    "TTSProvider",
    "TTSProviderCapabilities",
    "TTSProviderConfig",
    "TTSRequest",
    "TTSResult",
    "create_tts_provider",
    "get_provider_display_name",
    "get_voice_suggestions",
    "resolve_tts_provider_config",
]
