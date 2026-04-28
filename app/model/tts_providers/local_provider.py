"""Offline pyttsx3-backed implementation of the generic provider API."""

from pathlib import Path
import tempfile

from app.model.tts_providers.models import (
    TTSProviderCapabilities,
    TTSRequest,
    TTSResult,
)


class LocalPythonTTSProvider:
    """Wrap a local pyttsx3 engine behind the shared provider interface."""

    provider_name = "local"

    def __init__(self, driver_name="auto", engine_factory=None):
        self.driver_name = driver_name or "auto"
        self._engine_factory = engine_factory or self._default_engine_factory

    def synthesize(self, request: TTSRequest) -> TTSResult:
        if request.use_ssml:
            raise ValueError(
                "Offline Python TTS does not support SSML input. Use plain text instead."
            )

        engine = self._create_engine()
        self._apply_request_settings(engine, request)

        output_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                output_path = temp_file.name

            engine.save_to_file(request.text, output_path)
            engine.runAndWait()
            audio_data = Path(output_path).read_bytes()
        except Exception as error:
            raise RuntimeError(self._format_error(error)) from error
        finally:
            self._stop_engine(engine)
            if output_path:
                Path(output_path).unlink(missing_ok=True)

        return TTSResult(
            audio_data=audio_data,
            provider_name=self.provider_name,
            output_format="mp3",
            request=request,
        )

    def get_capabilities(self) -> TTSProviderCapabilities:
        return TTSProviderCapabilities(
            supports_ssml=False,
            supports_style_prompt=False,
            supports_multi_speaker=False,
            supports_offline=True,
            supports_streaming=False,
            supported_formats=("mp3",),
            max_input_size=None,
        )

    def list_voices(self, engine=None, language_code=None) -> tuple[str, ...]:
        del engine
        del language_code
        pyttsx_engine = self._create_engine()
        try:
            voices = pyttsx_engine.getProperty("voices") or []
            voice_ids = []
            for voice in voices:
                voice_id = getattr(voice, "id", None)
                if voice_id:
                    voice_ids.append(str(voice_id))
            return tuple(voice_ids)
        finally:
            self._stop_engine(pyttsx_engine)

    def _create_engine(self):
        if self.driver_name == "auto":
            return self._engine_factory(None)
        return self._engine_factory(self.driver_name)

    def _default_engine_factory(self, driver_name):
        import pyttsx3

        if driver_name:
            return pyttsx3.init(driverName=driver_name)
        return pyttsx3.init()

    def _apply_request_settings(self, engine, request):
        if request.voice:
            engine.setProperty("voice", request.voice)

        rate = request.metadata.get("rate")
        if rate is not None:
            engine.setProperty("rate", rate)

        volume = request.metadata.get("volume")
        if volume is not None:
            engine.setProperty("volume", volume)

    def _stop_engine(self, engine):
        stop_method = getattr(engine, "stop", None)
        if callable(stop_method):
            try:
                stop_method()
            except Exception:
                return

    def _format_error(self, error):
        error_text = str(error).strip()
        if "driver" in error_text.lower():
            return (
                "Offline Python TTS could not initialize the configured speech engine driver."
            )
        if error_text:
            return f"Offline Python TTS request failed: {error_text}"
        return "Offline Python TTS request failed."
