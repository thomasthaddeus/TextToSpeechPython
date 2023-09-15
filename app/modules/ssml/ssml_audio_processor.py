"""ssml_audio_processor.py

_summary_

_extended_summary_
"""

import os
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesisOutputFormat, SpeechSynthesizer
from api.azure_tts_api import AzureTTSAPI

# Use the above classes
SUBSCRIPTION_KEY = 'YOUR_AZURE_SUBSCRIPTION_KEY'
REGION = 'YOUR_AZURE_REGION'


class SSMLAudioProcessor:
    """
     _summary_

    _extended_summary_
    """

    def __init__(self, tts_api, output_dir, base_filename):
        """
        __init__ _summary_

        _extended_summary_

        Args:
            tts_api (_type_): A hypothetical TTS API class instance.
            output_dir (_type_): Directory where audio files will be saved.
            base_filename (_type_): The base filename (without extension).
        """
        self.tts_api = tts_api
        self.output_dir = output_dir
        self.base_filename = base_filename
        self.counter = 0  # Counter to append to filenames

    def generate_and_save_audio(self, ssml):
        """
        Generate and save the audio file from SSML.

        _extended_summary_

        Args:
            ssml (_type_): _description_
        """
        audio_data = self.tts_api.get_audio_from_ssml(ssml)

        filename = f"{self.base_filename}_{self.counter}.mp3"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(audio_data)

        self.counter += 1


tts_api = AzureTTSAPI(SUBSCRIPTION_KEY, REGION)
processor = SSMLAudioProcessor(tts_api, './output', 'sample_audio')

audio_effects = SSMLAudioEffects()
text_list = ["Hello, how are you?", "Goodbye!", "See you soon!"]

for text in text_list:
    ssml = audio_effects.add_background_sound(
        text,
        "http://example.com/background.mp3"
    )
    processor.generate_and_save_audio(ssml)
