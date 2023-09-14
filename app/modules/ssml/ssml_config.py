"""ssml_config.py

_summary_

_extended_summary_

Raises:
    ValueError: _description_

Returns:
    _type_: _description_
"""

class SSMLConfig:
    """
     _summary_

    _extended_summary_

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """

    # Define a list of supported voices.
    SUPPORTED_VOICES = [
        "en-US-JennyNeural",
        "en-US-GuyNeural",
        "en-US-AriaNeural",
        "en-US-DavisNeural",
        "en-US-AmberNeural",
        "en-US-AnaNeural",
        "en-US-AshleyNeural",
        "en-US-BrandonNeural",
        "en-US-ChristopherNeural",
        "en-US-CoraNeural",
        "en-US-ElizabethNeural",
        "en-US-EricNeural",
        "en-US-JacobNeural",
        "en-US-JaneNeural",
        "en-US-JasonNeural",
        "en-US-MichelleNeural",
        "en-US-MonicaNeural",
        "en-US-NancyNeural",
        "en-US-RogerNeural",
        "en-US-SaraNeural",
        "en-US-SteffanNeural",
        "en-US-TonyNeural"
    ]

    def __init__(self):
        """
        __init__ _summary_

        _extended_summary_
        """
        self._voice = self.SUPPORTED_VOICES[0]  # Set a default voice

    def list_voices(self):
        """
        list_voices _summary_

        _extended_summary_

        Returns:
            _type_: _description_
        """
        return self.SUPPORTED_VOICES

    def set_voice(self, voice):
        """
        set_voice _summary_

        _extended_summary_

        Args:
            voice (_type_): _description_

        Raises:
            ValueError: _description_
        """
        if voice not in self.SUPPORTED_VOICES:
            raise ValueError(f"Voice '{voice}' is not supported!")
        self._voice = voice

    def get_voice(self):
        """
        get_voice _summary_

        _extended_summary_

        Returns:
            _type_: _description_
        """
        return self._voice