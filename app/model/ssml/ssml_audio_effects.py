"""
SSML Audio Effects Module

This module provides a class, SSMLAudioEffects, which offers a variety of
methods for adding audio effects to text using SSML (Speech Synthesis Markup
Language). It allows for the incorporation of sound effects, background music,
volume adjustments, and other audio manipulations in text-to-speech
applications.

SSMLAudioEffects is designed to enhance the expressiveness and naturalness of
synthesized speech by providing easy-to-use methods for common SSML
enhancements. These include playing audio clips, adding background sounds,
fading in/out effects, and inserting pauses. The class can be utilized in any
application where SSML is supported and a more dynamic speech output is desired.
"""


class SSMLAudioEffects:
    """
    A class for adding various audio effects to SSML.

    This class provides methods for manipulating SSML to include audio effects
    such as sound effects, background music, and volume fades. It is useful for
    enhancing the expressiveness of speech in text-to-speech applications.
    """

    def __init__(self) -> None:
        """
        Initialize the SSMLAudioEffects class.

        This initializer currently doesn't set any instance variables or
        configurations. It can be extended in the future for more advanced
        configurations.
        """
        pass

    def play_audio(self, src):
        """
        Embed an audio clip within SSML using a provided source URL or file
        path.

        Args:
            src (str): URL or path to the audio source.

        Returns:
            str: SSML string to play the specified audio clip.
        """
        return f'<audio src="{src}"/>'

    def sound_effect(self, effect_name):
        """
        Play a predefined sound effect based on the provided effect name.

        Args:
            effect_name (str): Name of the sound effect to play.

        Raises:
            ValueError: If the effect name is not recognized or available.

        Returns:
            str: SSML string to play the specified sound effect.

        Note:
            This method currently uses a placeholder mapping of effect names to
            URLs. It should be updated with actual URLs or paths to sound
            effects.
        TODO: update effects to use actual URL
        """
        effects = {
            "chime": "http://example.com/chime.wav",
            "buzz": "http://example.com/buzz.wav",
            # Add more effects here
        }

        if effect_name in effects:
            return self.play_audio(effects[effect_name])
        else:
            raise ValueError(f"Effect {effect_name} not found!")

    def add_background_sound(self, text, sound_url, sound_level="medium"):
        """
        Add background sound to a given text.

        Args:
            text (str): The text to be spoken.
            sound_url (str): URL of the background sound to play.
            sound_level (str, optional): Volume level of the background sound.
            Defaults to "medium".

        Returns:
            str: SSML string with the specified background sound.
        """
        return f'<audio src="{sound_url}" soundLevel="{sound_level}">{text}</audio>'

    def fade_in(self, text, duration="2s"):
        """
        Apply a fade-in effect to the speech for the specified duration.

        Args:
            text (str): The text to be spoken.
            duration (str, optional): Duration of the fade-in effect. Defaults to "2s".

        Returns:
            str: SSML string with the fade-in effect applied.
        """
        return f'<audio fadeOutDur="{duration}">{text}</audio>'

    def fade_out(self, text, duration="2s"):
        """
        Apply a fade-out effect to the speech for the specified duration.

        Args:
            text (str): The text to be spoken.
            duration (str, optional): Duration of the fade-out effect. Defaults to "2s".

        Returns:
            str: SSML string with the fade-out effect applied.
        """
        return f'<audio fadeInDur="{duration}">{text}</audio>'

    def insert_pause(self, text, pause_duration="1s", before=True):
        """
        Insert a pause before or after the given text.

        Args:
            text (str): The text around which the pause is to be inserted.
            pause_duration (str, optional): Duration of the pause. Defaults to "1s".
            before (bool, optional): Whether to insert the pause before the text. Defaults to True.

        Returns:
            str: SSML string with the pause inserted.
        """
        pause_tag = f'<break time="{pause_duration}"/>'
        return f"{pause_tag}{text}" if before else f"{text}{pause_tag}"

    def repeat_audio(self, text, count=2):
        """
        Repeat a certain segment of audio a specified number of times.

        Args:
            text (str): The text (or SSML) to be repeated.
            count (int, optional): Number of times to repeat the segment. Defaults to 2.

        Returns:
            str: SSML string with the repeat effect applied.
        """
        return f'<audio repeatCount="{count}">{text}</audio>'
