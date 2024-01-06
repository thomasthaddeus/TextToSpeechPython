"""ssml_config.py

This module provides a configuration class for Speech Synthesis Markup Language
(SSML) settings, specifically tailored for Azure Cognitive Services Speech SDK.
It includes functionalities to list, set, and get supported voices for speech
synthesis.

Raises:
    ValueError: If the specified voice is not supported in the list of
    supported voices.

Returns:
    SSMLConfig: An instance of the SSMLConfig class.
"""

from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer
from azure.cognitiveservices.speech.audio import AudioOutputConfig


class SSMLConfig:
    """
    SSMLConfig is a class that encapsulates the configuration settings for
    speech synthesis using SSML with Azure Cognitive Services Speech SDK. It
    allows users to choose from a list of predefined neural voices.

    Raises:
        ValueError: If the voice set by the user is not in the list of
        supported voices.

    Returns:
        SSMLConfig: An instance of the SSMLConfig class.
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
        Initializes the SSMLConfig instance with default settings. By default, it selects
        the first voice in the list of supported voices.

        Extended Summary:
            The constructor sets a default voice from the SUPPORTED_VOICES list to ensure
            there is always a valid voice selected for speech synthesis.
        """
        self._voice = self.SUPPORTED_VOICES[0]  # Set a default voice

    def list_voices(self):
        """
        Provides a list of supported voices for speech synthesis.

        Extended Summary:
            This method returns the list of voice names that are available for use with
            Azure Cognitive Services Speech SDK.

        Returns:
            List[str]: A list of supported voice names.
        """
        return self.SUPPORTED_VOICES

    def set_voice(self, voice):
        """
        Sets the voice for speech synthesis.

        Args:
            voice (str): The name of the voice to be set for speech synthesis.

        Raises:
            ValueError: If the specified voice is not in the list of supported voices.

        Extended Summary:
            This method allows setting the voice for speech synthesis, provided it is
            in the list of supported voices. If the voice is not supported, it raises a
            ValueError.
        """
        if voice not in self.SUPPORTED_VOICES:
            raise ValueError(f"Voice '{voice}' is not supported!")
        self._voice = voice

    def get_voice(self):
        """
        Gets the currently set voice for speech synthesis.

        Extended Summary:
            This method returns the name of the currently selected voice for speech synthesis.

        Returns:
            str: The name of the currently set voice.
        """
        return self._voice
