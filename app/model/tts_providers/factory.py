"""Factory helpers for selecting and configuring TTS providers."""

from app.model.api.api_config import get_api_settings
from app.model.tts_providers.azure_provider import AzureTTSProvider
from app.model.tts_providers.models import TTSProviderConfig


DEFAULT_PROVIDER_NAME = "azure"
PROVIDER_DISPLAY_NAMES = {
    "azure": "Azure Speech",
}


def get_provider_display_name(provider_name):
    """Return a user-friendly name for a provider identifier."""
    return PROVIDER_DISPLAY_NAMES.get(provider_name, provider_name.title())


def resolve_tts_provider_config(settings, fallback_config_path=".env"):
    """Build a normalized provider config from UI settings or fallback env."""
    provider_name = (
        getattr(settings, "tts_provider", "") or DEFAULT_PROVIDER_NAME
    ).strip().lower()

    if provider_name == "azure":
        if settings.azure_key and settings.azure_region:
            return TTSProviderConfig(
                provider_name=provider_name,
                credentials={
                    "subscription_key": settings.azure_key,
                    "region": settings.azure_region,
                },
            )

        try:
            subscription_key, region = get_api_settings(fallback_config_path)
        except Exception:
            return None

        return TTSProviderConfig(
            provider_name=provider_name,
            credentials={
                "subscription_key": subscription_key,
                "region": region,
            },
            api_config_path=fallback_config_path,
        )

    raise ValueError(f"Unsupported TTS provider '{provider_name}'.")


def create_tts_provider(provider_config):
    """Instantiate the concrete provider requested by the given config."""
    provider_name = provider_config.provider_name.strip().lower()

    if provider_name == "azure":
        credentials = dict(provider_config.credentials)
        subscription_key = credentials.get("subscription_key")
        region = credentials.get("region")
        if not subscription_key or not region:
            raise ValueError(
                "Azure provider configuration requires subscription_key and region."
            )
        return AzureTTSProvider(subscription_key, region)

    raise ValueError(f"Unsupported TTS provider '{provider_name}'.")
