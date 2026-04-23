"""api_config.py

This module provides functionality to retrieve an API key from a configuration
file.

The get_api_key function reads a specified configuration file, and fetches an
API key if available. It raises exceptions if the file is not found or if the
key is missing.

Raises:
    FileNotFoundError: Raised when the specified configuration file does not
    exist.
    ValueError: Raised when the API key is not found in the configuration file.

Returns:
    str: Returns the API key as a string.

Example:

try:
    api_key = get_api_key()
    print(f"API Key: {api_key}")
except (FileNotFoundError, ValueError) as err:
    print(f"Error: {err}")
"""

import os
import configparser


def get_api_settings(config_file_path):
    """
    Retrieves Azure API settings from a given configuration file.

    Args:
        config_file_path (str): Path to the configuration file.

    Raises:
        FileNotFoundError: Raised when the specified configuration file does
        not exist.
        ValueError: Raised when required API settings are missing.

    Returns:
        tuple[str, str]: The subscription key and Azure region.
    """
    config = configparser.ConfigParser()

    if not os.path.exists(config_file_path):
        raise FileNotFoundError(
            f"Config file not found at '{config_file_path}'"
        )

    config.read(config_file_path)

    if "API" not in config:
        raise ValueError("API settings not found in config file")

    api_section = config["API"]
    subscription_key = api_section.get("key")
    region = api_section.get("region")

    if not subscription_key:
        raise ValueError("API key not found in config file")

    if not region:
        raise ValueError("API region not found in config file")

    return subscription_key, region


def get_api_key(config_file_path):
    """
    Retrieves the API key from a given configuration file.

    This function reads the specified configuration file and extracts the API
    key. If the file does not exist or the API key is not found, appropriate
    exceptions are raised.

    Args:
        config_file_path (str): Path to the configuration file containing the
        API key.

    Raises:
        FileNotFoundError: Raised when the specified configuration file does
        not exist.
        ValueError: Raised when the API key is not found in the configuration
        file.

    Returns:
        str: Returns the API key as a string.
    """
    subscription_key, _ = get_api_settings(config_file_path)
    return subscription_key


if __name__ == "__main__":
    get_api_key(config_file_path=".env")
