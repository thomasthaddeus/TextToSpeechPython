"""text_to_ssml.py

This module provides a class for converting plain text into Speech Synthesis
Markup Language (SSML) format. It allows for customization of voice attributes
like emphasis, speaking rate, and volume in the generated SSML.

The TextToSSML class offers various methods to apply SSML tags to text. These
tags include emphasis, breaks, changes in speaking rate, and volume
adjustments. The class is particularly useful for preparing text for speech
synthesis in applications where nuanced voice modulation is required.
"""

class TextToSSML:
    def __init__(self, voice_name="en-US-Guy24kRUS"):
        """
        Initializes the TextToSSML class with a default voice name. The voice
        name can be changed according to the available voices in Microsoft's
        Text-to-Speech services.

        The constructor sets up the class with a default voice name. This voice
        name can be any valid voice from Microsoft Azure's Text-to-Speech
        service and can be changed as required.

        Args:
            voice_name (str, optional): The name of the voice to be used in
            SSML. Defaults to "en-US-Guy24kRUS".
        """
        self.voice_name = voice_name

    def add_emphasis(self, text, level="moderate"):
        """
        Wraps the provided text with an SSML emphasis tag at the specified
        level.

        Emphasis is used to convey stress or importance in speech. The level of
        emphasis can be 'strong', 'moderate', or 'reduced', affecting how the
        text is spoken by the TTS engine.

        Args:
            text (str): The text to which emphasis is to be added.
            level (str, optional): The level of emphasis ('strong', 'moderate',
            'reduced'). Defaults to "moderate".

        Returns:
            str: The text wrapped in an SSML emphasis tag.
        """
        return f'<emphasis level="{level}">{text}</emphasis>'

    def add_break(self, time="500ms"):
        """
        Inserts an SSML break tag for a pause in speech.

        This method is used to add pauses in the speech, which can be specified
        in milliseconds (e.g., '500ms') or seconds (e.g., '1s'). This can
        enhance the naturalness of the speech output.

        Args:
            time (str, optional): The duration of the break. Defaults to
            "500ms".

        Returns:
            str: The SSML break tag with the specified duration.
        """
        return f'<break time="{time}"/>'

    def change_rate(self, text, rate="medium"):
        """
        Changes the speaking rate of the provided text.

        This method allows for changing the speed at which the text is spoken.
        The rate can be set to values like 'x-slow', 'slow', 'medium', 'fast',
        or 'x-fast'.

        Args:
            text (str): The text whose speaking rate is to be changed.
            rate (str, optional): The desired speaking rate. Defaults to
            "medium".

        Returns:
            str: The text wrapped in an SSML prosody tag with the specified
            rate.
        """
        valid_rates = ["x-slow", "slow", "medium", "fast", "x-fast"]
        if rate not in valid_rates:
            rate = "medium"  # Default to medium if invalid rate is provided
        return f'<prosody rate="{rate}">{text}</prosody>'

    def adjust_volume(self, text, volume="medium"):
        """
        Adjusts the volume of the provided text.

        This method is used to adjust the loudness of the speech. Volume levels
        include 'silent', 'x-soft', 'soft', 'medium', 'loud', and 'x-loud'.

        Args:
            text (str): The text whose volume is to be adjusted.
            volume (str, optional): The desired volume level. Defaults to "medium".

        Returns:
            str: The text wrapped in an SSML prosody tag with the specified volume.
        """
        valid_volumes = ["silent", "x-soft", "soft", "medium", "loud", "x-loud"]
        if volume not in valid_volumes:
            volume = "medium"  # Default to medium if invalid volume is provided
        return f'<prosody volume="{volume}">{text}</prosody>'

    def convert(self, text):
        """
        Converts plain text to an SSML string using the specified voice.

        This method wraps the given text in standard SSML tags, including the
        specified voice name. It's useful for converting plain text into a
        format suitable for speech synthesis.

        Args:
            text (str): The text to be converted to SSML.

        Returns:
            str: The text converted into an SSML format.
        """
        ssml = (
            f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">\n'
            f'  <voice name="{self.voice_name}">\n'
            f'    {text}\n'
            '  </voice>\n'
            '</speak>'
        )
        return ssml
