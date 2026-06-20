---
name: zotero-search
description: >
  Search the user's Zotero library for academic literature using the Zotero
  MCP connector. ALWAYS use this skill when the user mentions a research topic,
  asks for citations or references, wants to find papers, or says anything like
  "search Zotero", "do I have papers on", "find me literature on", "what do I
  have on", or "look in my library". Trigger even when the user only implies
  they need academic sources — e.g. "I'm writing a review on X", "I need to
  cite something about Y", or "what does the literature say about Z". Returns
  full metadata, abstracts, DOIs, journal details, and tags directly from
  Zotero. If no local match is found, offers to fall back to PubMed.
  Citation style: Vancouver.
---

# Zotero Literature Search Skill

Search the user's Zotero library via the **Zotero MCP connector** — no file
scanning required. The connector provides full metadata, abstracts, DOIs,
journal info, collections, and tags directly from Zotero's database.

---

## Available Zotero MCP Tools

| Tool | Best for |
|------|----------|
| `zotero_search_items` | Keyword search across title, author, year (default) or full text |
| `zotero_semantic_search` | Concept/meaning-based search (when keywords fail) |
| `zotero_search_by_tag` | Searching by Zotero tags |
| `zotero_get_item_metadata` | Fetching full details for a specific item key |
| `zotero_get_collections` | Browsing the library's collection structure |
| `zotero_get_collection_items` | All papers in a specific collection |
| `zotero_get_recent` | Browsing recently added papers |
| `zotero_advanced_search` | Multi-field queries (date range, item type, etc.) |
| `zotero_search_notes` | Searching the user's reading notes |

---

## Step-by-Step Workflow

### Step 1 — Understand the query

Parse the user's request to extract:
- **Core topic keywords** (e.g. "tuberculous meningitis", "Bayesian diagnosis")
- **Filters** if mentioned: date range, author, tag, collection, item type
- **Intent**: Are they looking for a specific paper, or exploring a topic?

If ambiguous, ask one clarifying question before proceeding.

---

### Step 2 — Run a layered search strategy

Use multiple search approaches and merge results. Do them in this order,
stopping early if you have ≥5 strong matches:

#### 2a. Keyword search (always run first)

```
zotero_search_items(
  query = "<core keywords>",
  qmode = "titleCreatorYear",   # fast, precise
  limit = 10
)
```

If results are sparse or the topic is conceptual, also run:

```
zotero_search_items(
  query = "<core keywords>",
  qmode = "everything",         # searches abstracts and notes too
  limit = 10
)
```

#### 2b. Semantic search (run when keyword search returns < 3 results)

```
zotero_semantic_search(
  query = "<natural-language description of the topic>",
  limit = 10
)
```

> Note: semantic search uses AI embeddings and may return conceptually related
> papers even when exact keywords don't match. If it returns
> "No semantically similar items found", skip and note this.

#### 2c. Tag search (run if user mentions a tag or topic maps to a likely tag)

```
zotero_search_by_tag(tag = ["<tag>"], limit = 10)
```

#### 2d. Advanced search (for filtered queries)

Use `zotero_advanced_search` when the user specifies:
- A date range ("papers from 2020–2024")
- A specific author
- An item type ("only journal articles")

```
zotero_advanced_search(
  conditions = [
    {"field": "title", "operator": "contains", "value": "<keyword>"},
    {"field": "date", "operator": "isAfter", "value": "2020"}
  ],
  join_mode = "all",
  limit = 20
)
```

---

### Step 3 — Deduplicate and rank results

Merge results from all searches. Deduplicate by `item_key`. Rank by:
1. Exact title/keyword match → highest priority
2. Abstract/full-text match
3. Semantic similarity match

If >10 results remain, keep the top 10 by relevance.

---

### Step 4 — Fetch full metadata for top results

The search tools return a summary. For the top results (up to 10), call:

```
zotero_get_item_metadata(item_key = "<key>", include_abstract = true)
```

This returns: full author list, journal, volume, issue, pages, DOI, URL,
abstract, tags, and collection membership.

> Only call this for papers you will actually show the user — it's one call
> per paper.

---

### Step 5 — Format results in Vancouver style

Vancouver citation format:
```
[N] Last FM, Last2 FM. Title of paper. Journal. Year;Volume(Issue):Pages.
```

For each paper, present:

```
────────────────────────────────────────
[N] Author(s). Title. Journal. Year;Vol(Issue):Pages.
DOI: https://doi.org/...
Tags: tag1, tag2

Abstract:
<First 150–200 words of abstract, or "Abstract not available">
────────────────────────────────────────
```

If DOI/URL is available, always include it — it lets the user jump straight
to the paper.

If journal/volume info is missing from metadata, note "journal details
unavailable" rather than omitting the citation.

---

### Step 6 — Handle no matches → PubMed fallback

If zero results are found after all search strategies, do NOT silently fail.
Say:

> "I didn't find any papers matching [topic] in your Zotero library.
> Would you like me to search PubMed for relevant literature instead?"

Wait for the user to confirm before searching PubMed.

If yes, use the PubMed MCP tool to search:
- Query: topic keywords + MeSH terms if applicable
- Max results: 10

Return PubMed results in the same Vancouver format (citation + abstract
snippet). Offer to help the user save references for follow-up.

If the PubMed MCP is unavailable, offer this direct URL:
`https://pubmed.ncbi.nlm.nih.gov/?term=<url-encoded-topic>`

---

## Output Format Summary

```
Searching your Zotero library for: "[topic]"
Found N matching paper(s).

────────────────────────────────────────
[1] Dong THK, Donovan J, Ngoc NM, et al. A novel diagnostic model for
tuberculous meningitis using Bayesian latent class analysis.
BMC Infect Dis. 2024;24(1):163.
DOI: https://doi.org/10.1186/s12879-024-08992-z
Tags: tuberculosis, meningitis, diagnostics

Abstract:
Diagnosis of tuberculous meningitis (TBM) is hampered by the lack of a gold
standard. We developed a diagnostic model using latent class analysis...
────────────────────────────────────────
```

---

## File Output Format

Default to `.txt` for all standard outputs (search results, summaries,
PubMed fallback). Only upgrade if it genuinely helps:

| Situation | Format |
|-----------|--------|
| >10 papers to compare across fields | `.csv` |
| User wants a formatted report to share/print | `.md` or `.docx` |
| User explicitly asks for "a table" | `.csv` |

Stick with `.txt` when in doubt — it's fast and readable everywhere.

---

## Edge Cases

| Situation | Action |
|-----------|--------|
| `zotero_search_items` returns nothing | Try `qmode = "everything"`, then `zotero_semantic_search` |
| Semantic search returns "No items found" | Note this, proceed with keyword results only |
| Metadata missing journal/volume | Show what is available; don't omit the citation |
| >10 matches | Show top 10 by relevance; tell user total count |
| User asks about a collection | Use `zotero_get_collections` then `zotero_get_collection_items` |
| User asks about recently added papers | Use `zotero_get_recent` |
| User asks about their notes on a paper | Use `zotero_search_notes` |
| PubMed MCP unavailable | Offer direct PubMed URL |

---

## Dependencies

- Zotero MCP connector (required) — must be active in the current session
- PubMed MCP server (for fallback) — https://pubmed.mcp.claude.com/mcp
