# Text-to-Speech Python Program

## Description

This repository contains a PyQt-based desktop application for experimenting
with text-to-speech workflows and SSML helpers for Azure Speech.

The codebase currently includes:

- a main application window with text editing, SSML preview, and playback/export actions
- a settings dialog for voice, speech rate, synthesis volume, playback volume, and output directory
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

Create a local `.env` file in INI format with your Azure credentials:

```ini
[API]
key = YOUR_AZURE_SPEECH_KEY
region = YOUR_AZURE_REGION
```

The `.env` file is intended for local development and should not be committed.

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
2. Adjust voice and output settings from `Tools > Settings`.
3. Preview the generated SSML.
4. Generate audio for playback or export it to an `.mp3` file.

## Status

The project is still being cleaned up and stabilized. The code now uses
package-qualified imports, committed in-repo UI modules, and a Poetry-based
project manifest, but additional work is still planned around tests and runtime
polish.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
