# TextToSpeechPython

## Overview

`TextToSpeechPython` is a PyQt6 desktop application for building Azure Speech
text-to-speech workflows around plain text, SSML previewing, and PowerPoint
imports.

The current application supports:

- editing or pasting source text in the main window
- live SSML preview generation
- Azure Speech synthesis to preview or exported `.mp3` files
- a settings dialog for Azure credentials, voice, output directory, logging,
  playback volume, and advanced SSML controls
- PowerPoint (`.pptx`) import with structured slide/notes preview
- selective PPTX import into the main editor
- batch export of selected PPTX rows to one audio file per slide item
- recent audio history in the main window

## Requirements

- Python 3.11+
- Poetry
- Azure Speech resource with a valid key and region

## Installation

From the project root:

```bash
poetry install
```

## Running The App

You can launch the application in either of these ways:

```bash
poetry run python -m app.main
```

or:

```bash
poetry run tts-app
```

## Azure Configuration

The app can start without Azure configured, but generation and export will stay
unavailable until credentials are provided.

You can configure Azure Speech in either of these ways:

1. In the GUI via `Tools > Settings`
2. With a local `.env` file in INI format

Example `.env`:

```ini
[API]
key = YOUR_AZURE_SPEECH_KEY
region = YOUR_AZURE_REGION
```

GUI settings take precedence over `.env` when both are present.

## Main Workflow

1. Paste text into the editor, or import slides from `Import PPTX`.
2. Open `Tools > Settings` to configure Azure, voice, output directory, and SSML options.
3. Review the generated SSML preview.
4. Use `Generate & Play` for a temporary preview file or `Generate File` to export an `.mp3`.
5. Review recent generated files in the `Recent Audio` panel.

## Advanced SSML Controls

The settings dialog includes an expandable advanced SSML section. The current
GUI exposes:

- emphasis
- pitch
- pitch range
- pause duration
- pause position

These controls are applied to both the SSML preview and generated audio.

## PowerPoint Workflow

`Import PPTX` opens a structured import dialog with:

- a row-based preview of slide number, slide text, and notes
- multi-row selection
- content modes:
  - `Prefer Notes`
  - `Notes Only`
  - `Slide Text Only`
  - `Combine Slide Text and Notes`

From that dialog you can:

- import the selected rows into the main editor
- batch export the selected rows to one `.mp3` per item

## Logging

If logging is enabled in `Tools > Settings`, the application writes logs to:

```text
data/dynamic/logs/app.log
```

Log timestamps use:

```text
YYYYMMDDHHmmss
```

## Runtime Data

The app writes runtime artifacts under `data/dynamic/`, including:

- `app_settings.json` for persisted UI settings
- `audio_history.json` for recent generated audio history
- `audio/` for default exported audio output
- `logs/` for application logs
- `tmp/` for temporary test and scratch artifacts that should not be synced

## Current Behavior Notes

- The app disables generation-related actions until the editor contains text.
- If multimedia playback support is unavailable in the environment, preview
  generation still works, but playback controls are disabled and the UI relabels
  the preview action accordingly.
- Preview audio files are temporary and cleaned up automatically.

## Project Layout

- [app/main.py](D:/Projects/TextToSpeechPython/app/main.py): application entrypoint
- [app/gui](D:/Projects/TextToSpeechPython/app/gui): in-repo Qt UI modules and dialogs
- [app/controller](D:/Projects/TextToSpeechPython/app/controller): GUI orchestration and workflow logic
- [app/model](D:/Projects/TextToSpeechPython/app/model): settings, Azure wrappers, SSML helpers, and scrapers
- [docs](D:/Projects/TextToSpeechPython/docs): supporting documentation
- [tests](D:/Projects/TextToSpeechPython/tests): focused regression tests

## Verification

The repo currently includes focused regression tests for:

- SSML escaping and advanced SSML markup
- audio history persistence
- PPTX import content-mode resolution

Run them with:

```bash
python -m unittest tests.test_main_controller_ssml tests.test_main_controller_history tests.test_second_controller_import
```

## License

This project is licensed under the MIT License. See `LICENSE` for details.
