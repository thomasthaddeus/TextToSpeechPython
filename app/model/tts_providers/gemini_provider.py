"""Google Cloud Gemini-TTS implementation of the generic provider API."""

from app.model.tts_providers.models import (
    TTSProviderCapabilities,
    TTSRequest,
    TTSResult,
)


class GeminiTTSProvider:
    """Wrap Google Cloud Gemini-TTS behind the shared provider interface."""

    provider_name = "gemini"
    DEFAULT_MODEL = "gemini-2.5-flash-tts"
    DEFAULT_LANGUAGE_CODE = "en-US"
    MAX_FIELD_BYTES = 4000
    MAX_TOTAL_BYTES = 8000

    def __init__(
        self,
        project_id,
        service_account_json,
        region="global",
        model=DEFAULT_MODEL,
        client=None,
    ):
        self.project_id = project_id
        self.service_account_json = service_account_json
        self.region = region or "global"
        self.model = model or self.DEFAULT_MODEL
        self.client = client or self._build_client()

    def _build_client(self):
        from google.api_core.client_options import ClientOptions
        from google.cloud import texttospeech
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_json,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        ).with_quota_project(self.project_id)
        api_endpoint = (
            f"{self.region}-texttospeech.googleapis.com"
            if self.region != "global"
            else "texttospeech.googleapis.com"
        )
        return texttospeech.TextToSpeechClient(
            credentials=credentials,
            client_options=ClientOptions(api_endpoint=api_endpoint),
        )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        prompt = str(request.metadata.get("style_prompt", "") or "").strip()
        text = request.text
        language_code = str(
            request.metadata.get("language_code", self.DEFAULT_LANGUAGE_CODE)
        )
        model = str(request.metadata.get("model", self.model))
        multi_speaker_map = request.metadata.get("speaker_voice_map") or {}

        self._validate_prompt_and_text(prompt, text, multi_speaker_map)

        if request.use_ssml:
            raise ValueError(
                "Gemini TTS uses prompt-controlled text input and does not accept SSML."
            )

        try:
            response = self.client.synthesize_speech(
                input=self._build_synthesis_input(prompt, text, multi_speaker_map),
                voice=self._build_voice_selection(
                    voice=request.voice,
                    language_code=language_code,
                    model=model,
                    multi_speaker_map=multi_speaker_map,
                ),
                audio_config=self._build_audio_config(),
            )
        except Exception as error:
            raise RuntimeError(
                self._format_error(error, model=model, region=self.region)
            ) from error

        return TTSResult(
            audio_data=response.audio_content,
            provider_name=self.provider_name,
            output_format="mp3",
            request=request,
            raw_result={
                "model": model,
                "region": self.region,
                "language_code": language_code,
            },
        )

    def get_capabilities(self) -> TTSProviderCapabilities:
        return TTSProviderCapabilities(
            supports_ssml=False,
            supports_style_prompt=True,
            supports_multi_speaker=True,
            supports_offline=False,
            supports_streaming=False,
            supported_formats=("mp3", "linear16", "alaw", "mulaw", "ogg_opus", "pcm"),
            max_input_size=self.MAX_TOTAL_BYTES,
        )

    def list_voices(self, engine=None, language_code=None) -> tuple[str, ...]:
        del engine
        del language_code
        from app.model.tts_providers.voice_catalog import GEMINI_VOICE_SUGGESTIONS

        return GEMINI_VOICE_SUGGESTIONS

    def _build_synthesis_input(self, prompt, text, multi_speaker_map):
        from google.cloud import texttospeech

        if multi_speaker_map:
            return texttospeech.SynthesisInput(
                text=text,
                prompt=prompt or None,
            )

        return texttospeech.SynthesisInput(
            text=text,
            prompt=prompt or None,
        )

    def _build_voice_selection(
        self,
        voice,
        language_code,
        model,
        multi_speaker_map,
    ):
        from google.cloud import texttospeech

        if multi_speaker_map:
            speaker_voice_configs = [
                texttospeech.MultispeakerPrebuiltVoice(
                    speaker_alias=str(alias),
                    speaker_id=str(speaker_voice),
                )
                for alias, speaker_voice in multi_speaker_map.items()
            ]
            return texttospeech.VoiceSelectionParams(
                language_code=language_code,
                model_name=model,
                multi_speaker_voice_config=texttospeech.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=speaker_voice_configs
                ),
            )

        if not voice:
            raise ValueError("Gemini TTS requires a voice selection.")

        return texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice,
            model_name=model,
        )

    def _build_audio_config(self):
        from google.cloud import texttospeech

        return texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

    def _validate_prompt_and_text(self, prompt, text, multi_speaker_map):
        prompt_bytes = len(prompt.encode("utf-8"))
        text_bytes = len(text.encode("utf-8"))
        total_bytes = prompt_bytes + text_bytes

        if prompt_bytes > self.MAX_FIELD_BYTES:
            raise ValueError(
                "Gemini style prompt exceeds the 4,000-byte limit for the prompt field."
            )
        if text_bytes > self.MAX_FIELD_BYTES:
            if multi_speaker_map:
                raise ValueError(
                    "Gemini multi-speaker input exceeds the 4,000-byte limit for dialogue text."
                )
            raise ValueError(
                "Gemini input text exceeds the 4,000-byte limit for the text field."
            )
        if total_bytes > self.MAX_TOTAL_BYTES:
            raise ValueError(
                "Gemini prompt and text exceed the combined 8,000-byte request limit."
            )

    def _format_error(self, error, model, region):
        error_text = str(error).strip()
        lowered = error_text.lower()

        if "permission" in lowered or "403" in lowered:
            return (
                "Gemini TTS authentication failed. Verify the service account, "
                "project access, and aiplatform.endpoints.predict permission."
            )
        if "not found" in lowered and "model" in lowered:
            return f"Gemini model '{model}' is not available in region '{region}'."
        if "api endpoint" in lowered or "dns" in lowered or "endpoint" in lowered:
            return f"Gemini region '{region}' could not be reached."
        if "voice" in lowered:
            return "Gemini TTS rejected the selected voice for the current model or locale."
        if error_text:
            return f"Gemini TTS request failed: {error_text}"
        return "Gemini TTS request failed."
