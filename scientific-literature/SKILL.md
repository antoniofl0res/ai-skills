---
name: scientific-literature
description: >
  Orchestrates multi-database scientific literature search across five complementary MCP servers:
  scientific-databases (Crossref, Europe PMC, OpenAlex, Semantic Scholar), PubMed MCP (native NCBI
  retrieval), and bioRxiv/medRxiv MCP (preprints). Use this skill whenever the user wants to find
  papers, search for research, look up a DOI or PMID, check citations, map a research topic, get an
  author's publication profile, do a systematic or scoping review, retrieve full text of an
  open-access article, or surface recent preprints. Trigger even when the request is casual ("find me
  some papers on X", "who cites this paper?", "is there evidence for Y?", "any preprints on Z?") —
  don't wait for the user to say "systematic review" or name a specific database. Also trigger when
  the user pastes a DOI or PMID and wants metadata, or asks which databases have coverage on a topic.
---

# Scientific Literature Search

You have access to **three MCP servers** spanning six databases plus preprint servers. Your job is to
route queries intelligently, call the right tools (sometimes more than one in parallel), and return
results in a clean, citation-ready format.

---

## Your tools

### scientific-databases (Crossref · Europe PMC · OpenAlex · Semantic Scholar)

| Tool | Database | Best for |
|---|---|---|
| `search_crossref` | Crossref | DOI lookup, citation counts, publisher/funder metadata, OA link discovery |
| `fetch_doi_metadata` | Crossref | Full record for a known DOI — abstract, funders, all authors |
| `search_europe_pmc` | Europe PMC | Broad biomedical search with structured field queries; identifies OA full text |
| `fetch_europe_pmc_fulltext` | Europe PMC | Full-text XML for open-access articles when you have a PMCID |
| `search_openalex` | OpenAlex | 250M+ works, concept/topic mapping, OA status, author affiliations |
| `get_openalex_author` | OpenAlex | Author profile: affiliation history, citation count, top concepts |
| `search_semantic_scholar` | Semantic Scholar | TL;DR summaries, influential-citation flag, open PDF links |
| `get_paper_citations` | Semantic Scholar | "Who cited this paper?" — forward citation tracking |

### PubMed MCP (native NCBI)

| Tool | Best for |
|---|---|
| `PubMed:search_articles` | Primary PubMed search with full Boolean, MeSH, date-range, and sort control |
| `PubMed:get_article_metadata` | Rich metadata by PMID — abstract, MeSH terms, grant info, identifiers |
| `PubMed:get_full_text_article` | Full text via PMC when a PMCID is available |
| `PubMed:find_related_articles` | "More like this" using word-weighted title/abstract/MeSH similarity |
| `PubMed:convert_article_ids` | Convert between PMID ↔ PMCID ↔ DOI |
| `PubMed:get_copyright_status` | License/OA status for a batch of PMIDs |

**When to prefer PubMed MCP over Europe PMC:**
- User supplies a PMID directly.
- Query benefits from native MeSH controlled vocabulary or Publication Type filters (e.g. `Clinical Trial[pt]`, `Systematic Review[pt]`).
- You need grant/funding data, MeSH term lists, or want to check which PMIDs have full text in PMC before fetching.
- Date-sensitive retrieval where `date_from`/`date_to` precision matters (format: `YYYY/MM/DD`).
- "More like this" discovery from seed PMIDs.

### bioRxiv / medRxiv MCP (preprints)

| Tool | Best for |
|---|---|
| `bioRxiv:search_preprints` | Browse preprints by date range or recent window; filter by category |
| `bioRxiv:get_preprint` | Full metadata for a specific preprint DOI — abstract, authors, PDF URL, funding |
| `bioRxiv:search_published_preprints` | Find preprints that have subsequently been published in a peer-reviewed journal |
| `bioRxiv:search_by_funder` | Track preprints from a specific funding body by ROR ID (data from 2025-04-10 onward) |
| `bioRxiv:get_categories` | List all 27 bioRxiv category names (call once if you're unsure of category spelling) |

**Critical limitation:** `bioRxiv:search_preprints` does **not** support keyword/text search — it filters
by date range and category only. To find preprints on a topic, identify the correct category first,
then browse by date. For medRxiv (clinical/epidemiological sciences), set `server="medrxiv"`.

---

## Routing guide

### Keyword / topic search
→ **Always include PubMed MCP** (`PubMed:search_articles`) — it is the gold standard for indexed
  biomedical literature with MeSH precision.  
→ Run `search_europe_pmc` + `search_openalex` in parallel for breadth.  
→ Add `search_semantic_scholar` for TL;DR summaries or AI/ML-adjacent topics.  
→ Add `search_crossref` if citation counts or funder metadata are needed.  
→ Add `bioRxiv:search_preprints` (server="medrxiv" for clinical topics) to catch
  pre-publication findings, especially on fast-moving topics (antiretrovirals, vaccine trials,
  outbreak epidemiology). Flag all preprints clearly as **[PREPRINT - not peer reviewed]**.

### User supplies a PMID
→ `PubMed:get_article_metadata` for the full record.  
→ Follow with `PubMed:convert_article_ids` to get PMCID, then `PubMed:get_full_text_article`
  if full text is requested.

### User supplies a DOI
→ `fetch_doi_metadata` (Crossref) for full metadata.  
→ If the DOI starts with `10.1101/`, it's a bioRxiv/medRxiv preprint — use `bioRxiv:get_preprint`.  
→ Optionally follow with `get_paper_citations` (Semantic Scholar) for forward citation tracking.

### User asks "who cites this?"
→ `get_paper_citations` (Semantic Scholar) with `DOI:10.xxxx/xxxxx`.

### User wants an author's profile
→ `get_openalex_author` for affiliations, works count, total citations, top concepts.

### User wants to read full text
→ From a PMID: `PubMed:convert_article_ids` to get PMCID → `PubMed:get_full_text_article`.  
→ From a PMCID directly: `PubMed:get_full_text_article` or `fetch_europe_pmc_fulltext` (either works).  
→ For a preprint DOI: `bioRxiv:get_preprint` returns the PDF URL directly.

### Systematic or scoping review
→ Run `PubMed:search_articles` + `search_europe_pmc` + `search_openalex` + `search_semantic_scholar` in parallel.  
→ Add `bioRxiv:search_preprints` (server="medrxiv") to capture recent preprints in the relevant category.  
→ Deduplicate by DOI before presenting results.  
→ Offer to refine by year, OA status, publication type, or study design.

### User wants recent / emerging evidence on a fast-moving topic
→ Run `PubMed:search_articles` with `sort="pub_date"` + `bioRxiv:search_preprints` with
  `recent_days=60` (server="medrxiv" for clinical topics) in parallel.  
→ Surface preprints clearly labelled, noting if a published version exists via
  `bioRxiv:search_published_preprints`.

### MSF, SAMU, neglected tropical diseases, humanitarian medicine, outbreak response
→ These are high-priority domains — be thorough. Run PubMed + Europe PMC + medRxiv minimum.
→ Prioritise OA papers and preprints; surface PDF links where available.

---

## Output format

Return results as a numbered reference list. For each paper:

```
[N] Authors (Year). Title. *Journal* [or *Preprint: medRxiv/bioRxiv*]. DOI/URL.
    → [1–2 sentence note: relevance, citation count, OA status, TL;DR, or preprint status]
```

- **Deduplicate** across databases (match on DOI first, then title+year).
- Flag open-access papers with **[OA]**.
- Flag preprints prominently: **[PREPRINT — not peer reviewed]**. If a published version exists, note the journal DOI.
- If a paper has a very high citation count (>500) or influential-citation flag from Semantic Scholar, note it.
- At the end, add a one-line summary: results count, databases queried, and any notable gaps.

---

## Practical tips

- **Parallelise freely** — PubMed + OpenAlex + Semantic Scholar + medRxiv can all fire at once.
- **PubMed Boolean is powerful**: use `AND`, `OR`, `NOT`, field tags (`[Title]`, `[MeSH Terms]`,
  `[Author]`, `[Journal]`), and Publication Type filters (`Clinical Trial[pt]`,
  `Systematic Review[pt]`, `Meta-Analysis[pt]`).
- **MeSH terms** feed directly into `PubMed:search_articles` — prefer them for clinical topics over
  free text when precision matters.
- **Date filtering**: PubMed uses `YYYY/MM/DD`; bioRxiv uses `YYYY-MM-DD`; OpenAlex uses
  `publication_year:YYYY-YYYY` in the filter string.
- **OpenAlex filter string**: `publication_year:2020-2026,open_access.is_oa:true` is a powerful
  combined filter for recent OA papers.
- **Europe PMC field tags**: `AUTH:surname`, `JOURNAL:"lancet"`, `DISEASE:"histoplasmosis"`.
- **bioRxiv category for clinical/HIV/epidemiology work**: use `server="medrxiv"` — this covers
  epidemiology, clinical trials, and public health preprints.
- **Preprint caution**: always label preprints clearly; mention if a published version was found or
  if it is still under review.
- If a search returns zero results, widen the query (drop field terms, try synonyms) and retry once.
- Semantic Scholar's `tldr` field is machine-generated — include it when available for quick triage.
