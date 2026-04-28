"""Helpers for loading offline/local TTS settings from a dedicated config file."""

import configparser
import os


def get_local_tts_settings(config_file_path):
    """Read local offline TTS settings from an INI file when present."""
    config = configparser.ConfigParser()

    if not config_file_path:
        raise ValueError("Local TTS config path is required.")

    if not os.path.exists(config_file_path):
        raise FileNotFoundError(
            f"Local TTS config file not found at '{config_file_path}'"
        )

    config.read(config_file_path)

    if "LOCAL_TTS" not in config:
        raise ValueError("LOCAL_TTS settings not found in local TTS config file")

    local_section = config["LOCAL_TTS"]
    return {
        "driver_name": local_section.get("driver_name", "auto"),
    }
