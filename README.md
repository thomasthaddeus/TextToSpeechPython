# Text-to-Speech Python Program

## Description

This repository contains a PyQt-based desktop application for experimenting
with text-to-speech workflows and SSML helpers for Azure Speech.

The codebase currently includes:

- a main application window with text editing, SSML preview, and playback/export actions
- a settings dialog for voice, speech rate, synthesis volume, playback volume, and output directory
- a settings dialog for voice, speech rate, synthesis volume, playback volume, output directory, and logging
- a PowerPoint import dialog for bringing slide notes into the editor
- helpers for converting plain text into SSML
- Azure Speech client wrappers for synthesizing text and SSML
- PowerPoint scraping utilities for extracting slide text and notes
- text-cleaning helpers for preparing imported or pasted content for speech

## Installation

Poetry is now the recommended way to manage this project.

Install dependencies with:

```bash
poetry install
```

## Configuration

You can configure Azure Speech in either of two ways:

1. From `Tools > Settings` inside the application.
2. By creating a local `.env` file in INI format:

```ini
[API]
key = YOUR_AZURE_SPEECH_KEY
region = YOUR_AZURE_REGION
```

The `.env` file is intended for local development and should not be committed.
If Azure Speech is not configured yet, the GUI now starts in a degraded state
so you can open the settings dialog and complete setup there.

## Usage

Launch the desktop application from the project root:

```bash
poetry run python -m app.main
```

or use the Poetry script entrypoint:

```bash
poetry run tts-app
```

Once the app is running, the main workflow is:

1. Paste or import text into the editor.
2. Adjust Azure, voice, and output settings from `Tools > Settings`.
3. Preview the generated SSML.
4. Generate audio for playback or export it to an `.mp3` file.

If logging is enabled from `Tools > Settings`, application logs are written to:

```text
data/dynamic/logs/app.log
```

with timestamps formatted as `YYYYMMDDHHmmss`.

## Status

The project is still being cleaned up and stabilized. The code now uses
package-qualified imports, committed in-repo UI modules, and a Poetry-based
project manifest, but additional work is still planned around tests and runtime
polish.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
