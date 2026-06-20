---
name: pubmed-websearch-retrieval
description: >
  Use this skill to find, curate, or summarise recent peer-reviewed biomedical
  or clinical research. Trigger whenever the user mentions a medical or health
  topic alongside words like "recent", "latest", "last N days/weeks/months",
  "search PubMed", "literature digest", "evidence roundup", "what's new in",
  or asks for references on any clinical question. Also trigger for HIV, cancer,
  drug efficacy, clinical trial results, prevention research, and global health
  topics — even if the user doesn't say "PubMed" explicitly. Combines the
  PubMed MCP connector (date-verified structured records), Zotero (user's own
  curated library), WebSearch (high-impact journals with indexing lag), and
  optionally preprints (medRxiv/bioRxiv). Never rely on WebSearch alone for
  date-sensitive retrieval — always anchor with PubMed.
---

# Biomedical Literature Retrieval: PubMed + Zotero + WebSearch Protocol

A standardised, reproducible approach for retrieving peer-reviewed biomedical
literature with **zero date ambiguity**. Combines three complementary sources:
the PubMed MCP connector (structured metadata), the user's Zotero library
(curated personal collection), and WebSearch (coverage of journals that lag
PubMed indexing).

---

## Why the multi-source approach?

**PubMed** provides ground truth: PMID, DOI, exact publication date, abstract,
MeSH terms, and article type — structured and machine-readable. But indexing
can lag days to weeks for *NEJM*, *The Lancet*, *JAMA*, *Nature Medicine*, and
*Science*.

**Zotero** surfaces articles the user has already curated and trusted — the
highest-quality starting point for any literature task.

**WebSearch** catches indexing-lagged articles in high-impact journals and
preprint servers, but provides unstructured data with unreliable dates.

**Preprints** (medRxiv, bioRxiv) are increasingly the first publication venue
for HIV prevention, vaccine, and implementation science data — sometimes weeks
ahead of peer-reviewed indexing.

The protocol: **Zotero first → PubMed second → WebSearch/preprints third →
date-verify everything → rank by evidence tier.**

---

## Step 0 — Check the user's Zotero library (if available)

Before any external search, query the user's Zotero library for the topic.
Articles already in Zotero are pre-curated and should be treated as **priority
candidates** regardless of their publication date.

Use the `zotero-search` skill (see its SKILL.md). Run:
- A semantic search on the core topic
- A tag-based search if the user has relevant tags (e.g. "HIV", "PrEP", "CAB-LA")

Flag Zotero hits clearly in the final report:
`| **Source** | Zotero library (user-curated) + PubMed-verified |`

If Zotero is not connected, skip this step and proceed to Step 1.

---

## Step 1 — Define retrieval parameters

Before searching, confirm:
- **Topic**: Condition, drug, intervention, or clinical question
- **Date window**: E.g. "last 60 days" → compute exact start date from today's actual date
- **Categories**: What the user wants to distinguish (e.g. treatment vs prevention, by drug class, by population)
- **Target count**: Default 6–8 articles; more if the user asks
- **Output format**: Inline Markdown (default) or formal DOCX report (see Step 8)

---

## Step 2 — PubMed searches (run in parallel)

Run **2–3 parallel PubMed searches** using different query angles. A single
query rarely captures the full scope of a topic. Example for HIV drugs:

```
Query A: "HIV antiretroviral treatment Clinical Trial[Publication Type]"
Query B: "HIV prevention PrEP pre-exposure prophylaxis drug"
Query C: "HIV drug resistance OR immune reconstitution randomized"
```

For each search:
- Set `date_from` and `date_to` using exact window dates (format: YYYY/MM/DD)
- Set `datetype: pdat` (publication date — not entry date)
- Sort by `pub_date` descending
- Retrieve 10–15 results per query

**The date filter is the single most important safeguard. Never omit it,
never approximate it. Compute it from today's actual date.**

### If results are sparse (fewer than 3–4 articles)

Apply the following fallback cascade in order:
1. **Broaden query terms** — remove the most specific modifier (e.g. drop drug
   name, keep condition)
2. **Extend the window** — add 30 days and inform the user
3. **Try MeSH terms** — use controlled vocabulary if free-text is underperforming
4. **Alert the user** — if the extended search still returns < 3 articles, report
   this explicitly: "PubMed returned limited results for [topic] in this window.
   Here is what was found; recommend broadening the scope or extending to [date]."

Do not silently pad with older articles to meet a target count.

---

## Step 3 — Fetch article metadata

Take the union of all PMIDs across queries (deduplicate). Prioritise the top
15–20 PMIDs for metadata fetch using this triage order:

1. **Recency** — most recent `pdat` first
2. **Article type** — prefer RCTs, systematic reviews, and meta-analyses
3. **Journal impact** — prefer top-tier journals when recency/type are equal
4. **Abstract keyword match** — skim the search-result abstract snippet for
   direct relevance to the user's topic before fetching full metadata

Use `get_article_metadata` on the selected PMIDs. For each article confirm:
- `publication_date.year`, `.month`, `.day`
- `article_types` (needed for quality tier assignment)
- `abstract` (needed for the summary)
- `doi` (needed for deduplication)
- `journal.title`

Discard any article where the publication date falls outside the window, even
if PubMed returned it (`edat` bleed can occur with date-filtered searches).

---

## Step 4 — WebSearch for indexing-lagged journals

Run **targeted WebSearch queries** scoped to high-impact journals likely to
have recent articles not yet indexed in PubMed:

```
"[topic] [NEJM OR 'New England Journal'] [year]"
"[topic] Lancet [year] published"
"[topic] JAMA [year] trial OR study"
"[topic] 'Nature Medicine' [year]"
"[topic] Science [year]"
"[topic] BMJ [year]"
"[topic] 'Annals of Internal Medicine' [year]"
```

Use `allowed_domains` to constrain to authoritative sources:
```
["pubmed.ncbi.nlm.nih.gov", "nejm.org", "thelancet.com", "jamanetwork.com",
"nature.com", "science.org", "bmj.com", "acpjournals.org", "cell.com",
"journals.lww.com"]
```

### Date extraction from WebSearch results

For each WebSearch result, apply this cascade:

1. **Snippet states a date explicitly** → use it, note as "snippet-verified"
2. **Snippet shows only year** → use `web_fetch` on the article URL to find
   the exact publication date (look for "Published:", "Published online:", or
   schema.org `datePublished` metadata in the page)
3. **web_fetch also yields no date** → **exclude the article**; do not use
   DOI year, URL year, or any inferred date as a substitute
4. **Article is paywalled and date cannot be extracted** → note as
   "date unverified, excluded" in your working notes

---

## Step 4b — Preprint search (optional but recommended)

For topics where cutting-edge data matters (HIV prevention, vaccines, novel
therapies, implementation science), run a targeted WebSearch on preprint servers:

```
"[topic] medRxiv [year]"
"[topic] bioRxiv [year]"
```

`allowed_domains: ["medrxiv.org", "biorxiv.org"]`

Preprints must be clearly flagged in the report:
`| **Source** | medRxiv preprint — not peer-reviewed |`

Include preprints **only** in Tier 5 (or a separate "Preprints" section) unless
the user explicitly requests them at higher prominence.

---

## Step 5 — Deduplication and date verification

Build a master list combining Zotero, PubMed, and WebSearch/preprint results.

**Deduplication by DOI:** If sources share a DOI, keep in this priority:
PubMed entry > WebSearch entry > Zotero-only entry (Zotero still flagged).

**Date verification rule — apply to every article before inclusion:**

| Source | Verified if... |
|--------|----------------|
| PubMed | `publication_date` field present and within window |
| WebSearch | Publication date explicitly stated in snippet or article page via `web_fetch` |
| WebSearch | DOI year alone — **NOT sufficient** |
| Preprint | Posted date on medRxiv/bioRxiv page — use `web_fetch` to confirm |

If an explicit publication date within the target window cannot be confirmed:
**exclude the article.** Note it as "date unverified, excluded."

---

## Step 6 — Quality tier ranking

Rank every confirmed article by evidence tier. Use this to prioritise
selection when candidates exceed the target count.

| Tier | Article types | Examples |
|------|--------------|---------|
| **1 — Synthesis** | Cochrane review, systematic review, meta-analysis | Cochrane Database, PROSPERO-registered SR |
| **2 — Experimental** | RCT, Phase 2/3 clinical trial, crossover trial | NEJM trial, Lancet RCT |
| **3 — Observational** | Prospective cohort, target trial emulation, registry study | Ann Epidemiol, JAIDS cohort |
| **4 — Descriptive** | Case series, cross-sectional survey, pharmacokinetics study | Single-centre case series |
| **5 — Expert opinion / Preprint** | Commentary, editorial, perspective, narrative review, preprint | NEJM editorial, medRxiv |

Selection logic:
- Fill from Tier 1 first, then Tier 2, and so on
- Within the same tier, prefer higher-impact journals
- Aim for balance across the user's requested categories
- Include Tier 5 only if it provides essential context not covered by higher tiers

---

## Step 7 — Write the structured report

Produce a Markdown report. Use this exact template for each article entry:

```markdown
## [N]. [Full Article Title]

| Field | Detail |
|---|---|
| **Published** | [Day Month Year — exact, verified] |
| **Journal** | *[Journal name]*, Vol. X, Issue Y |
| **Study type** | [Tier N — e.g. Tier 2: Randomised Controlled Trial] |
| **Category** | [Category label — see system below] |
| **PMID** | [41XXXXXX](https://pubmed.ncbi.nlm.nih.gov/41XXXXXX/) |
| **DOI** | [10.xxxx/xxxxx](https://doi.org/10.xxxx/xxxxx) |

**Summary:** [3–5 sentences. Lead with the study design and population.
Include the key quantitative result (effect size, p-value, NNT, etc.).
State the clinical or public health implication. Flag major limitations
if relevant.]

---
```

For WebSearch-only articles (no PMID):
`| **Source** | WebSearch-verified, not yet indexed in PubMed |`

For Zotero-curated articles:
`| **Source** | Zotero library (user-curated) + PubMed-verified |`

For preprints:
`| **Source** | medRxiv preprint — not peer-reviewed |`

### Category label system

Use consistent emoji-prefixed labels. Assign one primary category per article;
add a second only if the article is genuinely dual-purpose.

| Label | Use for |
|-------|---------|
| 🔵 Treatment | ART, curative/suppressive therapy, therapeutic interventions |
| 🟢 Prevention | PrEP, PEP, vaccines, behavioural prevention, harm reduction |
| 🔴 Diagnostics | Testing strategies, biomarkers, diagnostic accuracy |
| 🟡 Implementation | Delivery models, adherence, health systems, scale-up |
| 🟣 Pharmacology | PK/PD, drug interactions, dosing, formulations |
| ⚪ Epidemiology | Burden of disease, incidence, surveillance, modelling |
| 🟤 Basic science | Mechanism of action, virology, immunology, in vitro/animal |
| 📄 Review/Opinion | Systematic reviews, meta-analyses, editorials, guidelines |

---

## Report header and footer

**Header:**
```markdown
# [Topic] Evidence Digest
### [Category labels] — Last [N] Days
**Compiled:** [Date] | **Coverage window:** [Start] – [End]

> **Scope & Methodology:** Retrieved via multi-source protocol —
> Zotero personal library, PubMed MCP connector (date-filtered `pdat`
> [window]), WebSearch for NEJM, Lancet, JAMA, Nature Medicine, BMJ,
> Science[, and medRxiv/bioRxiv preprints if applicable].
> All publication dates verified against PubMed metadata or journal
> records before inclusion. DOI year alone was not accepted as date evidence.
```

**Footer:**
```markdown
## Key Themes
[3–4 cross-cutting observations drawn from the full article set]

---
*Sources: PubMed — [PMID links]. WebSearch-supplemented and preprint
articles noted inline. All dates verified. For professional reference
only; does not constitute clinical guidance.*
```

---

## Step 8 — Output format

**Default:** Inline Markdown in the conversation, suitable for reference and copying.

**Formal DOCX report:** If the user says "export", "send to team", "formal
report", "download", or "Word document" — trigger the `docx` skill and apply
`antonio-style`. Pass the full Markdown report as the source content.
File naming convention: `[YYYY-MM-DD]_Evidence-Digest_[Topic-slug].docx`

---

## Common mistakes to avoid

**DOI year ≠ publication date.** A DOI containing `(26)` means the journal
volume year is 2026. It does not mean the article was published within your
date window. Always get an explicit date.

**PubMed `edat` bleed.** Even with a date filter, PubMed occasionally returns
articles whose entry date (`edat`) falls in range but whose publication date
(`pdat`) does not. Always verify `publication_date` in the metadata.

**WebSearch snippets can be misleading.** A result snippet may show "2026" in
a URL or citation without specifying month and day. Use `web_fetch` before
excluding — but if the page still yields no date, exclude.

**High citation count ≠ recent publication.** Landmark older papers are often
surfaced by relevance-sorted searches. Sort by `pub_date` and verify dates.

**Silent padding.** Do not include older articles to meet a target count.
If results are sparse, apply the fallback cascade in Step 2 and report to
the user.

**Preprints without flags.** Never present a preprint as peer-reviewed. Always
label clearly and place in Tier 5.

---

## Attribution

Per PubMed MCP connector terms: always attribute results to PubMed and include
DOI links when presenting PubMed-sourced articles.
