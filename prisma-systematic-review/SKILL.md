---
name: prisma-systematic-review
description: >
  Execute a full PRISMA 2020-aligned systematic review workflow. ALWAYS use this skill
  when the user asks to "do a systematic review", "conduct a literature review", "run a
  scoping review", "map the evidence on X", "synthesise the literature", "screen papers
  for inclusion", "assess risk of bias", "produce a PRISMA flow diagram", "rapid review",
  "narrative review", "quick evidence digest", or "background literature search". Phase 0
  routes by review type: systematic/scoping follow the full pipeline; rapid/narrative skip
  protocol registration (Phase I.4), use single screener, narrative synthesis only
  (Phase V.3), and no meta-analysis. ALL review types produce a PRISMA 2020 flow diagram
  (Phase VI) — mandatory and non-negotiable. Integrates with Zotero, PubMed MCP,
  bioRxiv MCP, and scientific-databases tools. Output formatted per antonio-style.
---

# PRISMA 2020 Systematic Review Skill

A structured, reproducible pipeline for evidence synthesis. Covers all phases from
protocol registration to final reporting. Integrates directly with the user's
existing literature infrastructure (Zotero, PubMed MCP, bioRxiv, scientific-databases).

**Reference:** Page MJ et al. (2021). PRISMA 2020 statement. *BMJ*, 372, n71.
DOI: 10.1136/bmj.n71

---

## Skill map — where to go for what

| What you need | Section |
|---|---|
| **Identify review type & lock pipeline** | **Phase 0 — Routing ⚡ START HERE** |
| Formulate the research question | Phase I — PICOS |
| Build a search strategy | Phase II — Search |
| Screen records | Phase III — Screening |
| Extract data & assess bias | Phase IV — Extraction & RoB |
| Synthesise results | Phase V — Synthesis |
| Generate PRISMA flow diagram | Phase VI — Flow Diagram (**mandatory all types**) |
| Write/review the manuscript | Phase VII — Reporting |
| Tool routing for database searches | → Use `scientific-literature` skill |
| Output formatting | → Use `antonio-style` skill for any file |
| Reference management | → Use `zotero-search` skill |

---

## Phase 0 — Review mode routing ⚡ START HERE

**Trigger:** always. Before any other phase, identify the review mode and lock the pipeline accordingly. Ask the user if unclear.

### 0.1 Route by review type

| Review type | Trigger phrases | Pipeline |
|---|---|---|
| **Systematic review** | "systematic review", "exhaustive search", "PROSPERO", "dual screening" | Full pipeline — all phases I–VII |
| **Scoping review** | "scoping review", "map the evidence", "what's been published on", "extent of literature" | Full pipeline — all phases I–VII; skip RoB (Phase IV.2) and meta-analysis (Phase V.2) |
| **Rapid review** | "rapid review", "quick synthesis", "evidence digest", "for policy", "MSF field ops" | **Streamlined pipeline** — see 0.2 |
| **Narrative review** | "narrative review", "background search", "literature background", "overview of evidence" | **Streamlined pipeline** — see 0.2 |

### 0.2 Streamlined pipeline — rapid and narrative reviews

Rapid and narrative reviews follow a compressed version of the full workflow. Apply these deviations **explicitly** and document them in the Methods section of any output:

- **Skip Phase I.4** (protocol registration) — no PROSPERO or OSF registration required; note this as a limitation
- **Single screener** throughout (Phase III) — no dual independent screening; a 10% spot-check is recommended but not mandatory
- **Skip Phase IV.2** (formal Risk of Bias tool) — use a brief quality flag column in the extraction table (High / Medium / Low confidence, with one-line rationale) instead of RoB 2 / ROBINS-I / NOS
- **Skip Phase V.2** (meta-analysis) — go directly to Phase V.3 (narrative synthesis) regardless of apparent homogeneity; do not pool estimates
- **Skip Phase VII PRISMA checklist** (mandatory items apply only to full systematic reviews) — report methods transparently but without item-by-item compliance

**These deviations do not affect Phase VI.** The PRISMA 2020 flow diagram is mandatory for all review types — see below.

### 0.3 PRISMA flow diagram — mandatory for ALL review types

> ⚠️ **Non-negotiable:** Every review produced using this skill — systematic, scoping, rapid, or narrative — **must** include a PRISMA 2020 flow diagram (Phase VI). There are no exceptions. A review without a flow diagram is incomplete output.

The flow diagram:
- Documents identification, screening, eligibility, and inclusion counts
- Is generated as an SVG using the visualiser tool (see Phase VI for full instructions)
- Uses antonio-style colours: Signal Red `#C8102E` borders, Dark Grey `#2B2B2B` text, Light Grey `#F2F2F2` fills
- Is embedded as Figure 1 in any document output with the caption: *"Figure 1. PRISMA 2020 flow diagram of study selection."*

For rapid and narrative reviews where a full two-stage screen was not conducted: adapt the flow to reflect what was done (e.g. collapse title and abstract screening into a single stage, or add a "hand-searched" node). The diagram must accurately reflect the actual process — do not generate a pro-forma diagram that misrepresents the search.

---

## Phase I — Planning & PICOS

**Trigger:** user says "start a systematic review", "help me design the review",
"what's my research question", or "write my protocol".

### 1.1 Identify the review type

| Type | When to use | Key distinction |
|---|---|---|
| **Systematic review** | Exhaustive evidence synthesis on a focused question | Full PRISMA protocol, dual screening, RoB assessment |
| **Scoping review** | Map the breadth/extent of a field; no appraisal | PRISMA-ScR extension; no RoB required |
| **Rapid review** | Timely evidence summary (e.g. for policy, MSF field ops) | Streamlined search; single screener acceptable with checks |
| **Narrative review** | Thematic synthesis without full search transparency | Less rigorous; document decisions explicitly |

### 1.2 Formulate the question — PICOS framework

Clarify each element before writing the search strategy. Ask the user if any are
undefined.

| Element | Question | Example (HIV / LA ART context) |
|---|---|---|
| **P** Population | Who? | PLHIV on first-line ART in Sub-Saharan Africa |
| **I** Intervention | What is done? | Cabotegravir + rilpivirine (CAB/RPV) long-acting |
| **C** Comparator | Compared to? | Oral daily ART (e.g. TLD) |
| **O** Outcome(s) | What is measured? | Virological suppression at 48 weeks; retention in care |
| **S** Study design | What study types? | RCTs, cohort studies; minimum follow-up 24 weeks |

**Output:** Write the PICOS as a structured summary the user can paste into a PROSPERO
or OSF registration form. See `references/protocol-template.md` for the full template.

### 1.3 Eligibility criteria

Define inclusion/exclusion criteria against each PICOS element. Format as a two-column
table: **Include if** / **Exclude if**. Common exclusion reasons to pre-specify:
- Wrong population (e.g. paediatric when adult-only review)
- Wrong comparator or no comparator data
- Wrong study design (e.g. case reports, editorials, commentaries)
- No extractable outcome data
- Abstract-only or conference presentation without full text
- Non-peer-reviewed (flag but do not auto-exclude preprints — assess case by case)

### 1.4 Protocol registration

**PROSPERO** (NIHR — preferred for clinical systematic reviews): https://www.crd.york.ac.uk/prospero/
**OSF** (Open Science Framework — preferred for scoping reviews, mixed methods): https://osf.io/

Record the registration number before conducting the search. Note it in the manuscript
Methods section.

---

## Phase II — Literature Search (Identification)

**Trigger:** user says "run the search", "search the databases", "find papers on X",
"what search string should I use", or "build the Boolean query".

### 2.1 Hand off to `scientific-literature` skill

For all database searches, load and follow the `scientific-literature` SKILL.md.
Use its routing guide to parallelise:

- `PubMed:search_articles` — primary biomedical retrieval (MeSH + Boolean)
- `search_europe_pmc` — field-structured supplement
- `search_openalex` — breadth + OA status + concept mapping
- `search_semantic_scholar` — TL;DR, influential citations
- `bioRxiv:search_preprints` (server=`medrxiv` for clinical topics) — preprints

Also check Zotero via `zotero-search` skill for pre-curated papers before any
external search.

### 2.2 Boolean query construction

Use the PICOS elements to build parallel concept blocks:

```
(Concept-P: population terms)
AND (Concept-I: intervention terms)
AND (Concept-C: comparator, if narrow enough)
AND (Concept-O: outcome terms — only if needed to limit scope)
```

**Rules:**
- Use `OR` within concept blocks (synonyms, alternate spellings, MeSH + free text)
- Use `AND` between blocks
- Use `NOT` sparingly — it can exclude relevant papers
- Always pair free-text terms with MeSH terms for PubMed

**Example for CAB/RPV review:**
```
("cabotegravir" OR "cabotegravir-rilpivirine" OR "CAB/RPV" OR "long-acting ART"
 OR "injectable antiretroviral" OR "long-acting injectable")
AND
("HIV" OR "HIV-1" OR "PLHIV" OR "antiretroviral therapy" OR "ART")
AND
("virological suppression" OR "viral load" OR "treatment outcome" OR "retention"
 OR "adherence")
```

### 2.3 Grey literature

For MSF / humanitarian / LMIC contexts, grey literature is high-value. Search:
- ClinicalTrials.gov (https://clinicaltrials.gov)
- WHO ICTRP (https://trialsearch.who.int)
- MSF Field Research (https://fieldresearch.msf.org)
- medRxiv preprints (via `bioRxiv:search_preprints` server=`medrxiv`)
- Hand-searching reference lists of included studies (citation tracking)
- Forward citation search via `get_paper_citations` (Semantic Scholar)

### 2.4 Search documentation

Record for reproducibility (required by PRISMA 2020):
- Full search string for each database
- Database name and platform (e.g. PubMed/MEDLINE via NCBI, accessed via MCP)
- Date of search
- Total records retrieved per database

Save raw results to Zotero or a deduplication sheet before screening.

---

## Phase III — Screening (Selection)

**Trigger:** user says "screen these papers", "which papers meet inclusion criteria",
"help me screen", "title-abstract screening", or "full-text assessment".

### 3.1 Deduplication

Remove duplicate records before screening. Deduplication order:
1. Match on DOI (most reliable)
2. Match on PMID
3. Match on Title + Year (for records without DOIs, e.g. grey literature)

Report: `N records before deduplication — N duplicates removed — N unique records screened`

### 3.2 Stage 1 — Title/Abstract screening

**Decision rule:**
- **Include:** meets all PICOS inclusion criteria (or cannot be excluded on title/abstract alone)
- **Exclude:** clearly outside population, intervention, or study type; not the right language
- **Uncertain:** retrieve full text; do not exclude at this stage

**For large record sets (>200):**
Use structured inclusion/exclusion criteria as a checklist. Process in batches of 50.
Apply the criteria strictly — over-inclusion at Stage 1 is acceptable (resolved at Stage 2);
over-exclusion is not.

**For rapid reviews:** single screener with 10% spot-check by second reviewer is acceptable.
**For full systematic reviews:** dual independent screening; conflicts resolved by discussion
or third reviewer.

### 3.3 Stage 2 — Full-text screening

Retrieve PDFs for all Stage 1 includes and uncertains. Apply eligibility criteria at
full-text level. **Record a specific reason for each exclusion** — this is mandatory for
PRISMA reporting:

Common exclusion reasons (pre-code these before starting):
- A: Wrong population
- B: Wrong intervention (no CAB/RPV or no LA ART arm)
- C: Wrong comparator
- D: Wrong outcome (no virological or clinical endpoint reported)
- E: Wrong study design (case report, editorial, letter, review without primary data)
- F: Follow-up < minimum threshold (e.g. < 24 weeks)
- G: Full text not available
- H: Duplicate (secondary publication of included study)
- I: Abstract-only, conference proceedings

**Output of Phase III:**
Complete PRISMA flow counts (see Phase VI for diagram generation).

---

## Phase IV — Data Extraction & Risk of Bias

**Trigger:** user says "extract data from these papers", "fill out the extraction form",
"assess risk of bias", "quality assessment", or "GRADE the evidence".

### 4.1 Data extraction form

Extract at minimum:

**Study characteristics:**
- First author, Year, Country / Setting, Study design
- Sample size (N total; N per arm)
- Population characteristics (age, sex, CD4 count, prior ART duration)
- Follow-up duration

**Intervention details:**
- Drug name, dose, route, frequency
- Comparator description

**Outcomes:**
- Primary: Virological suppression (viral load < 50 copies/mL) at week 48 (or reported timepoint)
- Secondary: Retention in care %; adverse events (grade 3/4); resistance mutations; patient preference

**Statistical data:**
- Effect measure (OR, RR, HR, %); 95% CI; p-value; number of events / N

**Funding / conflicts of interest**

### 4.2 Risk of Bias tools by study design

| Study design | Tool | Key domains |
|---|---|---|
| Randomised controlled trial | **RoB 2** (Cochrane) | Randomisation; deviations; missing data; measurement; reporting |
| Non-randomised interventional | **ROBINS-I** | Confounding; selection; classification; deviations; missing; measurement; reporting |
| Observational (cohort, case-control) | **Newcastle-Ottawa Scale (NOS)** | Selection; comparability; outcome |
| Diagnostic accuracy | **QUADAS-2** | Patient selection; index test; reference standard; flow and timing |
| Qualitative | **CASP Qualitative Checklist** | Reflexivity; rigour; transferability |

**Reporting:**
- Present RoB judgements as a summary table (one row per study, one column per domain)
- Do NOT exclude studies based on quality alone
- Use RoB results to inform evidence certainty (GRADE) in the synthesis

### 4.3 GRADE certainty assessment (optional but recommended)

Rate certainty per outcome across all included studies:
- **High:** Probably close to the true effect
- **Moderate:** Probably close but uncertainty exists
- **Low:** Might be close but substantial uncertainty
- **Very Low:** Very uncertain

Downgrade for: risk of bias, inconsistency, indirectness, imprecision, publication bias.
Upgrade for: large effect, dose-response, residual confounding working against the effect.

---

## Phase V — Synthesis

**Trigger:** user says "synthesise the results", "can I do a meta-analysis", "pool the data",
"forest plot", "what's the overall finding", or "how heterogeneous are the results".

### 5.1 Decide: narrative vs quantitative synthesis

Ask:
1. Are study populations sufficiently similar? (Population homogeneity)
2. Are outcome definitions consistent? (Outcome homogeneity)
3. Are follow-up periods comparable?
4. Is the number of studies ≥ 3–4?

If YES to all → proceed to meta-analysis (5.2)
If NO to any → use narrative synthesis (5.3)

**PRISMA 2020 note:** Justification for synthesis choice must be stated in Methods.

### 5.2 Quantitative synthesis — meta-analysis

**Effect measures:**
- Binary outcomes: Risk Ratio (RR) or Odds Ratio (OR); use RR for common outcomes
- Continuous outcomes: Mean Difference (MD) or Standardised MD (Cohen's *d*)
- Time-to-event: Hazard Ratio (HR)

**Model selection:**
- Fixed-effect: use only if studies are near-identical (same intervention, population, setting)
- Random-effects (DerSimonian-Laird or REML): preferred when any heterogeneity is expected

**Heterogeneity assessment:**
- **I²** < 25% = low; 25–50% = moderate; > 50% = high; > 75% = very high
- **τ²** (tau-squared) — between-study variance estimate; report alongside I²
- **Q statistic** p-value — flag if p < 0.10
- If I² > 50%: explore via subgroup analysis or meta-regression before pooling

**Recommended R packages:**
```r
library(meta)       # meta-analysis, forest plots
library(metafor)    # REML, meta-regression, funnel plots
library(dmetar)     # heterogeneity, outliers, Egger's test helpers
```

**Publication bias:**
- Funnel plot asymmetry (visual; requires ≥ 10 studies to be informative)
- Egger's test (statistical; `metabias()` in R)
- Trim-and-fill method if asymmetry detected

### 5.3 Narrative synthesis

Use when meta-analysis is not appropriate. Structure as:
1. **Direction of effect** per study (benefit / no effect / harm)
2. **Vote-counting** (n studies showing benefit vs no effect)
3. **Effect magnitude range** (lowest to highest reported effect)
4. **Subgroup observations** (e.g. effects differ by region or baseline VL)

Narrative synthesis must still be systematic — document decisions and do not cherry-pick.

---

## Phase VI — PRISMA 2020 Flow Diagram

**Trigger:** user says "generate the PRISMA flow", "make the flow diagram", "how many
papers made it through", or "PRISMA diagram".

### 6.1 Collect the counts

Before generating the diagram, confirm these numbers with the user:

```
IDENTIFICATION
  Records from databases:          ___
  Records from other methods:      ___
  Duplicate records removed:       ___
  Records screened (Title/Abs):    ___
  Records excluded (Title/Abs):    ___

ELIGIBILITY
  Full-texts retrieved:            ___
  Full-texts not retrieved:        ___
  Full-texts excluded:             ___
    (list reasons and N for each)  ___

INCLUDED
  Studies in qualitative synthesis: ___
  Studies in quantitative synthesis (meta-analysis): ___
```

### 6.2 Generate the diagram

Once counts are confirmed, produce an SVG PRISMA 2020 flow diagram using the
visualiser tool. See `references/prisma-flow-template.md` for the standard node
layout and colour coding (uses antonio-style: Signal Red `#C8102E` for borders,
Dark Grey `#2B2B2B` for text, Light Grey `#F2F2F2` for box fills).

For docx/pdf output: embed the SVG as a figure with a caption:
*"Figure 1. PRISMA 2020 flow diagram of study selection."*

---

## Phase VII — Manuscript Reporting

**Trigger:** user says "write the methods section", "draft the results", "help me
write up the review", or "check my manuscript against PRISMA".

### 7.1 PRISMA 2020 checklist — mandatory items by section

**Title:** Must identify report as systematic review (or meta-analysis if applicable).

**Abstract:** Structured — Background, Methods, Results (N included, main findings),
Conclusions, Registration number.

**Introduction:**
- Rationale: Why this review is needed; what the gap is
- Objectives: Research question in PICOS terms

**Methods (all of these must appear):**
- Eligibility criteria (PICOS)
- Information sources (databases, dates, grey literature)
- Full search strategy for at least one database (copy-paste exact string)
- Selection process (who screened; how conflicts resolved)
- Data extraction process (form piloted; dual extraction or not)
- List of data items extracted
- Risk of bias assessment (tool used; who assessed)
- Effect measures and synthesis methods
- If meta-analysis: heterogeneity assessment, model, publication bias
- Any deviations from registered protocol

**Results:**
- PRISMA flow diagram (Figure 1)
- Study characteristics table
- Risk of bias summary
- Results of individual studies (forest plot or table)
- Synthesis results (pooled estimates or narrative)
- Publication bias (if applicable)

**Discussion:**
- Summary of main findings
- Limitations (search limitations, risk of bias, heterogeneity)
- Conclusions

**Supplementary:**
- Full search strings for all databases
- PRISMA 2020 checklist (completed)
- Excluded studies list with reasons

### 7.2 Common reporting gaps (flag these in manuscript review)

- Missing: exact search string in supplementary
- Missing: dates of database searches
- Missing: reason for exclusion for each full-text excluded
- Missing: risk of bias judgement for each included study
- Missing: PROSPERO/OSF registration number
- Missing: conflict of interest statement and funding source
- Missing: protocol deviations from preregistered plan

### 7.3 File output

For any document output, load `antonio-style` SKILL.md and apply the full style guide:
- Manuscript → DOCX (use docx skill)
- One-page summary → PDF (use pdf skill)
- Slide presentation of findings → PPTX (use pptx skill)
- Data extraction table → XLSX (use xlsx skill)

File naming: `[Org]_[Topic]_SystematicReview_[Version].[ext]`
Example: `MSF_CAB-RPV_SystematicReview_v1.docx`

---

## Quick reference — workflow checklist

```
☐ 0. ROUTING — identify review type; apply streamlined pipeline if rapid/narrative
☐    Rapid/narrative: confirm skip of Phase I.4, dual screening, meta-analysis
☐    ALL types: confirm PRISMA flow diagram will be produced (non-negotiable)

☐ 1. Identify review type (systematic / scoping / rapid / narrative)
☐ 2. Formulate PICOS — confirm with user
☐ 3. Define inclusion/exclusion criteria — pre-specify exclusion reason codes
☐ 4. [SYSTEMATIC/SCOPING ONLY] Register protocol (PROSPERO or OSF)
☐ 5. Build Boolean query — document full string + date for each database
☐ 6. Run search via scientific-literature skill (Zotero → PubMed → OpenAlex → medRxiv)
☐ 7. Record: N records per database; total before dedup
☐ 8. Deduplicate by DOI → PMID → Title+Year
☐ 9. Stage 1: Title/Abstract screen — report N excluded
☐    [SYSTEMATIC/SCOPING] Dual screener; [RAPID/NARRATIVE] Single screener + 10% spot-check
☐ 10. Stage 2: Full-text screen — report N excluded + reason per paper
☐ 11. Confirm PRISMA flow counts with user
☐ 12. ⚠️ Generate PRISMA 2020 flow diagram (SVG → embed in output) — MANDATORY ALL TYPES
☐ 13. Data extraction — use standardised form
☐ 14. [SYSTEMATIC/SCOPING ONLY] Risk of bias assessment (RoB 2 / ROBINS-I / NOS)
☐     [RAPID/NARRATIVE] Quality flag column (High / Medium / Low + one-line rationale)
☐ 15. Synthesis decision:
☐     [SYSTEMATIC/SCOPING] meta-analysis or narrative per Phase V.1
☐     [RAPID/NARRATIVE] narrative synthesis only (Phase V.3) — no pooling
☐ 16. [SYSTEMATIC/SCOPING + META-ANALYSIS ONLY] Heterogeneity → model → publication bias
☐ 17. GRADE certainty per outcome (optional but recommended for systematic/scoping)
☐ 18. Draft manuscript per PRISMA 2020 checklist [SYSTEMATIC/SCOPING] or transparent
☐     methods narrative [RAPID/NARRATIVE]
☐ 19. Apply antonio-style to output files
☐ 20. Verify all PRISMA reporting gaps before submission [SYSTEMATIC/SCOPING]
```

---

## Reference files

- `references/protocol-template.md` — Full PROSPERO/OSF protocol registration template
- `references/extraction-form.md` — Standardised data extraction form (generic + HIV-specific)
- `references/rob-tools.md` — RoB 2, ROBINS-I, NOS domain descriptions and judgement criteria
- `references/prisma-flow-template.md` — PRISMA 2020 flow diagram node layout for SVG generation

Read a reference file when you need detailed field-by-field guidance; the SKILL.md
body above is sufficient for most tasks.
