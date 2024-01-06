class AzureTTSAPI:

    def __init__(self, subscription_key, region):
        """
        Initialize Azure TTS API client.
        """
        speech_config = SpeechConfig(subscription=subscription_key, region=region)
        speech_config.set_speech_synthesis_output_format(SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
        self.synthesizer = SpeechSynthesizer(speech_config=speech_config)

    def get_audio_from_ssml(self, ssml):
        """
        Convert SSML to audio and return the audio data.
        """
        result = self.synthesizer.speak_ssml_async(ssml).get()
        return result.audio_data