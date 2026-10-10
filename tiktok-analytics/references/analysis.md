# Analysis Methodology: Metrics, Report Structure, Verification

Everything here exists because an error of that type actually shipped and had to be caught in review. The error catalog at the end is the most valuable part; read it before drafting and again before shipping.

## Time handling

- Convert `createTime` (epoch seconds) to the account's likely audience timezone; state the timezone and UTC offset in every table.
- Compute video ages from exact epochs (`snapshotEpoch - createTime`), never from minute-rounded clock times. Rounding conventions leak into velocity values at the first decimal and invite spurious "mismatches" in cross-checks. State the convention once in the inventory table caption.
- Distinguish three windows and never conflate them:
  - first-to-last posting span (content window),
  - first-post-to-snapshot (account observable age),
  - mean inter-post interval = posting span / (video count − 1), NOT span / video count.

## Core formulas

Definitions (per video and account-wide):

```
engagements        = likes + comments + shares + saves
ER by views        = engagements / plays            (report likes-only variant too)
velocity           = plays / hours_since_posting    (exact ages)
comment rate       = comments / plays
share rate         = shares / plays
follower conversion= followers / total plays        (crude: uses current followers, not followers gained)
```

Aggregates per metric: total, mean, and median. Median rule for even n: sort values, average the two middle elements (positions n/2 and n/2+1). Mispicking the middle pair (e.g. averaging positions 6 and 7 of 14 instead of 7 and 8) is the most frequent arithmetic error in this pipeline; verify medians by script, listing the two middle values.

Follower conversion from public data is a lower bound and a proxy (followers were not all gained from these plays); label it as such.

## Analysis passes

Run these in order; each maps to a report section.

1. **Aggregate performance**: totals, means, medians, ER by views (all interactions and likes-only), comment/share rates, follower conversion.
2. **Benchmark comparison**: current-year ER averages (expect a range across sources; report the range with source names), new-account test-tier view behavior, plus niche-specific context (policy windows, event calendars, seasonal attention). Cite monetization thresholds as secondary-sourced, verify-in-app.
3. **Top/bottom performers**: top three by plays AND top three by ER (they differ; report both). Bottom performers must be age-normalized: compare velocities, and always compare a batch against a same-metric baseline (the account median velocity), not against the best video.
4. **Velocity by posting slot**: group videos by time-of-day window; a batch running well below account-median velocity despite being YOUNGER than a faster batch is a genuine distribution shortfall, not an age artifact. State the format-slot confound wherever it exists (a weak slot that happened to carry long explainers is not proven evidence against the slot).
5. **Duration bands**: under 30s / 30-99s / 100s and over. Report mean plays AND mean per-video ER per band. The usual true pattern: short clips win reach, long wins engagement density, the middle wins neither. Do not assert that ordering; compute it.
6. **Content pillars**: classify every video into 3-5 dominant themes; aggregate plays, engagement, ER per pillar; compute share of total plays and engagements. Flag any pillar with fewer than four videos as low-confidence in-place.
7. **Hashtags**: frequency table; check tag-language vs content-language mismatch (growth/SEO tags in the wrong language for the audience); for any claimed pattern ("X of N videos carrying tag T finished below median"), sort and count from the table, not memory.
8. **Audio**: original vs licensed counts; note licensed-commercial-audio muting risk on commentary/news content as a risk factor, without overstating single-video coincidences as causation.
9. **Follower conversion funnel**: plays vs engagements vs followers; audit the profile's conversion infrastructure (bio link, series branding, pinned video, CTAs) as observable facts.

## Prediction protocol

Every prediction gets all three, in this order: the claim, the explicit Basis (which findings it rests on), and a Confidence label.

- **High**: follows directly from the measured data or near-universal platform mechanics.
- **Moderate**: direction supported by data, magnitude involves judgment; state the confounds.
- **Speculative**: numeric ranges that are analytical judgment, not derivation; label them as hypotheses to test. If a range requires improvement beyond any observed value (e.g. predicting a median above the current maximum), it is Speculative at best.

Scenario tables: state per-scenario assumptions explicitly, especially per-scenario follower-conversion bands, so comparative claims ("scenario C converts 3-10x more followers") are derivable from the stated assumptions rather than asserted. If two scenarios differ mainly by one lever, say which lever.

Consistency rule: no number may appear in two places with different values. The executive summary, body, findings, predictions and recommendations are one sweep; contradictions across them (a "four to six months" headline over a "multi-year" basis) destroy the report's credibility faster than any wrong median.

## Report skeleton

```
# TikTok Profile Analysis: @handle
metadata table (profile, snapshot timestamp+timezone, collection method, version)
## EXECUTIVE SUMMARY        (bottom line + key numbers)
## 1. PROFILE OVERVIEW      (attributes table, account age note, timing context)
## 2. DATA COLLECTION METHOD
## 3. VIDEO INVENTORY       (complete table, newest first, with links; formula notes)
## 4. ENGAGEMENT OUTCOMES    (4.1 aggregates, 4.2 benchmarks, 4.3 top/bottom,
                             4.4 velocity by slot, 4.5 duration, 4.6 cadence/timing)
## 5. CONTENT ANALYSIS       (pillars, hashtags, audio, conversion)
## 6. FACTUAL FINDINGS       (numbered, each traceable to the inventory)
## 7. PREDICTIVE INSIGHTS    (claim + basis + confidence; scenarios; risks)
## 8. RECOMMENDATIONS        (prioritized, each justified by a finding)
## REVISION NOTE             (from v2 onward: what the cross-check changed)
## LIMITATIONS
## SOURCES                   (primary capture + secondary benchmarks, separated)
```

Inventory table columns that earn their width: posted (local time), duration, topic label, plays, likes, comments, shares, saves, ER, plays/h. Link video IDs to live posts.

## Verification protocol

Self-verification (always, before shipping):

1. One script recomputes every derived number in the report from the raw inventory; diff against the shipped text. Fix, rerun, until zero mismatches.
2. Recount every categorical claim: top-N lists (sort first), zero-count lists, cluster counts (must sum to video count), "X of N" patterns.
3. Consistency sweep across all sections for the same figure.
4. Re-read the error catalog below as a checklist.

Independent cross-check (high-stakes reports): delegate to DeepSeek via the `engine` skill with a brief that (a) hands over the already-verified aggregates so its iteration budget goes to the unverified parts, (b) demands a numbered findings file with severity levels, and (c) forbids edits to the report. Raise `--max-iterations` (e.g. 100): default caps truncate long reviews silently. Then meta-assess: independently re-derive each reviewer finding; accept, partially accept (often the right fix is making an implicit assumption explicit rather than deleting the claim), or reject with stated reason. Ship as a version bump with a revision note; keep the reviewer's findings file as the audit trail.

## Error catalog (each entry shipped once and was caught in review)

1. **Wrong medians** (three separate medians wrong in one table): even-n middle-pair misselection. Fix: script it, print the two middle values.
2. **Top-three list from memory**: omitted the actual third place. Fix: sort all values, take the head, cite the fourth when it is close.
3. **Transposed band mean**: notes said 271.8, table said 225. Fix: the script writes the table row, not the drafter's memory.
4. **False band conclusion**: "middle band worst on both dimensions" was asserted from a miscomputed mean; corrected data showed it second on both. Fix: never assert an ordering you did not compute.
5. **Count errors**: videos over one minute (said five, was seven); zero-comment videos (said 10, was nine); posting clusters (six pairs + trio + two singles = 17 videos for a 14-video account). Fix: counts come from `len(filtered_list)`, and cluster counts are checked against the total.
6. **Cadence arithmetic**: used span/video-count for mean interval (should be span/(n−1)) and quoted an inconsistent span. Fix: define the three time windows once, derive everything from them.
7. **"Both long explainers" in a pillar that contained one**: category assignment drift between sections. Fix: single pillar assignment table; findings reference it.
8. **Zero-share claim on a pillar with one share**: absolute claims ("zero", "all", "none") are the easiest to falsify and the first thing a reviewer checks. Fix: count before writing absolutes.
9. **Contradictory monetization timeline** (headline vs body): the consistency sweep exists for exactly this.
10. **Velocity rounding mismatch** between draft and cross-check (minute-rounded vs exact epochs): pick one convention, state it, compute everything with it.
11. **Confidence inflation**: High confidence on a three-video pillar generalization. Fix: the n<4 rule.
12. **Age-blind comparison**: calling young videos underperformers before velocity-normalizing. Fix: no raw-play comparisons across ages, ever.
