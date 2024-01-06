"""ssml_voice_effects.py

This module provides a set of tools for manipulating voice effects using SSML
(Speech Synthesis Markup Language).

Returns:
    str: An SSML-formatted string with the desired voice effects.
"""

import azure.cognitiveservices.speech as speechsdk


class SSMLVoiceEffects:
    """
    A class to apply various SSML voice effects to a given text.

    Raises:
        ValueError: If an unsupported voice or parameter is provided.

    Returns:
        str: An SSML-formatted string with the desired voice effects.
    """

    def __init__(
        self,
        default_voice="en-US-Guy24kRUS",
        default_rate="medium",
        default_volume="medium",
    ):
        """
        Initializes the SSMLVoiceEffects class with default voice, rate, and
        volume settings.

        Args:
            default_voice (str, optional): The default voice to use. Defaults
              to "en-US-Guy24kRUS".
            default_rate (str, optional): The default speech rate. Defaults to
              "medium".
            default_volume (str, optional): The default volume level. Defaults
              to "medium".
        """
        self.default_voice = default_voice
        self.default_rate = default_rate
        self.default_volume = default_volume

    @property
    def default_prosody(self):
        """
        Generates a prosody tag with the default rate and volume settings.

        Returns:
            str: An SSML prosody tag with default settings.
        """
        return f'<prosody rate="{self.default_rate}" volume="{self.default_volume}">{{}}</prosody>'

    def wrap_with_default_prosody(self, text):
        """
        Wraps the given text with the default prosody settings.

        Args:
            text (str): The text to be wrapped.

        Returns:
            str: Text wrapped with the default prosody settings.
        """
        return self.default_prosody.format(text)

    def change_voice(self, text, voice_name=None):
        """
        Changes the voice for a specific part of the text.

        Args:
            text (str): The text for which the voice needs to be changed.
            voice_name (str, optional): The name of the voice to be applied.
            Defaults to the class's default voice.

        Raises:
            ValueError: If the provided voice_name is not in the
            SUPPORTED_VOICES list.

        Returns:
            str: Text wrapped with the specified voice.
        """
        voice_name = voice_name if voice_name else self.default_voice
        voice_name = voice_name or self.config.get_voice()

        if voice_name not in self.config.list_voices():
            raise ValueError(f"Voice '{voice_name}' is not supported!")

        return f'<voice name="{voice_name}">{text}</voice>'


    def adjust_pitch(self, text, pitch="medium"):
        """
        Adjust the baseline pitch of the voice.

        Values can be: "x-low", "low", "medium", "high", "x-high", or a
        relative value like "+2st" or "-2st".

        Args:
            text (str): The text for which the pitch needs to be adjusted.
            pitch (str, optional): The desired pitch level. Defaults to
              "medium".

        Returns:
            str: Text with adjusted pitch.
        """
        return f'<prosody pitch="{pitch}">{text}</prosody>'


    def adjust_contour(self, text, contour):
        """
        Adjusts the pitch contour of the voice.

        Args:
            text (str): The text for which the pitch contour needs to be
              adjusted.
            contour (str): The desired pitch contour pattern.

        Returns:
            str: Text with adjusted pitch contour.

        Example: "(0%,+20Hz)(10%,-5Hz)"
        """
        return f'<prosody contour="{contour}">{text}</prosody>'


    def set_duration(self, text, duration="medium"):
        """
        Sets the time taken to read an element.

        Duration can be in milliseconds like "250ms" or "3s".

        Args:
            text (str): The text for which the duration needs to be set.
            duration (str, optional): The desired duration. Defaults to
              "medium".

        Returns:
            str: Text with adjusted duration.
        """
        return f'<prosody duration="{duration}">{text}</prosody>'


    def adjust_range(self, text, range_val="medium"):
        """
        Adjust the range of pitch variation.

        Values can be: "x-low", "low", "medium", "high", "x-high".

        Args:
            text (str): The text for which the pitch range needs to be adjusted.
            range_val (str, optional): The desired pitch range. Defaults to
            "medium".

        Returns:
            str: Text with adjusted pitch range.
        """

        return f'<prosody range="{range_val}">{text}</prosody>'


    def change_rate(self, text, rate=None):
        """
        Adjusts the speaking rate of the text.

        Args:
            text (str): The text for which the speaking rate needs to be
              adjusted.
            rate (str, optional): The desired speaking rate. Defaults to the
              class's default rate.

        Returns:
            str: Text with adjusted speaking rate.
        """
        rate = rate if rate else self.default_rate
        return f'<prosody rate="{rate}">{text}</prosody>'


    def add_emphasis(self, text, level="moderate"):
        """
        Adds emphasis to the text.

        Levels can be: "strong", "moderate", or "reduced".

        Args:
            text (str): The text to be emphasized.
            level (str, optional): The level of emphasis. Defaults to
            "moderate".

        Returns:
            str: Text with added emphasis.
        """
        return f'<emphasis level="{level}">{text}</emphasis>'


    def adjust_volume(self, text, volume=None):
        """
        Adjusts the volume of the text.

        Args:
            text (str): The text for which the volume needs to be adjusted.
            volume (str, optional): The desired volume level. Defaults to the
              class's default volume.

        Returns:
            str: Text with adjusted volume.
        """
        volume = volume if volume else self.default_volume
        return f'<prosody volume="{volume}">{text}</prosody>'
