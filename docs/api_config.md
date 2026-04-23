# API Config

The current application reads Azure Speech settings from a local configuration
file using `configparser`. The project uses `.env` as the default filename, but
the contents are INI-style rather than shell-style environment variable lines.

## Expected Format

Create a local `.env` file with the following structure:

```ini
[API]
key = YOUR_AZURE_SPEECH_KEY
region = YOUR_AZURE_REGION
```

Both values are required.

## What the Code Reads

The configuration helpers support:

- `get_api_key(config_file_path)` for callers that only need the key
- `get_api_settings(config_file_path)` for callers that need both the key and
  region

## Notes

- The `.env` file should remain local and uncommitted.
- If you prefer a different filename, pass its path into the configuration
  helper.
- A future packaging pass may switch the project to a different configuration
  strategy, but this is the format the current code expects.
