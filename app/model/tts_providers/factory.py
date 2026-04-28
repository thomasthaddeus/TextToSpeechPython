"""Factory helpers for selecting and configuring TTS providers."""

from app.model.api.api_config import get_api_settings
from app.model.api.gemini_config import get_gemini_settings
from app.model.api.polly_config import get_polly_settings
from app.model.tts_providers.azure_provider import AzureTTSProvider
from app.model.tts_providers.gemini_provider import GeminiTTSProvider
from app.model.tts_providers.polly_provider import PollyTTSProvider
from app.model.tts_providers.models import TTSProviderConfig


DEFAULT_PROVIDER_NAME = "azure"
PROVIDER_DISPLAY_NAMES = {
    "azure": "Azure Speech",
    "gemini": "Gemini TTS",
    "polly": "Amazon Polly",
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

    if provider_name == "polly":
        config_path = (
            getattr(settings, "polly_config_path", "") or ".polly.env"
        ).strip()
        try:
            credentials = get_polly_settings(config_path)
        except Exception:
            return None

        return TTSProviderConfig(
            provider_name=provider_name,
            credentials=credentials,
            api_config_path=config_path,
            options={
                "engine": getattr(settings, "polly_engine", "neural"),
            },
        )

    if provider_name == "gemini":
        config_path = (
            getattr(settings, "gemini_config_path", "") or ".gemini.env"
        ).strip()
        try:
            credentials = get_gemini_settings(config_path)
        except Exception:
            return None

        return TTSProviderConfig(
            provider_name=provider_name,
            credentials=credentials,
            api_config_path=config_path,
            options={
                "model": getattr(
                    settings,
                    "gemini_model",
                    "gemini-2.5-flash-tts",
                ),
                "language_code": getattr(
                    settings,
                    "gemini_language_code",
                    "en-US",
                ),
                "style_prompt": getattr(settings, "gemini_style_prompt", ""),
            },
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

    if provider_name == "polly":
        credentials = dict(provider_config.credentials)
        access_key_id = credentials.get("aws_access_key_id")
        secret_access_key = credentials.get("aws_secret_access_key")
        region = credentials.get("region")
        if not access_key_id or not secret_access_key or not region:
            raise ValueError(
                "Amazon Polly provider configuration requires AWS credentials and region."
            )
        return PollyTTSProvider(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=credentials.get("aws_session_token", ""),
            region=region,
            engine=str(provider_config.options.get("engine", "neural")),
        )

    if provider_name == "gemini":
        credentials = dict(provider_config.credentials)
        project_id = credentials.get("project_id")
        service_account_json = credentials.get("service_account_json")
        region = credentials.get("region", "global")
        if not project_id or not service_account_json:
            raise ValueError(
                "Gemini TTS provider configuration requires project_id and service_account_json."
            )
        return GeminiTTSProvider(
            project_id=project_id,
            service_account_json=service_account_json,
            region=region,
            model=str(
                provider_config.options.get("model", "gemini-2.5-flash-tts")
            ),
        )

    raise ValueError(f"Unsupported TTS provider '{provider_name}'.")
