"""
_summary_

_extended_summary_

Raises:
    ValueError: _description_

Returns:
    _type_: _description_
"""

from azure.cognitiveservices.speech.audio import AudioOutputConfig

class SSMLAudioEffects:
    def play_audio(self, src):
        """
        Play an audio clip from a given URL or path.
        """
        return f'<audio src="{src}"/>'

    def sound_effect(self, effect_name):
        """
        Placeholder to play a sound effect. This should ideally link to
        specific audio files or use specific SSML tags.
        Currently, it just demonstrates the structure.
        """
        # Map of effect_name to its source URL or path
        effects = {
            'chime': 'http://example.com/chime.wav',
            'buzz': 'http://example.com/buzz.wav',
            # Add more effects here
        }

        if effect_name in effects:
            return self.play_audio(effects[effect_name])
        else:
            raise ValueError(f"Effect {effect_name} not found!")

    def add_background_sound(self, text, sound_url, sound_level="medium"):
        """Play a background sound while the text is spoken."""
        return f'<audio src="{sound_url}" soundLevel="{sound_level}">{text}</audio>'

    def fade_in(self, text, duration="2s"):
        """Gradually increase volume at the start."""
        return f'<audio fadeOutDur="{duration}">{text}</audio>'

    def fade_out(self, text, duration="2s"):
        """Gradually decrease volume at the end."""
        return f'<audio fadeInDur="{duration}">{text}</audio>'

    def insert_pause(self, text, pause_duration="1s", before=True):
        """Insert a pause before or after a certain text."""
        pause_tag = f'<break time="{pause_duration}"/>'
        return f'{pause_tag}{text}' if before else f'{text}{pause_tag}'

    def repeat_audio(self, text, count=2):
        """Repeat a certain segment of audio."""
        return f'<audio repeatCount="{count}">{text}</audio>'
