from pathlib import Path

from app.model.api.polly_config import get_polly_settings
from app.model.app_settings import AppSettings
from app.model.tts_providers.factory import resolve_tts_provider_config


def test_get_polly_settings_reads_dedicated_config_file(runtime_tmp_path):
    config_path = runtime_tmp_path / ".polly.env"
    config_path.write_text(
        "[POLLY]\n"
        "aws_access_key_id = example-key\n"
        "aws_secret_access_key = example-secret\n"
        "aws_session_token = example-token\n"
        "region = us-east-1\n",
        encoding="utf-8",
    )

    settings = get_polly_settings(str(config_path))

    assert settings["aws_access_key_id"] == "example-key"
    assert settings["aws_secret_access_key"] == "example-secret"
    assert settings["aws_session_token"] == "example-token"
    assert settings["region"] == "us-east-1"


def test_resolve_tts_provider_config_uses_dedicated_polly_file(runtime_tmp_path):
    config_path = runtime_tmp_path / "aws-polly.ini"
    config_path.write_text(
        "[POLLY]\n"
        "aws_access_key_id = provider-key\n"
        "aws_secret_access_key = provider-secret\n"
        "region = us-west-2\n",
        encoding="utf-8",
    )
    app_settings = AppSettings(
        tts_provider="polly",
        voice="Joanna",
        polly_config_path=str(config_path),
        polly_engine="generative",
    )

    provider_config = resolve_tts_provider_config(app_settings)

    assert provider_config is not None
    assert provider_config.provider_name == "polly"
    assert provider_config.api_config_path == str(config_path)
    assert provider_config.credentials["aws_access_key_id"] == "provider-key"
    assert provider_config.credentials["aws_secret_access_key"] == "provider-secret"
    assert provider_config.credentials["region"] == "us-west-2"
    assert provider_config.options["engine"] == "generative"


def test_resolve_tts_provider_config_returns_none_when_polly_file_missing(
    runtime_tmp_path,
):
    missing_path = runtime_tmp_path / "missing-polly.ini"
    app_settings = AppSettings(
        tts_provider="polly",
        polly_config_path=str(missing_path),
    )

    provider_config = resolve_tts_provider_config(app_settings)

    assert provider_config is None
