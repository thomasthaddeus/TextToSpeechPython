"""Static provider metadata used by the desktop settings workflow."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderProfile:
    """Describe what a provider can expose in the current desktop UI."""

    provider_id: str
    display_name: str
    description: str
    implemented: bool
    supports_ssml: bool
    supports_advanced_ssml: bool
    supports_voice_selection: bool
    supports_style_prompt: bool
    supports_connection_test: bool
    config_label: str
    config_placeholder: str
    config_help: str


PROVIDER_PROFILES = {
    "azure": ProviderProfile(
        provider_id="azure",
        display_name="Azure Speech",
        description=(
            "Full desktop support with voice selection, SSML preview, advanced "
            "prosody controls, and live connection testing."
        ),
        implemented=True,
        supports_ssml=True,
        supports_advanced_ssml=True,
        supports_voice_selection=True,
        supports_style_prompt=False,
        supports_connection_test=True,
        config_label="Azure Credentials",
        config_placeholder="Subscription key and region",
        config_help="Use an Azure Speech subscription key and region, or fall back to .env.",
    ),
    "polly": ProviderProfile(
        provider_id="polly",
        display_name="Amazon Polly",
        description=(
            "Provider-aware settings are available here, including SSML-oriented "
            "controls and an external config path."
        ),
        implemented=True,
        supports_ssml=True,
        supports_advanced_ssml=True,
        supports_voice_selection=True,
        supports_style_prompt=False,
        supports_connection_test=False,
        config_label="Polly Config Path",
        config_placeholder=".polly.env",
        config_help="Point to a local file that stores your Polly credentials and defaults.",
    ),
    "gemini": ProviderProfile(
        provider_id="gemini",
        display_name="Google Gemini TTS",
        description=(
            "Prompt-driven synthesis with model selection and style prompting, "
            "without SSML preview controls."
        ),
        implemented=True,
        supports_ssml=False,
        supports_advanced_ssml=False,
        supports_voice_selection=True,
        supports_style_prompt=True,
        supports_connection_test=False,
        config_label="Gemini Config Path",
        config_placeholder=".gemini.env",
        config_help="Point to a local file that stores your Gemini credentials and model defaults.",
    ),
    "local": ProviderProfile(
        provider_id="local",
        display_name="Local TTS",
        description=(
            "Offline-oriented provider configuration with a local engine config "
            "path and no cloud connection test."
        ),
        implemented=True,
        supports_ssml=False,
        supports_advanced_ssml=False,
        supports_voice_selection=True,
        supports_style_prompt=False,
        supports_connection_test=False,
        config_label="Local Config Path",
        config_placeholder=".local_tts.env",
        config_help="Point to a local engine configuration file for offline synthesis.",
    ),
}


def list_provider_profiles():
    """Return providers in the display order used by the settings UI."""
    return [
        PROVIDER_PROFILES["azure"],
        PROVIDER_PROFILES["polly"],
        PROVIDER_PROFILES["gemini"],
        PROVIDER_PROFILES["local"],
    ]


def get_provider_profile(provider_id):
    """Return the matching provider profile or fall back to Azure."""
    return PROVIDER_PROFILES.get(provider_id, PROVIDER_PROFILES["azure"])
