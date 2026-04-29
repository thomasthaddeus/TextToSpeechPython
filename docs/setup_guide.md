# Install And Setup Guide

This guide covers the first-time setup path for running TextToSpeechPython on a
new machine. It focuses on local requirements, runtime folders, OCR setup, and
provider configuration.

You can open this same guide inside the application with `Help > Setup Guide`.

## Prerequisites

Install these before launching the app:

- Python 3.11 or newer, but still lower than Python 4
- Poetry
- Git, if you are working from a cloned repository
- Tesseract OCR, if you want scanned PDFs and image documents to produce text
- At least one text-to-speech provider configuration

Poetry installs the Python packages used by the app, including parser libraries
and the `pytesseract` bridge. It does not install the native Tesseract OCR
executable or create cloud-provider resources.

## Install Python Dependencies

From the project root, run:

```bash
poetry install
```

This installs the application dependencies and the development dependencies used
by the test suite.

If document import reports that parser packages are unavailable, rerun
`poetry install` from the project root with the same Python environment you use
to launch the app.

## Launch The App

Run either command from the project root:

```bash
poetry run python -m app.main
```

or:

```bash
poetry run tts-app
```

The app can open before a provider is configured, but generation and export
actions remain unavailable until the selected provider has valid settings.

## Build A Windows Executable

The repository includes a PyInstaller spec and a PowerShell build script for
creating a Windows executable folder build:

```powershell
.\scripts\build_windows_exe.ps1 -Clean
```

PyQt packaging can take several minutes while PyInstaller analyzes and collects
dependencies. The build script also writes a log to
`data/dynamic/tmp/pyinstaller_build.log`.

The built app is created at:

```text
dist/TextToSpeech/TextToSpeech.exe
```

The executable build includes the app assets and docs used by the GUI, including
the in-app setup guide. It does not bundle local credential files or cloud
secrets.

OCR support in the executable still requires the native Tesseract OCR executable
to be installed on the user's machine and available on `PATH`.

If the executable reports a missing Azure Speech DLL, rebuild with `-Clean` so
PyInstaller recollects the native SDK libraries.

## Runtime Data

The app writes user-specific runtime files under `data/dynamic/`.

Common runtime paths include:

- `data/dynamic/app_settings.json`
- `data/dynamic/audio_history.json`
- `data/dynamic/audio/`
- `data/dynamic/logs/`
- `data/dynamic/tmp/`

These files are machine-specific and should not be committed.

## OCR Setup

OCR support is needed for scanned PDFs, screenshots, photos of documents, and
image-only imports.

To enable OCR:

1. Install the Tesseract OCR executable for your operating system.
2. Make sure `tesseract` is available on `PATH`.
3. Verify the install from a terminal:

```bash
tesseract --version
```

If this command is not found, scanned-document imports will not be able to use
OCR even though the Python dependency is installed.

## Provider Setup

Open `Tools > Settings` in the app, choose the provider, fill in the provider
settings, and use the provider test button where available.

### Azure Speech

Azure Speech requires a Speech resource key and region.

You can configure Azure in the settings sidebar or with a local `.env` file:

```ini
[API]
key = YOUR_AZURE_SPEECH_KEY
region = YOUR_AZURE_REGION
```

For more detail, see [Azure configuration](api_config.md).

### Amazon Polly

Amazon Polly requires AWS credentials and a region in a dedicated Polly config
file:

```ini
[POLLY]
aws_access_key_id = YOUR_AWS_ACCESS_KEY_ID
aws_secret_access_key = YOUR_AWS_SECRET_ACCESS_KEY
aws_session_token = OPTIONAL_SESSION_TOKEN
region = us-east-1
```

For more detail, see [Amazon Polly configuration](polly_config.md).

### Gemini TTS

Gemini TTS requires a Google Cloud project and a service account JSON file with
access to the needed text-to-speech APIs.

Use a dedicated Gemini config file:

```ini
[GEMINI]
project_id = YOUR_GOOGLE_CLOUD_PROJECT_ID
service_account_json = C:\path\to\service-account.json
region = global
```

For more detail, see [Gemini TTS configuration](gemini_config.md).

### Offline Python TTS

Offline Python TTS uses `pyttsx3` and can run without cloud credentials. It may
still depend on the local speech engine installed on the operating system.

An optional local config file can be used for driver troubleshooting:

```ini
[LOCAL_TTS]
driver_name = auto
```

For more detail, see [Offline Python TTS configuration](local_tts_config.md).

## Verify The Setup

After installing dependencies and configuring a provider:

1. Launch the app.
2. Open `Tools > Settings`.
3. Select a provider and verify the provider settings.
4. Type a short sentence in the editor.
5. Use `Preview SSML` for SSML-capable providers.
6. Use `Generate & Play` or `Generate File`.

To run the automated tests:

```bash
poetry run pytest
```

## Troubleshooting

- If the app cannot import a supported document format, run `poetry install`.
- If scanned PDFs or images do not extract text, verify `tesseract --version`.
- If generation buttons stay disabled, add text to the editor and configure a
  valid provider.
- If Azure, Polly, or Gemini generation fails, retest the provider from
  `Tools > Settings` and confirm the provider-specific config file paths.
- If offline TTS fails, try a different local driver in the settings sidebar.
- If preview playback is unavailable, generate a file instead; some
  environments do not expose multimedia playback support to PyQt.
