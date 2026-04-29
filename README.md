# TextToSpeechPython

## Overview

`TextToSpeechPython` is a PyQt6 desktop application for building provider-backed
text-to-speech workflows around plain text, SSML previewing, and multi-format
document imports.

The current application supports:

- editing or pasting source text in the main window
- live SSML preview generation
- Azure Speech, Gemini TTS, Amazon Polly, and offline Python TTS synthesis to preview or exported `.mp3` files
- a collapsible settings sidebar for provider selection, Azure credentials,
  Gemini config, local TTS config, Amazon Polly config, voice, output directory, logging,
  playback volume, and advanced SSML controls
- section-level narration controls for applying speaker, voice, rate, volume,
  and pause changes to selected editor text
- document import for `.txt`, `.docx`, `.pdf`, `.html`, `.htm`, `.rtf`,
  `.epub`, `.xlsx`, `.xls`, `.csv`, `.pptx`, and common image formats
- OCR extraction for scanned PDFs and image documents when Tesseract OCR is
  installed locally
- direct import of web URLs and pasted raw HTML through the same document
  extraction path
- selective import of extracted document sections into the main editor
- editor-text export to `.txt`, `.md`, or generated `.html`
- batch export of selected imported rows to one audio file per item
- actionable recent audio history in the main window

## Requirements

- Python 3.11+
- Poetry
- Azure Speech resource with a valid key and region, a Google Cloud Gemini TTS
  config file, Amazon Polly AWS credentials in a dedicated Polly config file,
  or the bundled offline Python TTS dependency
- Tesseract OCR for scanned PDFs and image imports

## Installation

From the project root:

```bash
poetry install
```

This install path includes the parser libraries needed for every format shown
in the document import dialog. If the active interpreter is missing one of those
packages, the app shows a startup/import warning and asks you to run
`poetry install`.

OCR support also requires the Tesseract OCR executable to be installed on the
user's machine and available on `PATH`. Poetry installs the Python bridge
package (`pytesseract`), but it cannot install the operating-system OCR engine
itself.

For a complete first-time setup path covering Poetry, Tesseract OCR, runtime
folders, local requirements, and provider-specific configuration, see
[docs/setup_guide.md](docs/setup_guide.md). The same guide is also available
inside the application through `Help > Setup Guide`.

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

## Building A Windows Executable

The repository includes a PyInstaller workflow for creating a Windows folder
build:

```powershell
.\scripts\build_windows_exe.ps1 -Clean
```

PyQt builds can take several minutes. Build output is also written to
`data/dynamic/tmp/pyinstaller_build.log` so packaging failures can be reviewed
after the command finishes.

The executable is written to:

```text
dist/TextToSpeech/TextToSpeech.exe
```

The build bundles the application code, `app/assets/`, and `docs/` so the app
stylesheet, icons, and in-app setup guide are available from the executable.

Before sharing a build, verify it on a clean Windows machine. Provider
credentials are intentionally not bundled, and OCR still requires the native
Tesseract executable to be installed on the target machine and available on
`PATH`.

If the executable reports a missing Azure Speech DLL, rebuild with `-Clean` so
PyInstaller recollects the native SDK libraries:

```powershell
.\scripts\build_windows_exe.ps1 -Clean
```

## Provider Configuration

The app can start without a configured TTS provider, but generation and export
stay unavailable until provider credentials are available.

You can configure Azure Speech in either of these ways:

1. In the GUI via `Tools > Settings`, then the settings sidebar `Apply` button
2. With a local `.env` file in INI format

Example `.env`:

```ini
[API]
key = YOUR_AZURE_SPEECH_KEY
region = YOUR_AZURE_REGION
```

GUI settings take precedence over `.env` when both are present.

Amazon Polly uses its own dedicated config file instead of Azure's `.env`
fallback. Example `.polly.env`:

```ini
[POLLY]
aws_access_key_id = YOUR_AWS_ACCESS_KEY_ID
aws_secret_access_key = YOUR_AWS_SECRET_ACCESS_KEY
aws_session_token = OPTIONAL_SESSION_TOKEN
region = us-east-1
```

Set `TTS Provider` to `Amazon Polly` in the settings sidebar, point the app at
that config file, and choose the desired Polly engine.

Gemini TTS also uses its own dedicated config file. Example `.gemini.env`:

```ini
[GEMINI]
project_id = YOUR_GOOGLE_CLOUD_PROJECT_ID
service_account_json = C:\path\to\service-account.json
region = global
```

Set `TTS Provider` to `Gemini TTS`, point the app at that config file, choose a
Gemini TTS model, and optionally provide a natural-language style prompt for
delivery control.

Offline Python TTS can run without cloud credentials. It also supports an
optional dedicated local config file for driver troubleshooting. Example
`.local_tts.env`:

```ini
[LOCAL_TTS]
driver_name = auto
```

Set `TTS Provider` to `Offline Python TTS`, optionally point the app at that
config file, and choose a local driver when platform-specific troubleshooting is
needed.

## Main Workflow

1. Paste text into the editor, open a local document, open a URL, import raw
   HTML, or use `Import Document` for row-based selection.
2. Open `Tools > Settings` to expand the settings sidebar and configure the TTS provider, provider credentials/config path, voice, output directory, and SSML options.
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

The settings sidebar includes an expandable advanced SSML section and can stay
open while you edit narration text. The current
GUI exposes:

- emphasis
- pitch
- pitch range
- pause duration
- pause position

These controls are applied to both the SSML preview and generated audio.

## Section Narration Controls

The main window includes a `Narration Section` control strip for more expressive
audio. Select text in the editor, choose a speaker label, voice, rate, volume,
and pause, then use `Apply To Selection`.

The app wraps the selected text in lightweight narration markup:

```text
[[narration speaker="Avery" voice="en-US-JennyNeural" rate="slow" volume="soft" pause="500ms"]]
Selected narration text.
[[/narration]]
```

SSML-capable providers use that markup to generate per-section voice, cadence,
volume, and pause changes. Plain-text providers strip the markup and keep useful
speaker labels in the generated prompt text.

## Document Import Workflow

`Import Document` opens a structured import dialog with:

- an editable row-based review table of extracted document sections
- heading-aware rows for DOCX, HTML, and EPUB content where available
- table and spreadsheet rows that keep sheet, column, and table context
- format-aware column labels and import modes, such as slide notes, page text,
  chapter text, OCR text, image text, or spreadsheet row context
- multi-row selection
- content modes that adapt to the loaded format, such as page text, slide
  notes, chapter text, OCR text, image text, or spreadsheet row context
- review actions for cleaning, splitting, merging, duplicating, deleting, and
  restoring imported rows before generation

Supported local source types include `.txt`, `.docx`, `.pdf`, `.html`, `.htm`,
`.rtf`, `.epub`, `.xlsx`, `.xls`, `.csv`, `.pptx`, `.png`, `.jpg`, `.jpeg`,
`.tif`, `.tiff`, `.bmp`, and `.webp`.

From that dialog you can:

- edit extracted titles, narration text, and context before using them
- import the selected reviewed rows into the main editor
- batch export the selected reviewed rows to one `.mp3` per item
- cancel active document-load or batch-export work without closing the app

The main window also supports quick source import from `File > Open Document`,
`File > Open URL`, and `File > Import Raw HTML`. URL and raw HTML imports are
parsed as structured HTML sections before being placed in the editor.

## Logging

If logging is enabled from the settings sidebar, the application writes logs to:

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

- collapse or expand the panel with the `-` / `+` control
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
- [app/model](app/model): settings, provider wrappers, SSML helpers, and scrapers
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
