"""Helpers for turning text into SSML and optionally saving synthesized audio."""

import os
from app.model.ssml.ssml_config import SSMLConfig
from app.model.ssml.text_to_ssml import TextToSSML


class SSMLAudioProcessor:
    """
    Build SSML snippets and optionally save synthesized audio to disk.
    """

    def __init__(
        self,
        tts_api=None,
        output_dir=None,
        base_filename="audio",
        voice_name=None,
    ):
        """
        Initialize the SSML processor.

        Args:
            tts_api (AzureTTSAPI | None): Optional API client used for saving
                synthesized SSML to audio files.
            output_dir (str | None): Directory where generated audio files
                will be saved.
            base_filename (str): Base filename for saving audio files.
            voice_name (str | None): Voice override for generated SSML.
        """
        self.tts_api = tts_api
        self.output_dir = output_dir
        self.base_filename = base_filename
        self.counter = 0
        self.ssml_config = SSMLConfig()

        if voice_name:
            self.ssml_config.set_voice(voice_name)

        self.text_converter = TextToSSML(
            voice_name=self.ssml_config.get_voice()
        )

    def convert_text_to_ssml(self, text):
        """
        Convert plain text into a basic SSML document.
        """
        return self.text_converter.convert(text)

    def process_ssml(self, text):
        """
        Return valid SSML, converting plain text when needed.
        """
        stripped_text = text.lstrip()
        if stripped_text.startswith("<speak"):
            return text
        return self.convert_text_to_ssml(text)

    def generate_and_save_audio(self, ssml):
        """
        Generate audio from SSML and save it to disk.

        Args:
            ssml (str): The SSML string from which audio will be generated.
        """
        if self.tts_api is None:
            raise ValueError("A configured AzureTTSAPI instance is required.")

        if not self.output_dir:
            raise ValueError("An output directory is required to save audio.")

        audio_data = self.tts_api.get_audio_from_ssml(ssml)
        os.makedirs(self.output_dir, exist_ok=True)

        filename = f"{self.base_filename}_{self.counter}.mp3"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "wb") as file:
            file.write(audio_data)

        self.counter += 1
        return filepath
