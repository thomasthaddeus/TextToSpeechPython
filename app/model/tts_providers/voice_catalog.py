"""Provider-specific voice suggestions for the settings UI."""

from app.model.ssml.ssml_config import SSMLConfig


POLLY_VOICE_SUGGESTIONS = (
    "Joanna",
    "Matthew",
    "Ivy",
    "Justin",
    "Kendra",
    "Kimberly",
    "Salli",
    "Joey",
    "Danielle",
    "Gregory",
    "Ruth",
    "Stephen",
    "Amy",
    "Brian",
    "Emma",
    "Olivia",
)

GEMINI_VOICE_SUGGESTIONS = (
    "Achernar",
    "Achird",
    "Algenib",
    "Algieba",
    "Alnilam",
    "Aoede",
    "Autonoe",
    "Callirrhoe",
    "Charon",
    "Despina",
    "Enceladus",
    "Erinome",
    "Fenrir",
    "Gacrux",
    "Iapetus",
    "Kore",
    "Laomedeia",
    "Leda",
    "Orus",
    "Pulcherrima",
    "Puck",
    "Rasalgethi",
    "Sadachbia",
    "Sadaltager",
    "Schedar",
    "Sulafat",
    "Umbriel",
    "Vindemiatrix",
    "Zephyr",
    "Zubenelgenubi",
)


def get_voice_suggestions(provider_name):
    """Return a provider-specific list of suggested voice identifiers."""
    normalized_name = (provider_name or "azure").strip().lower()
    if normalized_name == "polly":
        return POLLY_VOICE_SUGGESTIONS
    if normalized_name == "gemini":
        return GEMINI_VOICE_SUGGESTIONS
    return tuple(SSMLConfig.SUPPORTED_VOICES)
