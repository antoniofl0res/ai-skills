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

**Safe (≥ 0.999)** — `Safe = min(Reversibility, Exposure)`. Both sub-scores must clear 0.999.

- **Reversibility** (can the state be restored?): git reset, file restore, undo, re-deploy.
  If Reversibility < 0.999, Safe cannot reach 0.999.
- **Exposure** (does harm occur *before* any possible undo?): secrets read into context,
  messages/emails sent, data pushed to an external system, logs/transcripts created.
  A "reversible" send (you can send a correction) still leaks in the window before undo —
  score Exposure on whether the harmful event happens at all, not whether you can patch it after.
  Reading secrets into an LLM transcript is an Exposure event, not a read-only no-op.
- **Blast radius + consent** raise the score: an irreversible action on a *specifically named,
  single target the user explicitly requested* (e.g. "format drive E:") has a near-vanishing
  plausible-failure scenario once confirmed, and can clear 0.999. A glob/pattern/wildcard
  target (`rm *.log`, `DROP TABLE`) cannot — the failure scenario is "wrong file/table matched".

**Clear (≥ 0.95)**
- Is the goal specific enough to produce the right output without guessing?
- Are there ambiguous terms, missing parameters, or conflicting constraints?
- Scope creep risk: could a reasonable interpretation lead to 10× more work?

**Workable (≥ 0.95)**
- Do I have the right tools, permissions, and access?
- Is the required information present in context or reliably fetchable?
- Is the task within my capability boundary (not hallucination-prone domain)?
- **Model and Engine Alignment**: When delegating work to another engine (e.g. via `agent.py` or script), verify that the target model is explicitly specified in the command (e.g., `--model glm-5.2` for Z.ai). If it relies on implicit defaults, the execution harness will fall back to `deepseek-v4-flash`, violating user intent. Block the run and require the explicit model flag.

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
and proceed — but:
1. Log the accepted risk in one sentence before starting work.
2. Re-scope to the **named target** the user confirmed — do not widen to a glob/class/pattern
   even if the override was general. "Yes, format it" means drive E:, not "format drives."
3. If the block was on **Safe**, the override covers one execution, not a recurring/cron'd one.
   A scripted or scheduled destructive action needs its own gate per run — temporal scope does
   not carry over.
4. If you have already overridden on the same dimension twice this session, surface it:
   "This is the Nth override on Safe — the gate is doing little here; want me to retune the
   threshold instead?" Override fatigue defeats the gate; name it when it starts.

## Auto-trigger checklist

Run the gate silently before any of these action types:

- File/dir deletion: `rm`, `del`, `Remove-Item`, `rmdir -rf`, `git clean`,
  `Remove-Item -Recurse -Force`
- Discarding uncommitted work: `git reset --hard`, `git checkout --`, `git restore`,
  `git stash drop` (name the command, not just the abstract "overwriting uncommitted changes")
- History rewrite / shared-state git: `git push`, `git push --force`, `git rebase`,
  `git commit --amend` on published commits
- Messaging / external posts: email, Slack, Teams, GitHub comments/PRs/issues,
  Twitter/X, forum posts
- Database: `DROP`, `TRUNCATE`, `DELETE` without `WHERE`, `ALTER`, migrations on prod
- Infrastructure / IaC: CI/CD pipeline edits, permissions, prod env vars,
  `terraform apply`/`destroy`, `kubectl delete`/`apply`, `helm uninstall`,
  `aws s3 rm`/`gcloud`/`az` destructive subcommands, service stop/restart
- Publishing / release: `npm publish`, `pip upload`, `docker push`, `git tag`+push,
  GitHub Releases, any registry push
- System state: registry edits, `schtasks`/cron create-or-alter, firewall rules,
  `setx` machine env vars
- Reading secrets into context: `.env`, key files, vault reads, connection strings
  (see Exposure sub-score — read is NOT always safe)
- Overwriting files that have uncommitted local changes
- Any action writing to an external API with side effects (POST/PUT/DELETE)

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

## Calibration anchors

Use these to anchor scores instead of guessing. Each threshold gets concrete examples.

**Safe 0.999** — cannot construct a plausible failure scenario:
  - `git reset --hard` on a local branch where the user confirmed the lost changes are unwanted (reversible via reflog anyway): 0.999
  - `Remove-Item` one named `.tmp` file the user pointed at: 0.999
  - `git push --force` to your own solo feature branch: 0.80 (plausible: wrong remote, collaborator added since) → BLOCK
  - `DROP TABLE` in prod: 0.50 (irreversible at scale) → BLOCK, force override

**Safe — Exposure axis:**
  - Read a `.env` into context: 0.70 (transcript/log disclosure surface) → BLOCK unless Value+Workable and user consents
  - Send a test email to yourself: 0.85 (sent = leaked before undo) → BLOCK, light override

**Clear 0.95** — goal specific enough to act without guessing:
  - "Refactor the auth module": 0.50 (scope undefined) → BLOCK
  - "Extract the JWT validation in auth.js:42 into a pure function, no behavior change": 0.97 → CLEAR

**Workable 0.95** — tools, access, and capability present:
  - "Debug the Kubernetes networking" with no cluster access in context: 0.60 → BLOCK
  - "Run the test suite" with package.json visible: 0.98 → CLEAR

**High Value 0.90** — net benefit clearly positive:
  - 3-line readability refactor, no behavior change: 0.60 (cost > benefit) → BLOCK
  - Fix a failing build: 0.95 → CLEAR
  - Marginal 0.90–0.92: state it in the brief even on CLEARED so the user can reprioritize.
