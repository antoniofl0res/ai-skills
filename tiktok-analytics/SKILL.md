---
name: tiktok-analytics
description: End-to-end analysis of any public TikTok account: extract the complete video inventory with engagement metrics via browser capture of TikTok's own signed API, compute engagement rates, view velocities, duration/format and content-pillar performance, benchmark against platform averages, and produce a report separating factual findings from labeled predictions. Use whenever the user mentions TikTok analytics, auditing or analyzing a TikTok profile, account or creator, TikTok views/likes/followers/engagement performance, why videos underperform, what to post more of, growth predictions, or TikTok content strategy — even if they only paste a @handle or profile URL.
---

# TikTok Analytics

A field-proven pipeline for auditing any public TikTok account. Five stages:

```
EXTRACT  →  ANALYZE  →  BENCHMARK  →  REPORT  →  VERIFY
```

Read `references/extraction.md` before extracting data (stage 1) and `references/analysis.md` before computing metrics or writing the report (stages 2-5). Both encode failures already hit in production; skipping them rediscovers those failures the hard way.

## Scope and ground rules

- Works for public accounts. Private accounts, and "liked" playlists on any account, are not extractable without the owner's session; say so and stop rather than guessing.
- Everything is a single-point snapshot. Engagement counts on videos posted within the last 48 hours are still accumulating; every report must state the snapshot timestamp and this caveat.
- Never fabricate or estimate a metric. If a number cannot be captured, it is reported as unavailable, never approximated. If the whole extraction fails, deliver a degraded report (profile-header stats only) with limitations stated, not a fabricated inventory.
- Respect the target: read-only interaction in the browser. The interceptor described below clones responses; it never modifies or replays requests, and it never logs in.

## Stage 1: EXTRACT

Goal: a complete, authoritative dataset — profile stats plus every video with plays, likes, comments, shares, saves, duration, post time, description, audio.

1. Cheap first pass: fetch the profile URL with WebFetch or a reader tool. This usually returns the header stats (followers, total likes, bio) or nothing. Treat it as a sanity read only; the video inventory is never available this way.
2. Browser capture (the reliable path). Requires the `browser-use:control-browser` skill in-session; if unavailable, stop after step 1 and deliver the degraded report. The full playbook with working code is in `references/extraction.md`. Summary:
   - Open the profile in a controlled browser tab. Expect obstacles: a login modal (dismiss via its Skip button), a lazy-loaded or errored video grid, and bot-detection throttling. Fixes are in the reference.
   - Read profile data from the page's embedded `__UNIVERSAL_DATA_FOR_REHYDRATION__` JSON (`webapp.user-detail` scope). This gives authoritative stats plus the internal `secUid`.
   - Do NOT call `/api/post/item_list/` directly; it returns HTTP 200 with an empty body without TikTok's request signature. Instead install a fetch/XHR interceptor in the page context, then make the page issue its own signed request (click the grid's Refresh button or reload). Parse the captured response.
3. Integrity checks before proceeding (both must pass, else re-extract):
   - Captured video count equals the profile's `videoCount` (mind `hasMore`/`cursor` pagination).
   - Sum of per-video like counts equals the profile's total-likes counter. This cross-validation caught nothing less than full dataset integrity in field use.
4. Record the snapshot timestamp from the page clock (`Date.now()`). Velocity math depends on it.

## Stage 2: ANALYZE

Goal: derived metrics that survive an independent recomputation. Full definitions, formulas and worked examples are in `references/analysis.md`. The non-negotiables:

- Compute every derived number with a script, never mental math. The median of an even-count list is the average of the two middle sorted values; mispicking the middle pair is the single most common error class in this pipeline.
- Normalize before comparing: never compare raw plays between videos of different ages; compare plays-per-hour (velocity), and flag videos under two hours old as still in distribution.
- Watch the two classic confounds: format-vs-posting-slot (a "bad time slot" may just carry weak formats) and age-vs-performance (young videos look like underperformers until velocity-normalized).
- Count by sorting, not by memory: top-N lists, zero-count lists, posting-cluster counts. Recount each against the raw table before publication; cluster counts must sum to the video total.
- Small samples get small confidence: never state High confidence on a sub-pillar with fewer than four videos, and say so explicitly.

## Stage 3: BENCHMARK

Goal: external context, honestly sourced.

- Search for current-year engagement-rate benchmarks and new-account view behavior. Expect methodology spread (by-views vs by-followers vs by-follower-band); report a range with named sources, never a single point value.
- Monetization thresholds (Creator Rewards and equivalents) and policy facts change; cite them as "reported by secondary sources; verify in-app".
- Context specific to the account's niche matters (election calendars, platform policy windows, seasonal attention). Research it; timing context often explains more than content quality.
- Follow the verification rules of the `deep-websearch` skill when gathering these.

## Stage 4: REPORT

Goal: a deliverable that separates measured fact from labeled prediction.

- Apply the `my-professional-style` skill to the output document. File naming: `[Topic]_[DocType]_[Version].[ext]`, e.g. `Acme_TikTok_ProfileAnalysis_Report_v1.md`.
- Required structure (full skeleton in `references/analysis.md`): metadata block with snapshot timestamp and collection method; executive summary; profile overview; method; complete video inventory table with links; engagement outcomes; content analysis (pillars, hashtags, audio); numbered factual findings; predictive insights; prioritized recommendations; limitations; sources.
- Findings are numbered, quantified, and each traceable to the inventory table.
- Every prediction carries three things: an explicit Basis (which findings it rests on), a Confidence label (High / Moderate / Speculative), and stated assumptions. Scenario tables state per-scenario assumptions (especially conversion bands) so comparative claims are derivable, not vibes. Judgment-based numeric ranges are labeled as judgment, not model output.
- Consistency sweep before shipping: every number in the executive summary must match the body, the findings, and the predictions. This class of drift (headline says "four to six months", body says "multi-year") is common and fatal to credibility.

## Stage 5: VERIFY

Goal: catch what drafting missed. Always run self-verification; run independent cross-check when stakes justify it.

- Self-verification (always): re-run the computation script against the shipped numbers; recount every categorical claim; re-check the consistency sweep. Fix and re-verify until clean.
- Independent cross-check (for high-stakes reports): delegate a recomputation-and-critique pass to a second engine via the `engine` skill (DeepSeek is the designated stats validator). Two rules from field use: give the delegate the already-verified aggregates so it spends its iteration budget on the unverified parts, and raise `--max-iterations` (default caps truncate long reviews mid-flight with no error visible in the final message).
- Meta-assess before accepting: independently re-derive every reviewer finding; accept, partially accept (fix the underlying gap instead of deleting the claim), or reject with reason. Record the revision in the report as a version bump with a revision note; keep the reviewer's findings file as the audit trail.
