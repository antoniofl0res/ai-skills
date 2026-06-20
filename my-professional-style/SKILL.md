---
name: my-professional-style
description: >
  Apply Antonio Flores's personal professional style guide when creating or formatting
  any document, presentation, or file. ALWAYS use this skill when Antonio asks to create
  a report, brief, one-pager, slide deck, meeting materials, or any formal output (even
  if he doesn't say "style guide"). Trigger whenever the user says things like "make it
  look professional", "follow my style", "apply my branding", "format this properly", or
  any time a .docx, .pdf, or .pptx file is being produced for external or formal internal
  audiences. The system is minimalist, credibility-first, monochromatic red, Helvetica
  Neue, white-background.
---

# Antonio Flores: Professional Style Guide

This skill governs the visual and editorial standards for all professional files Antonio
produces: reports, briefs, one-pagers, slide decks, meeting materials.

**Design philosophy: minimalist, clean, credibility-first.**

Four governing principles:
1. **Clarity over decoration:** every element must earn its place
2. **Consistency across formats:** same colour, font, and structural logic across DOCX, PDF, PPTX
3. **Red as a signal, not wallpaper:** the red family is for orientation and urgency only; never decorative fill
4. **White space is not wasted space:** generous margins communicate confidence

---

## Critical Defaults: Apply These First

Ten rules sufficient for most outputs. Read the full sections below only when edge cases arise.

1. **Background**: always white (`#FFFFFF`); never coloured
2. **Primary accent**: Signal Red `#C8102E`; structural roles only; max ~15% of any page or slide
3. **Body text**: Helvetica Neue 9–10 pt, Mid Grey `#5A5A5A`
4. **Headings**: Dark Grey `#2B2B2B`; section headings in UPPERCASE
5. **Header bar**: choose variant by audience (see Header Variants below)
6. **Bullets**: en dash (–) in Signal Red; bullet body in Mid Grey
7. **Chart primary series**: Signal Red `#C8102E`; any chart with 3+ series must add a dash/shape secondary cue
8. **Status semantics**: Deep Crimson = critical, Signal Red = alert, Muted Rose = flagged, Grey = OK/baseline
9. **Vivid Red `#D94055`**: interactive/hover states only; never use in print or static documents
10. **Palette is closed**: 13 named entries only; never introduce new colours

---

## Colour Palette

The palette is monochromatic: all accent colours derive from the same red hue (H ≈ 350°),
differentiated by lightness and saturation. Neutrals are unchanged from the base system.

### Red Family

| Name | Hex | Role |
|---|---|---|
| Deep Crimson | `#4A0A18` | Critical alerts; urgent header variant; darkest chart series |
| Dark Red | `#8B0A1E` | Internal/operational header variant |
| Signal Red | `#C8102E` | **Brand anchor:** header bars, accent bars, category pills, bullets, chart primary |
| Vivid Red | `#D94055` | Hover/active states in interactive contexts only; not for print |
| Muted Rose | `#C45C6E` | Academic/teaching header variant; desaturated secondary data series |
| Blush | `#E8929A` | Tertiary chart series; light-fill badge backgrounds |
| Pale Red | `#F8C8CE` | Text on red-filled backgrounds (e.g. header bar sub-label); light fills |
| Whisper | `#FDF0F1` | Very light section tints; hover backgrounds |

### Neutrals

| Name | Hex | Role |
|---|---|---|
| Dark Grey | `#2B2B2B` | All titles, headings, section labels |
| Mid Grey | `#5A5A5A` | Body text, captions, badge labels, subtitles |
| Light Grey | `#F2F2F2` | Card/section backgrounds, table row fills, callout boxes |
| Rule Grey | `#D0D0D0` | Divider lines, column rules, badge borders, table borders, chart reference lines |
| White | `#FFFFFF` | Page/slide backgrounds; text on red fills |

### Colour Rules

- Red fills must not cover more than ~15% of any page or slide
- Red must never be used for running body text
- Palette is closed; do not introduce new colours
- All text/background combos must meet WCAG AA contrast (4.5:1 minimum)
- Never use pure black (`#000000`); use Dark Grey (`#2B2B2B`)
- No gradients, drop shadows, or glow effects
- Vivid Red (`#D94055`) is for interactive contexts only; never in print or static files
- When in doubt, default to Signal Red; use darker stops only when content warrants greater urgency

---

## Typography

**Font family:** Helvetica Neue (fallback: Arial, then any system sans-serif). Single typeface only; no mixing.

### Document scale (DOCX / PDF — A4 or Letter)

| Role | Size | Weight | Colour | Case |
|---|---|---|---|---|
| Document title | 22 pt | Bold | Dark Grey | Title Case |
| Section heading | 11 pt | Bold | Dark Grey | UPPERCASE |
| Sub-heading | 9 pt | Bold | Dark Grey | UPPERCASE |
| Body text | 9–10 pt | Regular | Mid Grey | Sentence case |
| Category tag / pill | 8.5 pt | Bold | White on Red | UPPERCASE |
| Badge / meta label | 7.5 pt | Regular | Mid Grey | Sentence case |
| Caption / footnote | 7.5 pt | Regular | `#999999` | Sentence case |
| Header bar subtitle | 8 pt | Regular | Pale Red | Sentence case |
| Footer text | 7 pt | Regular | `#999999` | Sentence case |

### Presentation scale (PPTX — 16:9 Widescreen)

| Role | Size | Weight | Colour | Case |
|---|---|---|---|---|
| Slide title | 28–32 pt | Bold | White on Red | Title Case |
| Section label / tag | 10 pt | Bold | White on Red | UPPERCASE |
| Sub-heading | 14 pt | Bold | Dark Grey | Title Case |
| Body text | 11 pt | Regular | Mid Grey | Sentence case |
| Callout / highlight | 11 pt | Bold | Signal Red | Sentence case |
| Caption / footnote | 8 pt | Regular | `#999999` | Sentence case |
| Speaker notes | 10 pt | Regular | Mid Grey | — |
| Footer | 8 pt | Regular | `#999999` | — |

**Typography rules:**
- Bold for structural emphasis (headings, tags); never italic
- Avoid underline (implies hyperlink)
- Line spacing: 1.15× for body text; 1.0× for labels and tags
- Paragraph spacing: 6 pt after each paragraph
- Do not use more than two font weights on a single page or slide
- Do not stretch, condense, or skew any typeface

---

## Layout & Spacing

### Documents (A4 / Letter)
- Left/Right margins: 22 mm
- Top margin: 18 mm (content begins below header bar)
- Bottom margin: 14 mm (above footer)
- Header bar height: 18 mm
- Footer zone height: 10 mm
- Section card padding: 8 mm internal; 3 mm corner radius
- Column gutter (2-col): 8 mm
- Space between cards: 6 mm

### Presentations (16:9 — 33.87 cm × 19.05 cm)
- Safe zone (all sides): 1.4 cm (40 pt)
- Header bar height: ~2.9 cm (~15% of slide height)
- Footer zone height: ~1.5 cm (~8% of slide height)
- Content block padding: 0.85 cm (24 pt) internal margin
- Column gutter (2-col): 0.85 cm

### Grid & Columns
- **Single column:** default for all document types
- **Two columns:** structured info cards (docs) or comparison slides (pptx); always separated by a 0.5 pt Rule Grey line
- **Three columns:** only for data-dense reference slides; never in documents
- **Tables:** always use Light Grey row fills; Rule Grey borders, 0.5 pt

---

## Structural Elements

### Header Bar Variants (Documents & Presentations)

The header bar colour encodes audience and urgency. Choose one variant per document; do not mix within a document.

| Variant | Hex | Context |
|---|---|---|
| Formal / External | `#C8102E` Signal Red | External reports, publications, MSF formal output |
| Internal / Operational | `#8B0A1E` Dark Red | Internal briefs, field operational documents |
| Urgent / Alert | `#4A0A18` Deep Crimson | SITREPs, field alerts, critical notices |
| Academic / Teaching | `#C45C6E` Muted Rose | UFRGS materials, training content, lower-urgency register |

**Header bar layout (all variants):**
Full-width rectangle, 18 mm tall (documents) or ~15% slide height (presentations), flush to top.
- Left: Organisation or author name; Helvetica-Bold 10 pt, White
- Right: Document context label; Helvetica 8 pt, Pale Red
- No logos or imagery inside the bar

### Section Cards (Documents)
Rounded rectangle, 3 mm corner radius, Light Grey fill, no stroke.
- Left accent bar: Signal Red, 3 mm wide, full card height, 1.5 mm radius
- Internal padding: 8 mm from accent bar edge to text
- One card per major content section

### Category Pills / Tags

Pill colour encodes severity or status. Choose the appropriate stop:

| Pill type | Fill | Text | Case |
|---|---|---|---|
| CRITICAL | Deep Crimson `#4A0A18` | Pale Red `#F8C8CE` | UPPERCASE |
| ALERT | Signal Red `#C8102E` | White `#FFFFFF` | UPPERCASE |
| FLAGGED | Muted Rose `#C45C6E` | White `#FFFFFF` | UPPERCASE |
| OK / BASELINE | Light Grey `#F2F2F2` | Mid Grey `#5A5A5A` | UPPERCASE |
| CLOSED / INACTIVE | Dark Grey `#2B2B2B` | Light Grey `#F2F2F2` | UPPERCASE |

Pill geometry: rounded rectangle, 1.5 mm corner radius. Height: 7 mm. Width: auto-fit with 6 mm horizontal padding. Font: Helvetica-Bold 8.5 pt.

### Meta Badges (status, time, version)
Rounded rectangle, 1.5 mm corner radius, White fill, 0.7 pt Mid Grey stroke.
- Text: Helvetica 7.5 pt, Mid Grey
- Position: immediately to the right of a category pill when paired

### Divider Lines
- Colour: Rule Grey (`#D0D0D0`). Weight: 0.5 pt
- Uses: column separators, footer rule, between major page sections
- Never use 1 pt or heavier; never use black lines

### Footer (Documents)
0.5 pt Rule Grey line running full content width above footer text.
- Left: Author or organisation name | Document context
- Right: Document title or page number
- Font: Helvetica 7 pt, `#999999`

### Slide Footer (Presentations)
0.5 pt Rule Grey line above footer zone.
- Left: Event, project, or organisation name; Helvetica 8 pt, `#999999`
- Right: Slide number; Helvetica 8 pt, `#999999`

### Callout Boxes (both formats)
Light Grey background, 3 mm corner radius, 2 mm left accent bar in Signal Red.
- Use sparingly for key takeaways, warnings, or critical data points
- Font: Helvetica-Bold 9 pt, Dark Grey for label; Regular for body text
- For critical callouts: use Whisper (`#FDF0F1`) background with Deep Crimson accent bar

---

## Document Types

| Type | Format | When to use |
|---|---|---|
| One-pager | PDF | Quick briefings, meeting references, guidelines |
| Report / brief | DOCX | Multi-section analysis, written deliverables |
| Slide deck | PPTX | Presentations, workshops, meetings |
| Data summary | XLSX | Tabular data, trackers, structured outputs |
| Reference card | PDF | Field guides, checklists, quick-reference tools |

**Length guidelines:**
- One-pager: 1 page (strictly)
- Executive brief: 2–3 pages
- Full report: no limit, but each section starts on a new page
- Slide deck: 1 idea per slide; ~10–15 slides for a 15-min talk

---

## Bullet Points & Lists

- Bullet character: en dash (–) in Signal Red
- Bullet text font: Helvetica Regular, Mid Grey
- Text indent: 4 mm from bullet character
- Spacing between items: 2 mm; between groups: 3 mm
- Maximum nesting depth: 2 levels (never 3 or more)
- Sub-bullet character: small red dot (·), indented 6 mm
- Numbered lists: reserved for sequential processes or ranked items
- Checklists: use ✓ (White on Signal Red) or ✗ (White on Deep Crimson) only when state carries meaning

**Do not:**
- Use standard round bullets (•)
- Use UPPERCASE text in bullet content
- Exceed 2 lines per bullet in presentations

---

## Tables

| Element | Specification |
|---|---|
| Header row | Signal Red fill, White text, Helvetica-Bold 9 pt |
| Data rows | Alternate White and Light Grey fills |
| Cell text | Helvetica Regular 9 pt, Dark Grey or Mid Grey |
| Borders | Rule Grey, 0.5 pt; no thick outer borders |
| Cell padding | 3 mm horizontal, 2 mm vertical |
| Alignment | Text left-aligned; numbers right-aligned |
| Caption | Above the table, Helvetica-Bold 8 pt, Dark Grey |

---

## Charts & Data Visualisation

### Series Palette

The chart palette is monochromatic. Use stops in order; do not skip entries.

| Series | Hex | Name |
|---|---|---|
| Primary | `#C8102E` | Signal Red |
| Secondary | `#4A0A18` | Deep Crimson |
| Tertiary | `#C45C6E` | Muted Rose |
| Quaternary | `#E8929A` | Blush |
| Reference / baseline | `#D0D0D0` | Rule Grey |

**Accessibility rule (mandatory for 3+ series):** Pair each red series with a distinct secondary visual cue. Use either dash pattern (solid / dashed / dotted / dash-dot) or marker shape (circle / square / triangle / diamond). Never rely on colour stop alone for series identification in print or export.

### General Chart Rules
- Chart background: White or Light Grey; never coloured
- Gridlines: Rule Grey, 0.3 pt, horizontal only
- Axis labels: Helvetica 8 pt, Mid Grey
- Data labels (if shown): Helvetica-Bold 8 pt, matching series colour
- Chart title: Helvetica-Bold 10 pt, Dark Grey, above the chart
- Source / note: Helvetica 7 pt, `#999999`, below the chart

**Chart type selection:**
- Bar / column → comparisons between categories
- Line → trends over time
- Dot / scatter → correlations or distributions
- **Avoid:** 3D charts, pie charts with more than 4 segments, overlapping area charts

---

## Imagery & Iconography

**Icons:** Simple, consistent line-weight set (e.g. Feather or Material Symbols). Single colour: Dark Grey or Signal Red. No filled/solid decorative icons. Size: 16–20 pt in documents, 24–32 pt in presentations.

**Photography:** Apply subtle Mid Grey overlay (40% opacity) to harmonise with palette. Avoid brightly coloured or heavily filtered images. No generic stock business photography. Prefer documentary or reportage aesthetics: images that establish context, show operational reality, or ground a claim. When human subjects appear, composition must preserve dignity and specificity. No staged imagery. No aspirational or abstract stock.

**Diagrams & process flows:**
- Boxes: Light Grey fill, 2 mm corner radius, no stroke or Rule Grey stroke
- Arrows: Signal Red, 1.5 pt, no decorative arrowheads
- Labels: Helvetica 9 pt, Dark Grey

**Visual register: governing principles**

Every visual element must carry information. Decoration that does not encode meaning is removed.

- **Operational grounding:** prefer maps, timelines, flowcharts, and data tables over illustrative or conceptual graphics. If a visual cannot be captioned with a specific claim, it does not belong.
- **Data as evidence:** every chart, figure, or data point must display its source, time reference, and population in a caption or footnote. Decontextualised statistics are not permitted.
- **No decorative flourishes:** no icon clusters used as visual texture, no gradient blobs, no abstract geometric backgrounds, no purely ornamental dividers. White space performs this function instead.
- **Callout boxes encode urgency:** label callouts with a functional tag (FINDING, RECOMMENDATION, ALERT, NOTE) rather than generic language such as "key takeaway." Tag choice must match the severity semantics defined in the Category Pills table.
- **Infographics:** acceptable only when data complexity justifies them. Must follow the chart series palette and accessibility rules. Never use infographics as substitutes for well-structured prose and a simple table.

---

## Tone & Editorial Rules

**Casing conventions:**

The table below is authoritative. When generating or editing any text, verify each element against it before output. Resolve all conflicts in favour of this table, not the typography scale tables.

| Element | Case | Examples |
|---|---|---|
| Document title | Title Case | "Field Brief on LA ART Rollout" |
| Slide title | Title Case | "Access Gaps in Sub-Saharan Africa" |
| Section heading | UPPERCASE | "CLINICAL FINDINGS" |
| Sub-heading | UPPERCASE | "DOSING SCHEDULE" |
| Body text | Sentence case | "Uptake increased by 34% across sites." |
| Bullets | Sentence case | "Three sites reported stock-outs." |
| Captions and footnotes | Sentence case | "Source: CARES trial, 2024." |
| Category tags and pills | UPPERCASE | ALERT, CRITICAL, FLAGGED |
| Badge and meta labels | Sentence case | "Version 2, June 2025" |
| Header bar subtitle | Sentence case | "Southern Africa Medical Unit" |
| Footer text | Sentence case | "MSF SAMU | Internal brief" |

Note: UPPERCASE in section and sub-headings applies to the heading label only, never to running body text that follows it.

---

**Punctuation rules:**

**No em-dashes.** The em-dash (`—`) is not used anywhere in this style system. When drafting or editing, replace it as follows:

| Em-dash function | Replacement |
|---|---|
| Introducing a consequence or elaboration | Colon (`:`) |
| Connecting two related clauses | Semicolon (`;`) |
| Parenthetical insertion | Comma pair or parentheses |
| Abrupt break or contrast | Restructure the sentence |

**En-dash exception:** the en dash (`–`) is retained exclusively as the bullet list character, rendered in Signal Red. It is a typographic marker, not a punctuation device, and this exception does not apply to running text.

---

**Writing style:**
- Be direct and specific; avoid filler phrases ("It is important to note…", "It should be noted that…")
- Use active voice wherever possible
- Define acronyms on first use; spell out in titles
- Quantify wherever possible ("increased by 34%" not "increased significantly")
- Every sentence must carry a claim, a figure, or an instruction. Remove sentences that only restate what a heading already says.
- Prefer short paragraphs (3–4 sentences maximum) and clear topic sentences
- Questions work well to frame analytical sections, but must be answered within the same section

**Numbers:**
- Spell out one through nine; use numerals for 10 and above
- Comma as thousands separator: 1,000 / 10,500
- Decimal point (not comma) for decimals: 3.5
- Percentages: always use % symbol, no space: 34%

---

## File Naming Convention

**Pattern:** `[Organisation]_[Project-or-Topic]_[DocumentType]_[Version].[ext]`

**Examples:**
- `MSF_LAPrep_PresentationGuidelines_v1.pdf`
- `MSF_AnnualReport_ExecutiveSummary_v2.docx`
- `UFRGS_Simulacao_CapituloTemplate_v1.docx`

**Rules:**
- No spaces; underscores only
- Version format: v1, v2, v3 (not v1.0 or 1.0)
- Date stamp when version alone is insufficient: YYYYMMDD suffix
- Draft files: append `_DRAFT` before the extension
