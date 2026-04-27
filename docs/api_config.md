# Azure Configuration

The current desktop application supports two Azure Speech configuration paths:

1. In-app settings from `Tools > Settings`
2. A local `.env` file in INI format

## Recommended Path

Use the in-app settings sidebar for day-to-day use. `Tools > Settings` expands
the sidebar without closing the editor, and `Apply` persists the current values.
The GUI supports:

- Azure key
- Azure region
- connection testing
- voice, output directory, playback, logging, and SSML defaults

These values are persisted to:

```text
data/dynamic/app_settings.json
```

## `.env` Fallback

If the saved GUI settings do not contain Azure credentials, the application falls
back to a local `.env` file.

Expected format:

```ini
[API]
key = YOUR_AZURE_SPEECH_KEY
region = YOUR_AZURE_REGION
```

## Resolution Order

When the application needs Azure credentials, it resolves them in this order:

1. Saved GUI settings
2. `.env`

## Startup Behavior

The application no longer requires valid Azure credentials just to launch. If
credentials are missing:

- the GUI still opens
- generation/export actions remain gated by editor state
- synthesis attempts show setup guidance instead of crashing the app

## Notes

- Keep `.env` local and uncommitted.
- GUI settings are better for interactive use because they also support a
  connection test.
- Azure credentials are required for preview generation, exported files, and
  batch document audio export.
