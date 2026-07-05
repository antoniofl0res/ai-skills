---
name: file2md
description: >
  Converts Office/PDF files (docx, pptx, xlsx, pdf) into matching .md files,
  cutting token usage when they're later read into an LLM context. Works on a
  whole folder or on specific named files within it — if the user names one or
  more files, convert only those; if no files are named, convert every
  supported file in the folder. Use this skill whenever the user asks to
  "convert this folder to markdown", "convert these files to markdown", "turn
  X into markdown", "optimise/reduce tokens for this folder", "make this
  folder LLM-friendly", "flatten these docs to markdown", or references
  Word/PowerPoint/Excel/PDF files that need to be prepped for a smaller
  context footprint. One markdown file is produced per input file, written
  alongside the original with the same base name and a .md extension. Not for
  a single already-open file conversion request that the docx/pptx/xlsx/pdf
  skills already cover directly — this skill is for batch/selective
  file-to-markdown conversion.
---

# file2md skill

Converts documents into a clean, compact `.md` file — one output per input —
so they can be fed into an LLM context at a fraction of the token cost of the
original binary formats. Accepts either a folder (convert everything
supported) or a specific list of files (convert only those).

## Why this exists

Markdown strips binary/XML overhead (styles, embedded media wrappers, OOXML
boilerplate) down to structural text — headings, lists, tables, plain
paragraphs. For most Office/PDF documents this is a 5–20x token reduction
versus reading the raw file, with no loss of the information an LLM actually
uses.

## Supported input types

`.docx`, `.pptx`, `.xlsx`, `.pdf`

Anything else in the folder is left untouched and reported as skipped.

## Step 1 — Confirm scope

Two modes, decided by whether the user named specific files:

- **File-selection mode** — the user names one or more files (by name or
  path). Convert only those files. If a named file isn't in the target
  folder or has an unsupported extension, report it as skipped rather than
  silently ignoring it.
- **Folder mode** (default when no files are named) — convert every
  supported file in the folder. Confirm the target folder path, and whether
  conversion should recurse into subfolders (default: top-level only, unless
  the user says "recursively" or "including subfolders"). If the folder is
  large (50+ candidate files), state the count before proceeding — this is a
  batch operation, not free.

## Step 2 — Check for `markitdown`

Prefer Microsoft's `markitdown` library — it already handles docx/pptx/xlsx/pdf
with sensible table and heading reconstruction in one dependency.

```bash
python -c "import markitdown" 2>&1 || pip install markitdown
```

If `markitdown` is unavailable and cannot be installed (no network, blocked
pip), fall back to Step 3b (per-type manual extraction) instead of failing
outright.

## Step 3a — Convert with markitdown (preferred path)

```python
from pathlib import Path
from markitdown import MarkItDown

SUPPORTED = {".docx", ".pptx", ".xlsx", ".pdf"}

def _convert_one(md: MarkItDown, path: Path, converted: list, skipped: list) -> None:
    if path.suffix.lower() not in SUPPORTED:
        skipped.append(f"{path.name} (unsupported type)")
        return
    out_path = path.with_suffix(".md")
    try:
        result = md.convert(str(path))
        out_path.write_text(result.text_content, encoding="utf-8")
        converted.append(out_path.name)
    except Exception as e:
        skipped.append(f"{path.name} (error: {e})")

def convert_files(folder: str, filenames: list[str]) -> None:
    """File-selection mode: convert only the named files."""
    md = MarkItDown()
    root = Path(folder)
    converted, skipped = [], []

    for name in filenames:
        path = root / name
        if not path.is_file():
            skipped.append(f"{name} (not found in {folder})")
            continue
        _convert_one(md, path, converted, skipped)

    _report(converted, skipped)

def convert_folder(folder: str, recursive: bool = False) -> None:
    """Folder mode: convert every supported file."""
    md = MarkItDown()
    root = Path(folder)
    pattern = "**/*" if recursive else "*"
    converted, skipped = [], []

    for path in sorted(root.glob(pattern)):
        if not path.is_file():
            continue
        _convert_one(md, path, converted, skipped)

    _report(converted, skipped)

def _report(converted: list, skipped: list) -> None:
    print(f"Converted: {len(converted)}")
    for name in converted:
        print(f"  - {name}")
    if skipped:
        print(f"Skipped: {len(skipped)}")
        for name in skipped:
            print(f"  - {name}")
```

## Step 3b — Manual per-type fallback (only if markitdown is unavailable)

Use the extraction approach each dedicated skill already documents, but write
markdown instead of prose output:

- **docx** — see the `docx` skill's read approach (python-docx: paragraphs,
  headings by style, tables as pipe-delimited rows).
- **pptx** — see the `pptx` skill's read approach (python-pptx: one `##`
  heading per slide, bullet text as `-` lists, speaker notes as a blockquote).
- **xlsx** — see the `xlsx` skill's read approach (openpyxl/pandas: one `##`
  heading per sheet, `DataFrame.to_markdown()` for the table body).
- **pdf** — see the `pdf` skill's read approach (pdfplumber: `page.extract_text()`
  per page, `page.extract_tables()` rendered as pipe-delimited rows; if a page
  extracts empty text, note it as a scanned/image page rather than guessing
  its content).

Keep the same output contract as Step 3a: one `.md` file per input, same base
name, written next to the source file, plus a converted/skipped summary.

## Step 4 — Verify

Before reporting success:
- Confirm each expected `.md` file actually exists on disk (`Path.exists()`),
  don't infer success from the script's own return code.
- Spot-check one or two output files by reading the first ~20 lines to
  confirm structure came through (headings, tables) rather than a wall of
  garbled text.
- Report the token-reduction angle concretely if easy to compute: original
  file size vs. markdown file size, e.g. "sourcedoc.pdf: 340 KB -> sourcedoc.md:
  18 KB".

## Notes

- This skill never deletes or modifies the original files — it only adds new
  `.md` files alongside them. Report this clearly since it doubles folder
  content; ask first if the user wants originals moved/archived after
  conversion (that would be a separate, reversible-but-destructive-adjacent
  step and should go through a preflight-style confirmation).
- If a `.md` file with the same name already exists, ask before overwriting
  rather than silently clobbering it.
- Scanned/image-only PDFs will extract empty or near-empty text; flag these
  explicitly rather than emitting a near-blank markdown file silently — OCR
  is out of scope for this skill (use the `pdf` skill's OCR workflow first if
  needed).
