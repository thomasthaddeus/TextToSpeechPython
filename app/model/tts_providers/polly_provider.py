"""Amazon Polly implementation of the generic text-to-speech provider API."""

from app.model.tts_providers.models import (
    TTSProviderCapabilities,
    TTSRequest,
    TTSResult,
)


class PollyTTSProvider:
    """Wrap Amazon Polly behind the shared provider interface."""

    provider_name = "polly"
    DEFAULT_OUTPUT_FORMAT = "mp3"
    DEFAULT_ENGINE = "neural"

    def __init__(
        self,
        aws_access_key_id,
        aws_secret_access_key,
        region,
        aws_session_token="",
        engine=DEFAULT_ENGINE,
        client=None,
    ):
        self.region = region
        self.engine = engine or self.DEFAULT_ENGINE
        self.client = client or self._build_client(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region=region,
        )

    def _build_client(
        self,
        aws_access_key_id,
        aws_secret_access_key,
        aws_session_token,
        region,
    ):
        import boto3

        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token or None,
            region_name=region,
        )
        return session.client("polly", region_name=region)

    def synthesize(self, request: TTSRequest) -> TTSResult:
        voice_id = request.voice or self._extract_voice_name_from_ssml(request.text)
        if not voice_id:
            raise ValueError("Amazon Polly requires a voice selection.")

        output_format = self._normalize_output_format(request.output_format)
        engine = str(request.metadata.get("engine", self.engine))
        sample_rate = str(
            request.metadata.get(
                "sample_rate",
                self._default_sample_rate(output_format, engine),
            )
        )
        params = {
            "VoiceId": voice_id,
            "OutputFormat": output_format,
            "Text": request.text,
            "TextType": "ssml" if request.use_ssml else "text",
            "Engine": engine,
            "SampleRate": sample_rate,
        }
        language_code = request.metadata.get("language_code")
        if language_code:
            params["LanguageCode"] = str(language_code)

        try:
            response = self.client.synthesize_speech(**params)
            audio_data = response["AudioStream"].read()
        except Exception as error:
            raise RuntimeError(self._format_error(error, voice_id, engine)) from error

        return TTSResult(
            audio_data=audio_data,
            provider_name=self.provider_name,
            output_format=output_format,
            request=request,
            raw_result={
                "request_characters": response.get("RequestCharacters"),
                "content_type": response.get("ContentType"),
            },
        )

    def get_capabilities(self) -> TTSProviderCapabilities:
        return TTSProviderCapabilities(
            supports_ssml=True,
            supports_style_prompt=False,
            supports_multi_speaker=False,
            supports_offline=False,
            supports_streaming=False,
            supported_formats=(
                "mp3",
                "ogg_vorbis",
                "ogg_opus",
                "pcm",
                "mulaw",
                "alaw",
            ),
            max_input_size=6000,
        )

    def list_voices(self, engine=None, language_code=None):
        """Fetch voice IDs available to the configured Polly region."""
        params = {}
        if engine:
            params["Engine"] = engine
        if language_code:
            params["LanguageCode"] = language_code

        voices = []
        next_token = None
        try:
            while True:
                if next_token:
                    params["NextToken"] = next_token
                response = self.client.describe_voices(**params)
                voices.extend(
                    voice.get("Id", "")
                    for voice in response.get("Voices", [])
                    if voice.get("Id")
                )
                next_token = response.get("NextToken")
                if not next_token:
                    break
        except Exception as error:
            raise RuntimeError(
                self._format_error(error, voice_id="voice discovery", engine=engine or self.engine)
            ) from error

        return tuple(sorted(set(voices)))

    def _normalize_output_format(self, output_format):
        normalized = str(output_format or "").strip().lower()
        if normalized in {"mp3", "ogg_vorbis", "ogg_opus", "pcm", "mulaw", "alaw"}:
            return normalized
        return self.DEFAULT_OUTPUT_FORMAT

    def _default_sample_rate(self, output_format, engine):
        if output_format == "pcm":
            return "16000"
        if output_format == "ogg_opus":
            return "48000"
        if output_format in {"mulaw", "alaw"}:
            return "8000"
        if str(engine).lower() == "standard":
            return "22050"
        return "24000"

    def _extract_voice_name_from_ssml(self, text):
        marker = 'name="'
        marker_index = text.find(marker)
        if marker_index == -1:
            return None
        start_index = marker_index + len(marker)
        end_index = text.find('"', start_index)
        if end_index == -1:
            return None
        voice_name = text[start_index:end_index].strip()
        return voice_name or None

    def _format_error(self, error, voice_id, engine):
        error_code = self._extract_error_code(error)
        error_message = self._extract_error_message(error)

        if error_code in {"InvalidSsmlException", "InvalidSsml"}:
            return (
                "Amazon Polly rejected the SSML document. Verify that the SSML "
                "tags and values are supported."
            )
        if error_code in {"EngineNotSupportedException", "EngineNotSupported"}:
            return (
                f"Amazon Polly engine '{engine}' is not supported for voice "
                f"'{voice_id}' in region '{self.region}'."
            )
        if error_code in {"InvalidVoiceIdException", "InvalidVoiceId"}:
            return (
                f"Amazon Polly voice '{voice_id}' is not available in region "
                f"'{self.region}'."
            )
        if error_code in {"TextLengthExceededException", "TextLengthExceeded"}:
            return (
                "Amazon Polly input text exceeded the SynthesizeSpeech limit of "
                "6000 total characters."
            )
        if error_code in {"UnrecognizedClientException", "InvalidClientTokenId"}:
            return "Amazon Polly credentials were rejected by AWS."
        if error_code in {"EndpointConnectionError", "UnknownEndpointError"}:
            return (
                f"Amazon Polly region '{self.region}' could not be reached. "
                "Verify the configured region."
            )
        if error_message:
            return f"Amazon Polly request failed: {error_message}"
        return "Amazon Polly request failed."

    def _extract_error_code(self, error):
        response = getattr(error, "response", None) or {}
        error_payload = response.get("Error", {})
        code = error_payload.get("Code")
        if code:
            return str(code)
        error_name = error.__class__.__name__
        if error_name:
            return error_name
        return ""

    def _extract_error_message(self, error):
        response = getattr(error, "response", None) or {}
        error_payload = response.get("Error", {})
        message = error_payload.get("Message") or response.get("message")
        if message:
            return str(message)
        return str(error).strip()
