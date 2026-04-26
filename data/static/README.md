# Static Test Fixtures

This directory is intended for manual and automated fixture documents used to verify import, extraction, OCR, and audio-generation behavior across all supported source types.

## Important Rule

Every fixture document in `data/static/` should contain text that is unique to that document.

Why this matters:

- each imported document should produce audio that is unique to that source
- extraction regressions are easier to spot when text clearly identifies the originating file
- cross-format comparisons are more reliable when we can tell exactly which fixture produced which output

Avoid reusing the same body text across multiple fixture files. Even if two fixtures test the same format family, their actual extracted text should differ.

## Suggested Fixture Layout

```text
data/static/
  plain/
  word/
  pdf/
  html/
  rtf/
  epub/
  spreadsheet/
  pptx/
  images/
```

## Recommended Fixtures

### Plain Text

- `plain/basic.txt`
  - Purpose: baseline multi-paragraph text import
  - Include: 2-4 paragraphs with simple prose
  - Expected: split into multiple text blocks

- `plain/unicode.txt`
  - Purpose: punctuation and Unicode handling
  - Include: quotes, apostrophes, symbols, accented words
  - Expected: text imports cleanly and remains distinguishable in generated audio

### Word

- `word/basic.docx`
  - Purpose: heading + paragraph extraction
  - Include: one heading and several body paragraphs
  - Expected: paragraphs import as separate rows

- `word/tables.docx`
  - Purpose: confirm current limitations around richer DOCX structure
  - Include: paragraphs plus one table
  - Expected: paragraph text imports; table handling should be documented if incomplete

### PDF

- `pdf/text_layer.pdf`
  - Purpose: searchable PDF import
  - Include: real text layer with unique copy
  - Expected: page text extracts without OCR

- `pdf/scanned_like.pdf`
  - Purpose: OCR fallback for image-only PDFs
  - Include: scanned or rasterized text with no embedded text layer
  - Expected: OCR path produces readable text

### HTML

- `html/basic.html`
  - Purpose: headings, paragraphs, and lists
  - Include: `<title>`, headings, paragraphs, and list items
  - Expected: structured text rows extracted from major elements

- `html/no_title.html`
  - Purpose: title fallback behavior
  - Include: body text without a `<title>` tag
  - Expected: filename-based section naming

### RTF

- `rtf/basic.rtf`
  - Purpose: rich-text conversion
  - Include: formatted text with bold/italic content
  - Expected: plain-text extraction preserves readable wording

### EPUB

- `epub/basic.epub`
  - Purpose: chapter-level extraction
  - Include: at least 2 chapters with distinct headings and body text
  - Expected: each chapter imports as a separate row

### Spreadsheet

- `spreadsheet/basic.csv`
  - Purpose: simple row/column flattening
  - Include: a few rows with column labels and varied values
  - Expected: one import row per CSV row

- `spreadsheet/basic.xlsx`
  - Purpose: single-sheet Excel extraction
  - Include: one worksheet with several rows
  - Expected: one import row per worksheet row

- `spreadsheet/multi_sheet.xlsx`
  - Purpose: multi-sheet coverage
  - Include: 2 or more worksheets with distinct row content
  - Expected: rows preserve worksheet-aware titles

### PowerPoint

- `pptx/basic_notes.pptx`
  - Purpose: slide text + notes import
  - Include: visible slide text and meaningful speaker notes
  - Expected: primary and secondary text both populate

- `pptx/notes_only.pptx`
  - Purpose: note-heavy presentation import
  - Include: sparse visible slide text and detailed notes
  - Expected: secondary-text-preferred workflows remain useful

### Images / OCR

- `images/printed_text.png`
  - Purpose: clean OCR baseline
  - Include: high-contrast printed text
  - Expected: OCR extracts text accurately

- `images/printed_text.jpg`
  - Purpose: lossy-image OCR baseline
  - Include: text similar in complexity to the PNG test, but unique wording
  - Expected: OCR still produces readable text

- `images/rotated_text.png`
  - Purpose: OCR robustness
  - Include: rotated text
  - Expected: OCR quality is measurable even if imperfect

- `images/low_contrast_scan.png`
  - Purpose: difficult OCR case
  - Include: low-contrast or lightly degraded text
  - Expected: fallback behavior remains stable even if extraction quality drops

- `images/photo_document.jpg`
  - Purpose: photographed document OCR
  - Include: perspective distortion or phone-photo characteristics
  - Expected: OCR path exercises real-world scan-like input

## Suggested Naming Convention

Use descriptive names that indicate both format and scenario, for example:

- `basic.txt`
- `unicode.txt`
- `text_layer.pdf`
- `scanned_like.pdf`
- `multi_sheet.xlsx`
- `notes_only.pptx`
- `photo_document.jpg`

## Suggested Content Convention

Inside each file, include a short unique identifier in the actual text, such as:

- `Fixture ID: PDF-TEXT-LAYER-01`
- `Fixture ID: DOCX-TABLES-01`
- `Fixture ID: OCR-PHOTO-01`

This helps confirm:

- the correct file was imported
- the correct file produced the generated audio
- OCR or parser output came from the expected source

## Minimum Coverage Goal

At minimum, `data/static/` should contain one working fixture for each currently importable type:

- `.txt`
- `.docx`
- `.pdf`
- `.html`
- `.rtf`
- `.epub`
- `.csv`
- `.xlsx`
- `.pptx`
- one OCR image format such as `.png` or `.jpg`
