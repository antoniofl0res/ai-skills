---
name: folder-about
description: >
  Creates a comprehensive About.txt file that documents a folder — its contents,
  purpose, and quantitative statistics. Use this skill whenever the user asks to
  "create an About file", "describe this folder", "document what's in this folder",
  "summarize the folder", or anything that implies generating a human-readable
  description of a directory. Also trigger when the user says things like "write
  an overview of my project folder", "make a README for this folder", or "document
  this directory". The output is always a plain-text .txt file saved into the
  target folder itself.
---

# Folder About Skill

This skill produces a well-structured `About.txt` file that serves as a
self-contained reference document for any folder. The file should be useful
to someone encountering the folder for the first time — telling them what's
here, why it exists, how much of it there is, and how it's organized.

---

## Step 1 — Identify the target folder

The target folder is wherever the user's files live. Check whether a folder
has already been mounted or referenced in the conversation. If not, ask the
user to confirm the path before proceeding.

---

## Step 2 — Gather quantitative stats

Run these shell commands (or equivalent) before writing anything. Concrete
numbers make the document trustworthy and useful.

```bash
# Total size of the entire folder tree
du -sh <folder>

# Size broken down per immediate subfolder
du -sh <folder>/*/

# Total file count
find <folder> -type f | wc -l

# Total subfolder count (excluding root)
find <folder> -mindepth 1 -type d | wc -l

# File count grouped by extension
find <folder> -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn

# Top 5 largest individual files
find <folder> -type f -exec du -sh {} \; | sort -rh | head -5

# Per-subfolder: file count
for d in <folder>/*/; do echo -n "$d: "; find "$d" -type f | wc -l; done

# Per-subfolder: immediate subfolder count
for d in <folder>/*/; do echo -n "$d: "; find "$d" -mindepth 1 -type d | wc -l; done
```

Capture all of this before writing a single line of the output file — the
numbers should flow naturally into the document rather than being retrofitted.

---

## Step 3 — Explore the contents

Browse through the folder tree to understand:
- What kind of files are present (documents, data, code, media, etc.)
- How the subfolders are organized — by topic, by date, by role, by workflow step?
- Any naming patterns that reveal context (e.g., project names, cohort years,
  participant IDs, version numbers)
- Whether any files appear duplicated across subfolders

Read a few key filenames and folder names carefully — they often reveal purpose
and domain even without opening the files.

---

## Step 4 — Infer purpose and context

Based on what you've found, form a clear mental model of:
1. **What** this folder is: its domain, project, or subject matter
2. **Why** it exists: is it an archive, an active working area, a training package,
   a deliverable library, a research repository?
3. **Who** might use it: practitioners, managers, researchers, trainees?
4. **When**: does the folder span a single event/cycle, or is it ongoing?

Don't ask the user to fill in these gaps if you can infer them confidently from
the file and folder names. Only ask if you genuinely can't tell.

---

## Step 5 — Write the About.txt

Save the file as `About.txt` directly in the root of the target folder (not in
a subfolder). Use plain ASCII — no Markdown, no special characters beyond what
a basic text editor renders cleanly.

### Required sections (in this order):

**1. Header block**
```
================================================================================
ABOUT THIS FOLDER
================================================================================
Folder Name   : <name>
Last Updated  : <Month YYYY>
Maintained by : <name and email if known, otherwise omit>
```

**2. Folder Summary (Quantitative)**
Put the numbers up front — readers often want the quick facts first.
- Total size
- Total file count and subfolder count
- File counts broken down by type (use a clean indented list)
- A table showing size, file count, and subfolder count per immediate subfolder
  (ASCII table with box-drawing characters works well here)
- Root-level files with their individual sizes
- Top 5 largest individual files

**3. Description**
2–4 sentences describing what the folder contains, in plain language. Name the
domain, the type of content, and the scope. Avoid generic phrases like "this
folder contains various files" — be specific.

**4. Purpose**
A numbered list of 3–6 concrete purposes the folder serves. Think in terms of
what someone would actually *do* with this folder: plan a training, look up a
reference document, track participant data, replicate the workflow elsewhere, etc.

**5. Folder Structure**
An ASCII tree of the full folder hierarchy. Annotate each node with a brief
description of what it contains. Keep annotations concise (one line per node).

Example format:
```
FolderName/
│
├── SubfolderA/         ← Brief description of what's here
│   ├── SubfolderA1/    ← What's in this sub-subfolder
│   └── file.xlsx       ← What this file is for
│
└── SubfolderB/         ← Brief description
```

**6. Domain-specific sections (if warranted)**
If the folder is rich enough to justify it, add one or two sections specific to
its content — for example:
- "Key Topics Covered" (for training or educational material)
- "Participating Sites / Organizations" (for multi-site projects)
- "Data Files" (for research or analytics folders)
- "Software / Scripts" (for code repositories)

Use your judgment — don't force a section if it adds no value.

**7. Remarks**
3–5 bullet points covering practical observations a future user would want to
know. Good candidates:
- Duplicate files that appear in multiple locations (and why)
- Naming convention patterns
- Files that are templates vs. completed instances
- Suggestions for where new content from a future cycle should go
- Any external links or dependencies (URLs, connected systems)

**Closing line:**
```
================================================================================
```

---

## Formatting principles

- Use `--------------------------------------------------------------------------------` (80 dashes) as section dividers.
- Use `================================================================================` (80 equals) as the top and bottom border.
- Keep the line width at or under 80 characters for comfortable reading in any text editor.
- Indent consistently with 2 spaces.
- Use bullet points with `•` for unordered lists.
- Use numbered lists (`1. 2. 3.`) for ordered items like purpose statements.
- For the per-subfolder table, align columns with spaces so it reads cleanly without a monospace font assumption.
- Avoid Markdown syntax (`**bold**`, `# headers`, etc.) — this is a plain text file.

---

## Quality check before saving

Before writing the file, ask yourself:
- Would someone unfamiliar with this folder understand its purpose from the Description alone?
- Are all the numbers consistent (e.g., does the per-subfolder table add up to the total)?
- Does the folder tree match what you actually found on disk?
- Are the Remarks genuinely useful, or just filler?

If any answer is "no", revise before saving.
