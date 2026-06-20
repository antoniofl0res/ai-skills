---
name: preflight
description: >-
  Gate-check any task through a four-dimension framework (Clear / High Value / Workable / Safe)
  before proceeding. Use this skill: (1) whenever the user types "/preflight" or asks to evaluate
  a task through the framework; (2) automatically — BEFORE taking any action that is hard to
  reverse or affects shared systems — including file/directory deletion, git push or force-push,
  sending emails or messages, modifying CI/CD or infrastructure, dropping database tables,
  overwriting uncommitted changes, or posting to external services. In auto-trigger mode, run the
  check silently in your head and only surface it when a gate fails; if all gates pass, proceed
  without mentioning it.
---

# Preflight gate-check

A four-gate framework that blocks action until all dimensions clear their probability threshold.
The asymmetry is intentional: safety has no tolerance; value has the widest margin because a
best-guess task with medium confidence is still worth attempting if it is safe and clear enough.

## Thresholds

| Dimension | Threshold | Rationale |
|-----------|-----------|-----------|
| **Safe** (includes Reversibility) | **0.999** | Permanent harm has no recovery path |
| **Clear** (task is well-defined enough to act) | **0.95** | Ambiguity above 5% wastes effort and risks wrong output |
| **Workable** (tools, context, and authority exist) | **0.95** | Attempting without the means produces theatre, not work |
| **High Value** (net benefit relative to cost/effort) | **0.90** | Some uncertainty is fine if the upside is real |

All four must clear. One fail = block.

## Workflow

### Step 1 — Score each dimension

For each dimension, reason explicitly:

**Safe (≥ 0.999)**
- What is the worst-case outcome if this goes wrong?
- Is it reversible? (git reset, file restore, undo?) If yes, how easily?
- Does it affect shared state (push, send, deploy, drop)?
- Does it touch credentials, secrets, or production?
- Sub-score: **Reversibility** (0–1). If Reversibility < 0.999, the Safe score cannot reach 0.999.

**Clear (≥ 0.95)**
- Is the goal specific enough to produce the right output without guessing?
- Are there ambiguous terms, missing parameters, or conflicting constraints?
- Scope creep risk: could a reasonable interpretation lead to 10× more work?

**Workable (≥ 0.95)**
- Do I have the right tools, permissions, and access?
- Is the required information present in context or reliably fetchable?
- Is the task within my capability boundary (not hallucination-prone domain)?

**High Value (≥ 0.90)**
- What is the concrete benefit of completing this?
- What is the cost/effort (time, risk, side effects)?
- Net value = benefit − cost. Is the ratio clearly positive?

### Step 2 — Aggregate

`p(proceed) = min(Safe, Clear, Workable, Value)`

If `p(proceed) ≥` all thresholds: **proceed**. Do not mention the check.

If any threshold fails: **stop and emit the constraint brief** (Step 3). Do not attempt the task.

### Step 3 — Constraint brief (on fail)

When invoked manually (`/preflight`) or when a gate fails in auto-trigger mode, output this
structure — and nothing else (no attempt at the task):

```
PREFLIGHT — [BLOCKED / CLEARED]

Scores
  Safe:       0.XX  (threshold 0.999)  ✓ / ✗
  Clear:      0.XX  (threshold 0.95)   ✓ / ✗
  Workable:   0.XX  (threshold 0.95)   ✓ / ✗
  High Value: 0.XX  (threshold 0.90)   ✓ / ✗

Blocking dimension(s):
  [Dimension] — [one sentence: what specifically is uncertain or missing]

Minimum viable unlock:
  [The smallest change that would raise the failing score above threshold]

Proposed next step:
  [Concrete action: a clarifying question, a safer scoped alternative, a
   prerequisite to complete first, or an explicit "proceed at your risk" prompt
   the user can give to override]
```

On CLEARED (all pass), suppress the report and proceed directly.

### Step 4 — Override

If the user explicitly acknowledges the constraint brief and instructs you to proceed anyway
("yes, proceed", "override", "I accept the risk"), treat this as raising the threshold bar
and proceed — but log the accepted risk in one sentence before starting work.

## Auto-trigger checklist

Run the gate silently before any of these action types:

- `rm`, `del`, `Remove-Item`, `rmdir -rf`, `git clean` (file/dir deletion)
- `git push`, `git push --force`, `git reset --hard`, `git rebase` (history rewrite)
- `git commit --amend` on published commits
- Sending email, Slack, Teams messages, GitHub comments/PRs
- Database `DROP`, `TRUNCATE`, `DELETE` without `WHERE`
- Infrastructure changes: CI/CD pipeline edits, permissions, environment variables in production
- Any action writing to an external API with side effects (POST/PUT/DELETE)
- Overwriting files that have uncommitted local changes

For purely local, read-only, or fully reversible actions, skip the check.

## Calibration notes

- **0.999** is not certainty; it means "I cannot construct a plausible failure scenario."
  If you can, score lower and block.
- Scores are your epistemic state, not objective probabilities. Be honest about what you
  don't know — unknown unknowns lower the score.
- When Value is marginal (0.90–0.92), say so in the brief even on a CLEARED result. The
  user may choose to reprioritize.
- A task that is Clear + Safe + Workable but low Value (< 0.90) is still a block. Doing
  the wrong thing efficiently is not a win.
