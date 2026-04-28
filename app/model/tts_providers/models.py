"""Shared provider-facing data models for text-to-speech synthesis."""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class TTSRequest:
    """Normalized synthesis request passed to provider implementations."""

    text: str
    use_ssml: bool = False
    voice: str | None = None
    output_format: str = "audio-16khz-32kbitrate-mono-mp3"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TTSResult:
    """Normalized synthesis result returned by providers."""

    audio_data: bytes
    provider_name: str
    output_format: str = "audio-16khz-32kbitrate-mono-mp3"
    request: TTSRequest | None = None
    raw_result: Any = None


@dataclass(frozen=True)
class TTSProviderCapabilities:
    """Feature flags surfaced by a provider implementation."""

    supports_ssml: bool = False
    supports_style_prompt: bool = False
    supports_multi_speaker: bool = False
    supports_offline: bool = False
    supports_streaming: bool = False
    supported_formats: tuple[str, ...] = ("audio-16khz-32kbitrate-mono-mp3",)
    max_input_size: int | None = None


@dataclass(frozen=True)
class TTSProviderConfig:
    """Serializable provider selection and credential bundle."""

    provider_name: str
    credentials: dict[str, str] = field(default_factory=dict)
    api_config_path: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


class TTSProvider(Protocol):
    """Protocol every concrete TTS provider must satisfy."""

    provider_name: str

    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Generate audio for the provided request."""

    def get_capabilities(self) -> TTSProviderCapabilities:
        """Describe the provider's supported synthesis features."""

    def list_voices(self, engine=None, language_code=None) -> tuple[str, ...]:
        """Return available voice identifiers for the provider."""
