---
name: deep-websearch
description: >
  Use this skill for any non-trivial web research — when the answer is not already in
  context, when the user asks to "look up", "find", "research", "search for", "what's
  the latest on", "compare", or "fact-check", or when a single WebSearch call would be
  shallow. Covers any domain: technical, scientific, medical, news, products, people,
  official/regulatory, historical. Combines query decomposition, multi-angle
  triangulation, source routing by topic, full-page reading (not just snippets),
  explicit verification before citing, and a contradiction-handling step. Always ends
  with a Sources list. Distinct from a single WebSearch call: this is the multi-pass,
  verify-before-cite protocol to reach high-confidence answers.
---

# Deep WebSearch: multi-pass, verify-before-cite research protocol

A standardised approach for reaching **high-confidence answers** to non-trivial
questions. The defining features that separate this from a one-shot search:

1. **Query decomposition** — break the question into sub-questions; one query almost never captures the whole answer.
2. **Multi-angle triangulation** — 3–5 queries per sub-question, with different vocabulary and framing.
3. **Source routing** — match the query type to authoritative domains via `allowed_domains`.
4. **Read the page, not the snippet** — snippets are shallow; use `webReader` / page fetch for anything substantive.
5. **Verify before citing** — every factual claim cross-checked against a second independent source (or one primary authoritative source) before inclusion.
6. **Iterate** — search → read → find gaps → search again. One round rarely suffices for hard questions.
7. **Surface contradictions** — when sources disagree, say so; never silently pick one.

---

## Step 0 — Classify the query

Before searching, decide what kind of question this is. Classification routes source selection and verification strictness.

| Type | Telltale signals | Primary sources | Recency matters? |
|------|------------------|-----------------|------------------|
| **Factual lookup** | "what is", "who wrote", "when did" | Encyclopedic, official, primary docs | Low |
| **Technical / how-to** | "how do I", "why does", API/CLI/code question | Official docs, RFCs/specs, source code, reputable Q&A | Medium |
| **Recent / current** | "latest", "this week", "what's new", date-sensitive | News, official announcements, release notes, changelogs | **Critical** |
| **Comparative** | "X vs Y", "best", "alternatives to" | Reviews, benchmarks, official comparison pages, multiple primary sources | Medium |
| **Academic / scientific** | studies, evidence, mechanism, efficacy | PubMed, Semantic Scholar, arXiv, Google Scholar, DOI-linked papers | Medium |
| **Statistical / data** | "how many", rates, prices, market share | Official statistics agencies, SEC/financial filings, primary datasets | **Critical** |
| **Opinion / subjective** | "should I", "is it worth", recommendations | Mix of expert commentary, community discussion, primary sources | Low |
| **Person / entity** | biography, company info, contact | Official site, primary records, reputable secondary profiles | Low |

**Output of Step 0:** a one-line classification, the recency flag, and an initial source-domain list. This is internal — do not print unless asked.

---

## Step 1 — Decompose into sub-questions

Restate the user's question as 1–4 concrete sub-questions. Most "hard" questions are hard only because they bundle several.

- *"Is Rust good for web backends?"* → (a) What are Rust's web ecosystem options? (b) What are typical performance/productivity tradeoffs vs Node/Go? (c) What do practitioners report in 2025–2026?
- *"What's the latest on HIV PrEP?"* → (a) Recently approved / late-stage PrEP agents? (b) Real-world implementation findings? (c) Resistance / safety signals?

If decomposition feels forced (single, narrow factual lookup), collapse back to a single sub-question — don't over-engineer.

---

## Step 2 — Multi-angle search queries (run in parallel)

For each sub-question, run **2–4 parallel WebSearch queries** with different framing and vocabulary. Synonyms, different register (technical vs lay), abbreviation expansions, and "site:" or domain hints all count as different angles.

Example angles for one sub-question:
```
"Rust web framework performance benchmark 2026"
"actix axum rocket comparison production"
"Rust backend vs Go throughput latency"
site:reddit.com "rust web" experience 2025
```

**Why multiple angles:** search ranking rewards one phrasing and buries another; the second query often surfaces the source that resolves the question.

### Source routing — use `allowed_domains` to constrain authority

Pick the domain allow-list from the query type (Step 0). Common authoritative bundles:

- **Official docs / specs**: `developer.mozilla.org`, `w3.org`, `rfc-editor.org`, `ietf.org`, `ecma-international.org`, `kotlinlang.org`, `rust-lang.org`, `go.dev`, `nodejs.org`, `python.org`, `microsoft.com`, `oracle.com` (Java)
- **Code / packages**: `github.com`, `gitlab.com`, `npmjs.com`, `crates.io`, `pypi.org`, `pkg.go.dev`, `mvnrepository.com`, `stackoverflow.com`
- **Academic / scientific**: `pubmed.ncbi.nlm.nih.gov`, `semanticscholar.org`, `arxiv.org`, `biorxiv.org`, `medrxiv.org`, `doi.org`, `nature.com`, `science.org`, `sciencedirect.com`, `jamanetwork.com`, `nejm.org`, `thelancet.com`, `bmj.com`, `scholar.google.com`
- **Official / government / regulatory**: `gov.uk`, `europa.eu`, `.gov` sites, `who.int`, `cdc.gov`, `fda.gov`, `ema.europa.eu`, `nist.gov`, `bis.org`, `imf.org`, `oecd.org`, `worldbank.org`
- **Statistics / data**: `census.gov`, `ons.gov.uk`, `ec.europa.eu/eurostat`, `statista.com`, `ourworldindata.org`, `oecd.org`, primary dataset landing pages
- **News (reputable)**: `reuters.com`, `apnews.com`, `bbc.com`, `ft.com`, `bloomberg.com`, `nytimes.com`, `washingtonpost.com`, `economist.com`, `nature.com/news`, `arstechnica.com`, `theverge.com`
- **Product / company**: the company's own `*.com` official site, support domain, and status page first; then reputable reviews.

Don't over-constrain. A reasonable default is **no `allowed_domains` for the first round** (to discover the lay of the land), then **a constrained second round** once the authoritative domains are obvious.

---

## Step 3 — Read the pages, not the snippets

For any non-trivial sub-question, fetch the **top 2–4 most promising results** with `webReader` (or page fetch) and read the body. Snippets answer trivia; they do not answer *why*, *how*, or *compared to what*.

Reading rules:
- Extract the **specific claim** plus the **evidence** the page offers for it (data, citation, primary source link).
- Note the **publication / last-updated date** of the page itself, in passing — you'll need it for Step 5.
- Trace one level: if the page cites a primary source (paper, spec, official statement, dataset) for a load-bearing claim, follow that link rather than trusting the summary.

**Don't read everything.** Triage hard: most queries are answered by 2–4 well-chosen pages, not 15.

---

## Step 4 — Identify gaps and iterate

After the first search+read pass, ask: **what's still unanswered?** Common gaps:
- A sub-question never got a clean answer
- Two sources contradict each other
- The result is suspiciously old for a recency-sensitive query
- A claim is unsourced or comes from a single weak source

For each gap, run a **targeted second-round query** — narrower, alternative vocabulary, or scoped to a specific authoritative domain. Two rounds is typical for substantive questions; three is fine for genuinely contested or obscure ones. Stop when the marginal gain per round is small.

---

## Step 5 — Verify before citing (the gate that prevents fabrication)

Every factual claim entering the final answer must clear one of these bars:

| Strength | What it means |
|----------|---------------|
| **Primary authoritative** | The official spec, the dataset itself, the paper's own abstract/results, the company's own announcement. Single source is acceptable if primary. |
| **Two independent sources** | Two non-derivative sources (i.e. not both citing the same original). Together they count as verified. |
| **Aggregation of reputable reporting** | ≥3 reputable outlets reporting the same fact independently (acceptable for news/claims where no single primary source exists). |

**What fails the gate:**
- A single non-primary source for a load-bearing claim → search for a second, or downgrade to "reported by X, not independently verified".
- A date-sensitive claim with no visible date → either find the date or flag recency unverified.
- A claim that only appears in low-quality or SEO-content sources → discard, search again, or omit.

### Recency check (for date-sensitive queries)

For any "latest", "current", or time-bounded claim:
1. Note the **publication or last-updated date** on the source.
2. If the date isn't on the page, try `webReader` on the article URL looking for "Published", "Updated", schema.org `datePublished` / `dateModified`.
3. **DOI year, URL year, or copyright year are NOT publication dates.** Don't accept them as recency evidence.
4. If no real date can be established, exclude or flag as "date unverified".

### No fabrication, ever

- Never invent URLs, citations, version numbers, dates, statistics, or quotes.
- If you're unsure of an exact figure or quote, paraphrase and flag uncertainty — don't approximate and present as exact.
- URLs in the Sources list must be pages you actually fetched or that appeared verbatim in a WebSearch result. If you're unsure a URL exists, omit it.

---

## Step 6 — Handle contradictions explicitly

When sources disagree, do not silently pick one. Options, in order of preference:
1. **Find the resolution** — often a newer source, an erratum, or a primary dataset settles it.
2. **Report the range / both positions** — "Source A reports X; Source B reports Y. The discrepancy appears to come from <difference in method/scope/date>."
3. **Flag unresolved** — "Sources disagree and I could not resolve it; the credible range is X–Y."

Never average contradictory figures into a misleading single number.

---

## Step 7 — Write the structured answer

Adapt depth to the question. For trivial lookups, one paragraph is right. For substantive research, use this skeleton:

```markdown
## [Question restated as a heading]

**Bottom line:** [2–3 sentence direct answer up front. Lead with the conclusion, not the process.]

### [Sub-question 1]
[Answer paragraph, citing inline as (Source N).]

### [Sub-question 2]
[...]

### What's uncertain or contested
[Any gaps, contradictions, or recency caveats the user should know.]

---
**Sources:**
1. [Title — Site/domain — Date if known](URL)
2. ...
```

Quality bar for the writeup:
- **Direct first.** The user wants the answer, not a tour of the search. Put the conclusion above the reasoning.
- **Cite inline.** `(Source 2)` next to the claim it supports; full link in the Sources list.
- **Quote when paraphrase is risky.** Exact figures, named-party statements, technical specifications — quote verbatim in quotes.
- **Flag uncertainty honestly.** "Verified" / "reported by one source" / "date unverified" / "sources disagree" — these labels are more useful than false confidence.
- **End with Sources.** Always. A research answer without verifiable sources is incomplete.

---

## Step 8 — Output format

**Default:** Inline Markdown in the conversation.

**Formal export:** If the user says "export", "report", "document", "send", or "Word" — trigger the `docx` skill and apply `antonio-style`. Pass the full Markdown answer as the source content.

---

## Common mistakes to avoid

**One query and done.** The single most common failure. Hard questions need 3–5 angles; the resolving source is often the third query.

**Trusting the snippet.** Snippets answer trivia and mislead on substance. Read the page.

**Citing a summary that cites another summary.** Trace to the primary source for load-bearing claims; secondary aggregators propagate and amplify errors.

**Treating recency as optional.** For "latest" / "current" queries, an undated source is worse than no source. Find the date or exclude.

**Silently resolving contradictions.** Two sources, two numbers, and you pick one — the user can't see the choice. Surface it.

**Inventing URLs or citations to fill a gap.** Never. Omit, flag, or search again.

**Over-citing to look thorough.** Five strong sources beats fifteen redundant ones. Triage.

**Answering more than was asked.** Stay scoped to the sub-questions. Scope creep is detected as waffle.

---

## Attribution and scope

- Cite every source used; include the URL and (where known) the date.
- Mark opinion, rumour, or unverified reporting as such.
- This skill handles public web sources only. For the user's personal library of curated papers, use `zotero-search`. For biomedical literature with date-verified PubMed metadata specifically, the `pubmed-websearch-retrieval` skill remains the dedicated tool.
