---
name: mylearning
description: >-
  Capture a concept just learned or explored as a bite-sized, interactive, single-file HTML
  reference page in C:\dev\MyLearning, then register it on the library index. Use this whenever
  Antonio says "/mylearning", "add this to MyLearning", "make a learning page", "capture this
  concept", "turn this into a reference", or right after finishing an exploratory or learning
  session (a debugging deep-dive, a new tool, a paper, a mechanism understood) that is worth
  preserving for quick future reference. Trigger even when he does not name the folder explicitly:
  if the session produced a reusable mental model and he signals he wants to keep it, this is the
  skill. Do not use it for formal deliverables (reports, briefs, slides): those go through the
  docx/pptx/pdf skills and antonio-style.
---

# MyLearning page builder

MyLearning is Antonio's growing interactive textbook at `C:\dev\MyLearning`. Each page is one
self-contained HTML file teaching one concept, openable directly in a browser with no server or
build step. The library is the asset; any single page is just the current frontier. Your job is to
turn something he just learned into one more page, fast, and shelve it.

The guiding bet: a page is worth making when the concept has a **reusable shape** he will want to
re-grok in seconds later. If it is a one-off fact, it does not belong here; if it is a mental model
he will reach for again, it does.

## Folder layout

```
C:\dev\MyLearning\
├─ index.html            the shelf: lists every page as a card
└─ pages\
   ├─ _template.html     the scaffold you copy (pre-stubbed, two reusable widgets)
   └─ <concept>.html     one file per concept
```

## Workflow

### 1. Decide it is worth a page
Confirm the concept has a reusable shape (a mechanism, a tradeoff, a procedure, a failure mode).
If it is borderline, say so and ask. A thin page dilutes the library.

### 2. Harvest REAL material from the session
This is the most important rule: **build from real artifacts, never invented numbers.** The pages
earn their credibility (and Antonio's whole style is credibility-first) by showing what actually
happened: the real loss curve, the real benchmark, the real error, the real command output. Before
writing, gather from the conversation:
- the one surprising number or contrast that makes the idea land (the hook)
- any real measurements, outputs, or examples you can wire into an interactive widget
- the single rule worth remembering, and any real failure/caveat that was actually hit

If a number is not available, do not fabricate one. Use a qualitative illustration instead, or omit
the widget. A page with one honest interactive element beats one with three invented ones.

### 3. Copy the template
Copy `pages\_template.html` to `pages\<concept>.html` (kebab-case, e.g. `bayes-updating.html`).
The template already carries the full styled CSS and two reusable widgets. You fill blanks and
keep or delete whole blocks; you do not restyle.

### 4. Fill the five sections
The fixed pedagogical arc, in order. Keep it bite-sized: target ~5 minutes to read, one screen of
scrolling. Resist adding a sixth section.

1. **Hook** (`pill`, `h1`, `.hook`): the category tag, a Title Case title, and one sentence with
   the surprising number or contrast in red. This is the whole page in one line.
2. **The core idea** (`h2` + `.lead`): two or three sentences. Define the terms once. Say what it
   is *for*, not just what it is.
3. **Interact** (one or two widgets): see "Widgets" below. This is what makes it a page and not a
   note. Wire it to real numbers.
4. **The one rule to remember** (`.callout` tagged `Rule`): the single flashcard-worthy takeaway.
   Optionally add a second `.callout finding` for a real failure mode or caveat that was hit.
5. **Knobs to turn** (`ul.knobs`): two to four experiments that teach by breaking it. Each names a
   thing to change and what intuition it tests.

### 5. Wire or remove the widgets
The template ships two patterns. Keep what fits the concept, delete the rest cleanly (the HTML
block and its paired `<script>` IIFE are commented so they come out together).

- **Pattern A, slider-lever**: use when one number drives others (rank → params, n → confidence
  interval width, learning rate → step size). Replace the formulas in the IIFE with the real
  relationship.
- **Pattern B, toggle-compare**: use for before/after, naive/correct, A/B (base vs fine-tuned
  output, wrong vs right proof step). One object per case in the `DATA` array.

If neither fits, a static inline SVG (a real chart, a labelled diagram) is a fine third option;
follow the chart rules in the style section. Never leave an empty or placeholder widget on a
shipped page.

### 6. Register the card on the shelf
Open `index.html` and add one card inside `<div class="grid" id="shelf">`, immediately **above**
the ghosted `card soon` placeholder, so the newest real page sits last among the real ones. Use
this exact shape:

```html
      <a class="card" href="pages/<concept>.html">
        <span class="pill">Category</span>
        <h2>Page title</h2>
        <p>One sentence on what it teaches and the payoff.</p>
        <div class="foot"><span>~5 min, interactive</span><span class="arrow">open →</span></div>
      </a>
```

The page count in the meta row is computed by script from the number of real cards, so it stays
correct on its own. Do not hand-edit it.

### 7. Verify
Confirm: the new file exists in `pages\`, the card links to the right filename, and the page
respects the style guardrails below (run the em-dash and palette check). Tell Antonio the page is
shelved and what it covers, and offer the next obvious card if the session suggests one.

## Style guardrails (Antonio style guide, closed palette)

The template's CSS already encodes these; your job is to not violate them in the content you write.

- **Palette is closed.** Only these: Signal Red `#C8102E` (accent, the anchor), Muted Rose
  `#C45C6E` (teaching header bar), Vivid Red `#D94055` (hover/active only, fine here because pages
  are interactive), Deep Crimson `#4A0A18` (a Finding callout's accent), Dark Grey `#2B2B2B`
  (titles/headings), Mid Grey `#5A5A5A` (body), Light Grey `#F2F2F2` (panel fills), Rule Grey
  `#D0D0D0` (borders), `#999999` (captions/footer), white background. Introduce no new colours.
  Red stays a signal, not wallpaper (keep it under ~15% of the page).
- **No em-dashes anywhere.** This is the easiest rule to break in prose. Replace: consequence or
  elaboration → colon; joined clauses → semicolon; aside → comma pair or parentheses; abrupt break
  → restructure the sentence. The en dash `–` appears only as the red bullet marker in the knobs
  list (already in CSS), never in running text.
- **Typography**: Helvetica Neue only. Section headings (`h2`) UPPERCASE Dark Grey. Title in Title
  Case. Body sentence case. Bold for structure, never italic for emphasis, never underline.
- **Callout tags are functional**, not generic: `Rule`, `Finding`, `Note`, `Alert`. Never "key
  takeaway". Match the tag to what the box actually is.
- **Numbers**: spell out one through nine in prose; numerals for 10 and up; `%` with no space;
  comma thousands separator. Data values, code, and axis labels keep their literal form.
- **Every visual must carry information.** No decorative flourishes. If a widget or figure cannot
  be captioned with a specific claim, cut it. Charts get a Dark Grey bold title above and a
  `#999999` source/context note below.

## Quick conformance check

After writing, from `C:\dev\MyLearning` run:

```bash
grep -rn "—" pages/<concept>.html        # expect: none in prose (title tab separator uses ·)
grep -rn "C20E1A\|#000000\|#000\b" pages/<concept>.html   # expect: none (off-palette / pure black)
```

## What to resist

- Inventing numbers to make a widget look richer. Real and modest beats fake and slick.
- Adding sections beyond the five. The arc is the product; length is not.
- Restyling. The template is the identity; if it needs to change, change the template and the
  existing pages together, not one page in isolation.
- Building a generator script or page manifest. At this scale, hand-adding one card is cheaper than
  the machinery. Revisit only past roughly eight pages, when maintaining the shelf by hand starts
  to bite; then a small build step that regenerates `index.html` from `pages\` earns its keep.
