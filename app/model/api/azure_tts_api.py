"""azure_tts_api.py
_summary_

_extended_summary_

Returns:
    _type_: _description_
"""

import azure.cognitiveservices.speech as speechsdk

class AzureTTSAPI:
    """
     _summary_

    _extended_summary_
    """
    def __init__(self, subscription_key, region):
        """
        Initialize Azure TTS API client.

        _extended_summary_

        Args:
            subscription_key (_type_): _description_
            region (_type_): _description_
        """
        speech_config = SpeechConfig(subscription=subscription_key, region=region)
        speech_config.set_speech_synthesis_output_format(SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
        self.synthesizer = SpeechSynthesizer(speech_config=speech_config)

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