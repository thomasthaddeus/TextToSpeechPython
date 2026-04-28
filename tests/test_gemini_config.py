from app.model.api.gemini_config import get_gemini_settings
from app.model.app_settings import AppSettings
from app.model.tts_providers.factory import resolve_tts_provider_config


def test_get_gemini_settings_reads_dedicated_config_file(runtime_tmp_path):
    service_account_path = runtime_tmp_path / "service-account.json"
    service_account_path.write_text("{}", encoding="utf-8")
    config_path = runtime_tmp_path / ".gemini.env"
    config_path.write_text(
        "[GEMINI]\n"
        "project_id = sample-project\n"
        f"service_account_json = {service_account_path}\n"
        "region = us-central1\n",
        encoding="utf-8",
    )

    settings = get_gemini_settings(str(config_path))

    assert settings["project_id"] == "sample-project"
    assert settings["service_account_json"] == str(service_account_path)
    assert settings["region"] == "us-central1"


def test_resolve_tts_provider_config_uses_dedicated_gemini_file(runtime_tmp_path):
    service_account_path = runtime_tmp_path / "service-account.json"
    service_account_path.write_text("{}", encoding="utf-8")
    config_path = runtime_tmp_path / "gemini-provider.ini"
    config_path.write_text(
        "[GEMINI]\n"
        "project_id = provider-project\n"
        f"service_account_json = {service_account_path}\n"
        "region = eu\n",
        encoding="utf-8",
    )
    app_settings = AppSettings(
        tts_provider="gemini",
        voice="Kore",
        gemini_config_path=str(config_path),
        gemini_model="gemini-2.5-pro-tts",
        gemini_language_code="en-US",
        gemini_style_prompt="Say the following in a documentary tone.",
    )

    provider_config = resolve_tts_provider_config(app_settings)

    assert provider_config is not None
    assert provider_config.provider_name == "gemini"
    assert provider_config.api_config_path == str(config_path)
    assert provider_config.credentials["project_id"] == "provider-project"
    assert provider_config.credentials["service_account_json"] == str(
        service_account_path
    )
    assert provider_config.credentials["region"] == "eu"
    assert provider_config.options["model"] == "gemini-2.5-pro-tts"
    assert provider_config.options["language_code"] == "en-US"
    assert provider_config.options["style_prompt"] == (
        "Say the following in a documentary tone."
    )


def test_resolve_tts_provider_config_returns_none_when_gemini_file_missing(
    runtime_tmp_path,
):
    missing_path = runtime_tmp_path / "missing-gemini.ini"
    app_settings = AppSettings(
        tts_provider="gemini",
        gemini_config_path=str(missing_path),
    )

    provider_config = resolve_tts_provider_config(app_settings)

    assert provider_config is None
