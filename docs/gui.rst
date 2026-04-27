GUI Overview
============

The current application is a PyQt6 desktop GUI centered around a single main
window plus supporting dialogs.

Main Window
-----------

The main window includes:

- a source text editor
- a read-only SSML preview panel
- action buttons for preview, cleaning, generation, export-related flow, and
  document import
- a playback volume control
- an inline guidance label for disabled or unavailable states
- a recent audio history panel
- a menu bar with file, tools, and help actions
- quick source import actions for local documents, URLs, and pasted raw HTML

Settings Dialog
---------------

The settings dialog currently supports:

- Azure key
- Azure region
- Azure connection testing
- voice selection
- speaking rate
- synthesis volume
- playback volume
- output directory
- auto-clean toggle
- logging toggle

It also includes an advanced SSML section with:

- emphasis
- pitch
- pitch range
- pause duration
- pause position

Document Import Dialog
----------------------

The document import dialog uses a structured table instead of a free-form text
preview.

It provides:

- item/title column
- primary text column
- secondary text column
- heading-aware rows for structured documents
- table, spreadsheet, and slide metadata that preserves source context
- format-aware labels and content-mode options for pages, slides, chapters,
  OCR text, and spreadsheet rows
- multi-row selection
- content-mode selection
- import of selected rows into the main editor
- batch export of selected rows to one audio file per item
- cancel controls for active document-load and batch-export work

Currently supported file types include:

- ``.txt``
- ``.docx``
- ``.pdf``
- ``.html`` / ``.htm``
- ``.rtf``
- ``.epub``
- ``.xlsx`` / ``.xls`` / ``.csv``
- ``.pptx``

The main window additionally supports ``File > Open URL`` and
``File > Import Raw HTML``. Both flows parse the source through the same
structured HTML scraper used for local ``.html`` and ``.htm`` files before
placing the resolved text in the editor.

The app checks parser dependency availability at startup and before loading a
document. If the active environment is missing a package required by an
advertised format, the UI reports that clearly and points back to
``poetry install``.

Validation And Action States
----------------------------

The current GUI proactively guides users by disabling invalid actions.

Examples:

- preview and generation actions are disabled when the editor is empty
- stop is disabled when no preview audio is active
- playback volume controls are disabled when multimedia playback support is not
  available
- the preview button text changes when only file generation is possible
- long-running document-load and batch-export work exposes cancel controls while
  the worker is active

Recent Audio History
--------------------

The main window tracks recent generated audio items and displays:

- timestamp
- source type
- voice
- filename
- output path

History items are actionable:

- double-click a generated audio item to replay it
- right-click to open the containing folder
- right-click to copy the audio path
- right-click to restore the source text and generation settings snapshot

History is persisted to ``data/dynamic/audio_history.json``.
