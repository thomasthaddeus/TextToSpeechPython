""" tts_processor.py
_summary_

_extended_summary_

Returns:
    _type_: _description_
"""

from api.azure_tts_api import AzureTTSAPI
from ssml_audio_processor import SSMLAudioProcessor


class TTSProcessor:
    """
     _summary_

    _extended_summary_
    """
    def __init__(self, api_config_path, ssml_config_path):
        """
        Initialize the Azure TTS API and SSML processor with configuration paths

        _extended_summary_

        Args:
            api_config_path (_type_): _description_
            ssml_config_path (_type_): _description_
        """
        self.azure_tts_api = AzureTTSAPI(api_config_path)
        self.ssml_processor = SSMLAudioProcessor(ssml_config_path)

    def text_to_speech(self, text, use_ssml=False):
        """
        Converts text to speech.

        Args:
            text (str): The text to be converted to speech.
            use_ssml (bool): Flag to determine whether the text is SSML formatted.

        Returns:
            bytes: The audio data in byte format.
        """
        if use_ssml:
            # Process the SSML text
            ssml_text = self.ssml_processor.process_ssml(text)
            audio_data = self.azure_tts_api.convert_ssml_to_audio(ssml_text)
        else:
            # Directly convert text to audio
            audio_data = self.azure_tts_api.convert_text_to_audio(text)

        return audio_data

    # Additional methods can be added here for more specific TTS processing tasks.
