"""ssml_audio_processor.py

This module provides a class for processing Speech Synthesis Markup Language
(SSML) to generate audio using Azure's Text-to-Speech (TTS) service. It
includes functionalities for generating audio from SSML strings and saving them
as files.

The SSMLAudioProcessor class utilizes an instance of AzureTTSAPI to convert
SSML strings into audio. It supports saving the generated audio into specified
directories with a base filename and an incremental counter to differentiate
between files.

Example:

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
"""

import os
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesisOutputFormat, SpeechSynthesizer
from api.azure_tts_api import AzureTTSAPI

# Use the above classes
SUBSCRIPTION_KEY = 'YOUR_AZURE_SUBSCRIPTION_KEY'
REGION = 'YOUR_AZURE_REGION'


class SSMLAudioProcessor:
    """
    A class to process SSML for audio generation using Azure Text-to-Speech services.

    This class provides methods to generate audio from SSML strings and to save
    the audio in a specified directory.

    Attributes:
        tts_api (AzureTTSAPI): An instance of AzureTTSAPI for TTS operations.
        output_dir (str): Directory where generated audio files will be saved.
        base_filename (str): Base filename for saving audio files.
        counter (int): A counter to append to filenames for uniqueness.
    """

    def __init__(self, tts_api, output_dir, base_filename):
        """
        Initializes the SSMLAudioProcessor with AzureTTSAPI instance, output directory, and base filename.

        Args:
            tts_api (AzureTTSAPI): An instance of AzureTTSAPI for TTS operations.
            output_dir (str): Directory where generated audio files will be saved.
            base_filename (str): Base filename for saving audio files.
        """
        self.tts_api = tts_api
        self.output_dir = output_dir
        self.base_filename = base_filename
        self.counter = 0  # Counter to append to filenames

    def generate_and_save_audio(self, ssml):
        """
        Generates audio from an SSML string and saves it as a file in the specified output directory.

        Args:
            ssml (str): The SSML string from which audio will be generated.

        Extended Summary:
            This method utilizes the tts_api instance to convert the provided SSML string
            into audio data. It then saves this audio data to a file, naming it using
            the base_filename and an incremental counter.
        """
        audio_data = self.tts_api.get_audio_from_ssml(ssml)

        filename = f"{self.base_filename}_{self.counter}.mp3"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(audio_data)

        self.counter += 1
