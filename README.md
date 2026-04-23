# Text-to-Speech Python Program

## Description

This repository contains a PyQt-based desktop application for experimenting
with text-to-speech workflows and SSML helpers for Azure Speech.

The codebase currently includes:

- a main application window with a secondary dialog
- a small compute demo window used by the controller examples
- helpers for converting plain text into SSML
- Azure Speech client wrappers for synthesizing text and SSML
- PowerPoint scraping utilities for extracting slide text and notes

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

## Status

The project is still being cleaned up and stabilized. The code now uses
package-qualified imports, committed in-repo UI modules, and a Poetry-based
project manifest, but additional work is still planned around tests and runtime
polish.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
