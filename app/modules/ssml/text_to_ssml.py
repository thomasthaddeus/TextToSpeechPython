"""text_to_ssml.py

_summary_

_extended_summary_

Returns:
    _type_: _description_
"""

class TextToSSML:
    def __init__(self, voice_name="en-US-Guy24kRUS"):
        """
        Initialize with a default voice. You can change the voice_name as per
        your requirements. See Microsoft's documentation for available voice
        names.
        """
        self.voice_name = voice_name


    def add_emphasis(self, text, level="moderate"):
        """
        Adds emphasis to the given text. Levels can be: "strong", "moderate", or "reduced".
        """
        return f'<emphasis level="{level}">{text}</emphasis>'

    def add_break(self, time="500ms"):
        """
        Adds a break. You can specify time in milliseconds or in seconds like "1s".
        """
        return f'<break time="{time}"/>'

    def change_rate(self, text, rate="medium"):
        """
        Changes the speaking rate. Rate can be: "x-slow", "slow", "medium", "fast", "x-fast".
        """
        rate = ["x-slow", "slow", "medium", "fast", "x-fast"]
        return f'<prosody rate="{rate[2]}">{text}</prosody>'

    def adjust_volume(self, text, volume="medium"):
        """
        Adjusts the volume. Volume can be: "silent", "x-soft", "soft", "medium", "loud", "x-loud".
        """
        volume = ["silent", "x-soft", "soft", "medium", "loud", "x-loud"]
        return f'<prosody volume="{volume[0]}">{text}</prosody>'

    def convert(self, text):
        """
        Convert plain text to SSML.
        """
        ssml = f"""
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <voice name="{self.voice_name}">
        {text}
    </voice>
</speak>
"""
        return ssml
