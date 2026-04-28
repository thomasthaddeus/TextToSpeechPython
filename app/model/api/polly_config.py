"""Helpers for loading Amazon Polly credentials from a dedicated config file."""

import configparser
import os


def get_polly_settings(config_file_path):
    """Read AWS Polly credentials and region settings from an INI file."""
    config = configparser.ConfigParser()

    if not config_file_path:
        raise ValueError("Amazon Polly config path is required.")

    if not os.path.exists(config_file_path):
        raise FileNotFoundError(
            f"Amazon Polly config file not found at '{config_file_path}'"
        )

    config.read(config_file_path)

    if "POLLY" not in config:
        raise ValueError("POLLY settings not found in Amazon Polly config file")

    polly_section = config["POLLY"]
    access_key_id = polly_section.get("aws_access_key_id")
    secret_access_key = polly_section.get("aws_secret_access_key")
    session_token = polly_section.get("aws_session_token", "")
    region = polly_section.get("region")

    if not access_key_id:
        raise ValueError(
            "Amazon Polly config file is missing aws_access_key_id."
        )

    if not secret_access_key:
        raise ValueError(
            "Amazon Polly config file is missing aws_secret_access_key."
        )

    if not region:
        raise ValueError("Amazon Polly config file is missing region.")

    return {
        "aws_access_key_id": access_key_id,
        "aws_secret_access_key": secret_access_key,
        "aws_session_token": session_token,
        "region": region,
    }
