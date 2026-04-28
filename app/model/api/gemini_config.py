"""Helpers for loading Gemini TTS settings from a dedicated config file."""

import configparser
import os


def get_gemini_settings(config_file_path):
    """Read Google Cloud Gemini TTS settings from an INI file."""
    config = configparser.ConfigParser()

    if not config_file_path:
        raise ValueError("Gemini TTS config path is required.")

    if not os.path.exists(config_file_path):
        raise FileNotFoundError(
            f"Gemini TTS config file not found at '{config_file_path}'"
        )

    config.read(config_file_path)

    if "GEMINI" not in config:
        raise ValueError("GEMINI settings not found in Gemini config file")

    gemini_section = config["GEMINI"]
    project_id = gemini_section.get("project_id")
    service_account_json = gemini_section.get("service_account_json")
    region = gemini_section.get("region", "global")

    if not project_id:
        raise ValueError("Gemini config file is missing project_id.")

    if not service_account_json:
        raise ValueError("Gemini config file is missing service_account_json.")

    if not os.path.exists(service_account_json):
        raise FileNotFoundError(
            f"Gemini service account file not found at '{service_account_json}'"
        )

    return {
        "project_id": project_id,
        "service_account_json": service_account_json,
        "region": region,
    }
