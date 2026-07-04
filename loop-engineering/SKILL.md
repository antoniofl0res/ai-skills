---
name: loop-engineering
description: >-
  Self-applied heuristics for running long agent loops (10+ tool calls) without
  degrading: define an exit contract, detect stalls, recover from failures by
  re-reasoning, and apply effort proportional to task depth. Trigger only on
  long, iterative, or stuck tasks — not routine multi-step work.
---

# Loop Engineering

Your execution loop — the perception → reasoning → action → observation cycle —
is what turns a language model into a goal-directed agent. On long runs it
degrades without discipline: context fills with stale output, the agent repeats
actions, retries failures blindly, and burns tokens past the point of value.

This skill is a set of **self-applied heuristics**. Everything here is something
you do by reasoning — there are no external scripts to run.

## When to apply this (and when not to)

**Trigger:** a task has reached **≥10 tool calls** AND shows signs of depth or
trouble — iterative debugging that isn't converging, a multi-file refactor,
research with synthesis, a batch pipeline, or you feel stuck / repetitive /
uncertain how much further there is to go. Also trigger any time you notice
yourself repeating actions or looping.

**Do NOT trigger** on routine multi-step work (1–9 calls, linear path, clear
end). Loading this advice on a quick edit is overhead with no payoff.

## Proportional application

Match the depth of optimization to the expected loop depth.

| Task profile | Expected calls | Apply |
|---|---|---|
| **Quick** — one-shot read, trivial edit | 1–3 | Nothing from here. Just do the task. |
| **Standard** — small pipeline, linear sequence | 3–9 | Define an exit contract (below). Skip the rest. |
| **Deep** — iterative gen, multi-file refactor, research synthesis | 10–20 | All five heuristics. |
| **Marathon** — batch processing, large pipeline, long run | 20+ | All five, plus checkpoint state every ~5 iterations. |

If you start at one tier and the task grows, re-assess — don't stay in the
shallow tier on a task that became deep.

---

## Heuristic 1 — Define an exit contract

Before starting any Standard+ task, state: **"I am done when [specific
condition]."** Include at least:

- **One deterministic criterion** — a concrete artifact or state ("file X exists
  with expected content," "test suite passes," "the user confirms the answer").
- **One heuristic boundary** — a budget ("max 15 tool calls," "~50K tokens,"
  "stop after 3 search queries and synthesize").

Re-read this contract at every "am I done?" decision point. The heuristic
boundary is a stop condition, not a target — if you hit it, stop and deliver or
escalate, don't silently keep going.

## Heuristic 2 — Manage your context actively

Each iteration appends observations and reasoning. Without active management,
signal-to-noise degrades until you reason over a soup of stale data.

- **Summarize completed sub-tasks.** When a sub-goal is done, write a 1–3 line
  summary of *what was learned* and *what state was produced* (file path, data,
  result). Then stop carrying the raw trace forward in your reasoning.
- **Externalize large outputs.** When a tool returns >100 lines you'll need
  later, save it to a file and reference the path. Do not keep it inline.
- **Checkpoint before branching.** Before exploring multiple approaches, save
  the current state summary to a file so you can return to it without
  re-deriving.
- **Watch for data-collection-without-synthesis.** If your last 3 messages are
  all tool output with no reasoning between them, you are collecting without
  integrating — pause and synthesize.
- **Re-verify stale references.** If you're acting on a value or file produced
  >5 tool calls ago, verify it still exists and is still correct before relying
  on it.

## Heuristic 3 — Detect stalls and terminate

At the end of each iteration in a Deep+ task, run the **three-gate check**:

1. **Deterministic success** — does the output meet the exit contract? If yes →
   deliver.
2. **Boundary breached** — iteration count, token estimate, or wall-time budget
   hit? If yes → deliver best-effort or escalate; do not continue silently.
3. **Diminishing returns** — was this iteration materially different from the
   previous two? If not, you've plateaued → deliver or escalate.

**Stall signatures** (any one means stop and change strategy, not push harder):
- **Identical-repeat** — same tool call, same arguments, last 2–3 actions.
- **Oscillation** — A → B → A → B without convergence.
- **Plateau** — last 2–3 iterations produced no meaningful change in output.

If stalled: stop the current approach, revert to the last checkpoint (Heuristic
2), and redesign the strategy or escalate to the user. **Do not repeat the same
pattern expecting a different result.**

## Heuristic 4 — Recover from failures without blind retry

Never re-run the exact same action against the exact same state — it produces
the same failure and wastes tokens. Before retrying, answer three questions:

- *Why did this fail?* — permission? timeout? wrong input? wrong approach?
- *What state am I in?* — is partial work done? is the system in a dirty state?
- *What's the least-cost recovery?* — rollback? alternative approach? ask user?

**Failure routing:**
- **Known/predictable error** → use a deterministic fix (correct the parameter,
  add the missing flag) and retry once. Don't re-reason from scratch.
- **Flaky/transient** (timeout, rate limit) → retry with backoff, max 3, then
  escalate.
- **Semantic** (wrong approach, logic error) → revert to checkpoint, re-reason,
  try a different approach. Do not retry the same logic.
- **Persistent** (3 consecutive failures on the same sub-goal) → stop. Surface
  to the user: what was tried, what failed, what alternatives remain. Do not
  silently keep trying.

## Heuristic 5 — Spend effort proportional to value

Not every step deserves the same cognitive depth.

- **Reserve deep reasoning for decision nodes** — approach selection, error
  diagnosis, architecture, ambiguous judgment. These are the 20% of steps worth
  real thought.
- **Keep mechanical steps cheap** — parsing output, formatting, running a known
  command, extracting a value. Do these directly; don't overthink them.
- **Verify the critical path, trust the routine.** Verify the output artifact in
  your exit contract, the first time you use a new pattern, and any action where
  a silent failure would be hard to detect. Skip verification for proven,
  routine operations — it costs tokens for no benefit.
- **Batch independent actions.** Actions that don't depend on each other go in
  one assistant turn (parallel tool calls), not serial.
- **Early-exit.** When a sub-task meets its success criterion, stop. Don't keep
  polishing past the exit contract.

---

## Quick reference: before starting a Deep+ task

1. **Depth?** (quick / standard / deep / marathon) → apply only that row.
2. **Exit contract?** (deterministic criterion + heuristic budget)
3. **Checkpoint location?** (skip if quick)
4. **Recovery plan** if the first approach fails?

## At the end of each iteration

- Am I closer to the exit contract? If not → strategy shift, not more effort.
- Is my context signal-to-noise healthy? If not → summarize / externalize.
- Did my last action actually change the environment? If not → don't re-reason
  from stale data.
- Could I have short-circuited any step? If yes → note it and do so next time.
- Am I using the cheapest approach that answers the question?
