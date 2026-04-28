from app.model.api.local_tts_config import get_local_tts_settings
from app.model.app_settings import AppSettings
from app.model.tts_providers.factory import resolve_tts_provider_config


def test_get_local_tts_settings_reads_dedicated_config_file(runtime_tmp_path):
    config_path = runtime_tmp_path / ".local_tts.env"
    config_path.write_text(
        "[LOCAL_TTS]\n"
        "driver_name = espeak\n",
        encoding="utf-8",
    )

    settings = get_local_tts_settings(str(config_path))

    assert settings["driver_name"] == "espeak"


def test_resolve_tts_provider_config_uses_local_defaults_without_config_file():
    app_settings = AppSettings(
        tts_provider="local",
        local_tts_driver_name="sapi5",
        local_tts_config_path=".missing-local.env",
    )

    provider_config = resolve_tts_provider_config(app_settings)

    assert provider_config is not None
    assert provider_config.provider_name == "local"
    assert provider_config.options["driver_name"] == "sapi5"


def test_resolve_tts_provider_config_prefers_local_config_file_values(runtime_tmp_path):
    config_path = runtime_tmp_path / "local-provider.ini"
    config_path.write_text(
        "[LOCAL_TTS]\n"
        "driver_name = nsss\n",
        encoding="utf-8",
    )
    app_settings = AppSettings(
        tts_provider="local",
        local_tts_driver_name="auto",
        local_tts_config_path=str(config_path),
    )

    provider_config = resolve_tts_provider_config(app_settings)

    assert provider_config is not None
    assert provider_config.provider_name == "local"
    assert provider_config.api_config_path == str(config_path)
    assert provider_config.options["driver_name"] == "nsss"
