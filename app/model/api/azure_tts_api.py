"""azure_tts_api.py
_summary_

_extended_summary_

Returns:
    _type_: _description_
"""

import azure.cognitiveservices.speech as speechsdk
from app.model.api.api_config import get_api_settings


class AzureTTSAPI:
    """
     _summary_

    _extended_summary_
    """
    def __init__(self, subscription_key, region=None):
        """
        Initialize Azure TTS API client.

        _extended_summary_

        Args:
            subscription_key (_type_): Azure subscription key or config path.
            region (_type_): Azure region. If omitted, subscription_key is
                treated as a config file path.
        """
        if region is None:
            subscription_key, region = get_api_settings(subscription_key)

        speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key,
            region=region,
        )
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
        self.synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config
        )

    def get_audio_from_ssml(self, ssml):
        """
        Convert SSML to audio and return the audio data.

        _extended_summary_

        Args:
            ssml (_type_): _description_

        Returns:
            _type_: _description_
        """
        result = self.synthesizer.speak_ssml_async(ssml).get()
        return result.audio_data

    def get_audio_from_text(self, text):
        """
        Convert plain text to audio and return the audio data.
        """
        result = self.synthesizer.speak_text_async(text).get()
        return result.audio_data

    def convert_ssml_to_audio(self, ssml):
        """
        Backward-compatible alias for SSML synthesis.
        """
        return self.get_audio_from_ssml(ssml)

    def convert_text_to_audio(self, text):
        """
        Backward-compatible alias for plain-text synthesis.
        """
        return self.get_audio_from_text(text)
