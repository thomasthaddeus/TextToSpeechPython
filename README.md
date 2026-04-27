# TextToSpeechPython

## Overview

`TextToSpeechPython` is a PyQt6 desktop application for building Azure Speech
text-to-speech workflows around plain text, SSML previewing, and multi-format
document imports.

The current application supports:

- editing or pasting source text in the main window
- live SSML preview generation
- Azure Speech synthesis to preview or exported `.mp3` files
- a settings dialog for Azure credentials, voice, output directory, logging,
  playback volume, and advanced SSML controls
- document import for `.txt`, `.docx`, `.pdf`, `.html`, `.htm`, `.rtf`,
  `.epub`, `.xlsx`, `.xls`, `.csv`, and `.pptx`
- direct import of web URLs and pasted raw HTML through the same document
  extraction path
- selective import of extracted document sections into the main editor
- editor-text export to `.txt`, `.md`, or generated `.html`
- batch export of selected imported rows to one audio file per item
- actionable recent audio history in the main window

## Requirements

- Python 3.11+
- Poetry
- Azure Speech resource with a valid key and region

## Installation

From the project root:

```bash
poetry install
```

This install path includes the parser libraries needed for every format shown
in the document import dialog. If the active interpreter is missing one of those
packages, the app shows a startup/import warning and asks you to run
`poetry install`.

## Version Bumping

To have VS Code commits automatically bump the patch version in
`pyproject.toml`, install the local pre-commit hook:

```powershell
.\scripts\version\install_pre_commit_hook.ps1
```

After installation, commits that include staged changes under `app/`, `docs/`,
`scripts/`, `tests/`, or `README.md` will bump and stage `pyproject.toml`.
Commits that already include a staged `pyproject.toml` version change are left
alone.

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

1. Paste text into the editor, open a local document, open a URL, import raw
   HTML, or use `Import Document` for row-based selection.
2. Open `Tools > Settings` to configure Azure, voice, output directory, and SSML options.
3. Review the generated SSML preview.
4. Use `Generate & Play` for a temporary preview file or `Generate File` to export an `.mp3`.
5. Review, replay, copy, reopen, or restore previous work from the `Recent Audio` panel.

## Editor Text Export

`File > Export Editor Text` writes the current editor contents to `.txt`, `.md`,
or generated `.html`. This is an editor export, not a document round-trip save:
opened/imported `.docx`, `.pdf`, `.pptx`, spreadsheets, URLs, and other sources
are converted into editable narration text and are not saved back to their
original structured format.

## Advanced SSML Controls

The settings dialog includes an expandable advanced SSML section. The current
GUI exposes:

- emphasis
- pitch
- pitch range
- pause duration
- pause position

These controls are applied to both the SSML preview and generated audio.

## Document Import Workflow

`Import Document` opens a structured import dialog with:

- a row-based preview of extracted document sections
- heading-aware rows for DOCX, HTML, and EPUB content where available
- table and spreadsheet rows that keep sheet, column, and table context
- format-aware column labels and import modes, such as slide notes, page text,
  chapter text, OCR text, or spreadsheet row context
- multi-row selection
- content modes that adapt to the loaded format, such as page text, slide
  notes, chapter text, OCR text, or spreadsheet row context

From that dialog you can:

- import the selected rows into the main editor
- batch export the selected rows to one `.mp3` per item
- cancel active document-load or batch-export work without closing the app

The main window also supports quick source import from `File > Open Document`,
`File > Open URL`, and `File > Import Raw HTML`. URL and raw HTML imports are
parsed as structured HTML sections before being placed in the editor.

## Logging

If logging is enabled in `Tools > Settings`, the application writes logs to:

```text
data/dynamic/logs/app.log
```

Log timestamps use:

```text
YYYYMMDDHHmmss
```

## Recent Audio History

The `Recent Audio` panel keeps the latest generated files and supports workflow
actions:

- double-click a history item to replay it
- right-click to open the containing folder
- right-click to copy the generated audio path
- right-click to restore the source text and voice/settings snapshot used for
  that generation

New history entries include the editor text and relevant synthesis settings so
recent exports can be reused without manually reconstructing the previous setup.

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
- If a parser package for an advertised document format is missing, the app
  reports that clearly instead of failing with a raw import error.
- `Export Editor Text` only exports the current narration editor contents; it
  does not preserve or overwrite the original imported document format.
- Preview audio files are temporary and cleaned up automatically.

## Project Layout

- [app/main.py](app/main.py): application entrypoint
- [app/gui](app/gui): in-repo Qt UI modules and dialogs
- [app/controller](app/controller): GUI orchestration and workflow logic
- [app/model](app/model): settings, Azure wrappers, SSML helpers, and scrapers
- [docs](docs): supporting documentation
- [tests](tests): focused regression tests

## Verification

The repo currently includes focused regression tests for:

- SSML escaping and advanced SSML markup
- audio history persistence
- document import content-mode resolution
- normalized document scraping and dependency checks for supported import formats
- PyQt interaction flows for main-window menu actions, history affordances, and
  import-dialog selection/import behavior

Run them with:

```bash
poetry run pytest
```

## License

This project is licensed under the MIT License. See `LICENSE` for details.
