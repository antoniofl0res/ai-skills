---
name: loop-engineering
description: >-
  Optimize agentic execution loops via 5 principles: state/context management with
  advanced compaction techniques, deterministic & heuristic termination,
  recursive self-correction with backtracking and deterministic short-circuiting,
  environmental coupling with action space pruning, and computational budgeting
  with tiered compute routing (model cascading).
  Trigger on any multi-step agentic task (3+ tool calls, iterative debugging,
  research synthesis, multi-file generation, data pipelines, or any task where
  an agent loops over perception→reasoning→action→observation steps). Also
  trigger when an agent is stuck, repeating actions, consuming excessive tokens,
  or when the user asks about making agent runs more efficient. This skill
  teaches the agent to be self-aware about its own operational efficiency.
---

# Loop Engineering

## Why this matters

Your execution loop — the perception→reasoning→action→observation cycle — is the
architecture that turns a language model into a goal-directed agent. Without
deliberate loop engineering, agents suffer context degradation, infinite loops,
wasted tokens, hallucinated state, and brittle error recovery. This skill gives
you five concrete disciplines to own your operational lifecycle.

**When to explicitly invoke this skill:** Before any multi-step task (3+ calls). When you notice yourself repeating the same action. When context feels bloated. When an action fails and you're about to blind-retry. At every "done?" decision point.

---

## ⚖️ Proportional Application

Not every optimization pays off on every task. Over-engineering a 3-step task
with checkpointing and verification adds 40-50s of overhead for zero benefit.
**Match the depth of optimization to the expected loop depth.**

| Task Profile | Expected Calls | Apply |
|---|---|---|
| **Quick hit** — single command, one-shot read, trivial edit | 1-3 | Just define an exit contract. Skip everything else. |
| **Standard** — multi-step pipeline, small batch, linear sequence | 3-8 | All 5 core principles at standard depth. Use `termination-heuristics.sh` at the end. |
| **Deep** — iterative generation, multi-file refactor, research with synthesis | 8-20 | Core principles + Advanced techniques (Context Compaction, Tiered Routing). Use all 3 scripts. |
| **Marathon** — batch processing, large data pipelines, long-running agent | 20+ | Full suite. All advanced techniques. Recursive summarization every 5 iterations. |

**Before starting, take 3 seconds to estimate:**
1. How many tool calls will this take? → pick a row above
2. Is the output critical or exploratory? → critical = more verification
3. Is the path clear or might I need to backtrack? → uncertain = more checkpointing

Then apply only what the row says. The rest is noise.

---

## Principle 1: State & Context Vector Management

### The insight
Each loop iteration appends observations, reasoning traces, and action results
to context. Without active management, signal-to-noise ratio degrades until the
agent is reasoning over a soup of stale data.

### Agent actions

**Before each major iteration cycle:**
1. **Quick-scan the conversation.** Ask: *what fraction of my context is
   live/relevant right now?* If >50% of messages are completed tool output from
   actions that are no longer being referenced, you need to prune or summarize.
2. **Summarize completed sub-tasks.** When a sub-goal is achieved, do NOT carry
   its full execution trace forward. Write a 1-3 line summary of *what was
   learned* and *what state was produced* (file path, data, result). Then drop
   the raw trace from active reasoning.
3. **Externalize large outputs.** When a tool returns >100 lines of output that
   you'll need later, save it to a file and reference the file path. Do not keep
   it in the conversation's active context.
4. **Checkpoint intermediate state.** Before branching (exploring multiple
   approaches), save the current state summary to a file so you can return to
   it without re-deriving.

### Advanced: Context Compaction Techniques
**Use when:** Deep loops (8+ iterations) or when context already feels bloated.

When working in deep loops, basic summarization isn't enough.
Use these techniques to keep context lean:

1. **Recursive summarization.** Every 3-5 iterations, write a compact summary
   of what was accomplished, what state was produced, and what remains. Then
   let the raw iteration trace age out of your active reasoning. Use a
   lightweight model or concise formatting for the summary — it doesn't need
   to be pretty, just correct and referenceable.

2. **RAG-style retrieval from checkpoints.** Instead of keeping all checkpoints
   in context, save them as timestamped files in a `checkpoints/` directory.
   When you need to recall a past state, read only the specific checkpoint
   file relevant to the current question. Don't load all of them.

3. **Drop obsolete tool outputs.** After an action's result has been consumed
   (e.g., you read a file, extracted the data, and wrote it elsewhere), the
   raw tool output is dead weight. Acknowledge it, extract the signal, then
   treat it as reference material — not active context.

**Heuristics:**
- If your last 3 messages are all tool output (no reasoning between them), you
  are in data-collection mode without synthesis — pause and integrate.
- If you're referencing a file or value that was produced >5 tool calls ago,
  verify it still exists / is still correct before using it.

---

## Principle 2: Deterministic & Heuristic Termination

### The insight
Agentic loops need explicit halting conditions. Without them, you risk infinite
recursion, token waste, or indefinite oscillation.

### Agent actions

**Before starting the task:**
1. **Define an exit contract.** Write down: "I am done when [specific condition]."
   This should include at least one deterministic criterion (e.g., "file X exists
   with expected content") and at least one heuristic boundary (e.g., "max 15
   iterations, or 50K tokens, or 5 minutes wall time").
2. **Set an iteration budget.** Decide a max loop count for the task. If the
   task is open-ended (research, exploration), set a "resource budget" instead
   (e.g., "I will stop after 3 search queries and synthesize what I have").

**At the end of each iteration:**
3. **Run the termination check.** Three gates, in order:
   1. **Deterministic success** — does the output artifact meet the exit contract?
   2. **Heuristic boundary breached** — iteration count, token estimate, or time?
   3. **Diminishing returns** — was this iteration's output materially different
      from the previous two? If not, you're plateaued.
4. **If done → deliver and stop.** If not done → before looping back, ask: *Is my
   current approach working, or do I need a strategy shift?*

**Stall detection pattern:**
Run `loop-stall-detector.sh` when you suspect you're going in circles. It checks
for three failure signatures:
- **Identical-repeat** — same tool call with same arguments in the last 3 actions
- **Oscillation** — alternating between two states A→B→A→B without convergence
- **Progress-plateau** — last N iterations produced zero net change in output quality

---

## Principle 3: Recursive Self-Correction & State Backtracking

### The insight
Agents will execute sub-optimal actions. The loop must handle failures without
collapsing — not via blind retry, but through intelligent recovery.

### Agent actions

**When an action fails:**
1. **Never blind-retry.** Re-running the exact same prompt against the exact same
   state will produce the exact same failure (or near enough to waste tokens).
2. **Route error → reasoning.** Before retrying, answer these three questions:
   - *Why did this fail?* (diagnose the error — permission? timeout? wrong input?)
   - *What state am I in now?* (is partial work done? is the system in a dirty state?)
   - *What's the least-cost recovery path?* (rollback? alternative approach? ask user?)
3. **Implement backtracking.** If the failure corrupts state (e.g., a partial write,
   a half-migrated DB), revert to the last known-good checkpoint before retrying.
   The checkpoints you saved under Principle 1 are your recovery points.
4. **Escalate on persistent failure.** After 3 consecutive failures on the same
   sub-goal, surface the pattern to the user with: what was tried, what failed,
   and what alternatives remain. Do not silently keep trying.

**Decision tree for failures:**
```
Action failed
├─ Determined in advance (known error, predictable pattern)
│  └─ SHORT-CIRCUIT: Use a hardcoded script or retry logic
│     — do NOT route through LLM reasoning. Only escalate to
│     LLM if the script-based handler fails 3 times or the
│     error changes in an unexpected way.
├─ Deterministic (known error code, validation rejection)
│  └─ Fix the specific parameter/input → retry (1 attempt)
├─ Nondeterministic (timeout, rate limit, flaky service)
│  └─ Retry with backoff (max 3) → escalate
└─ Semantic (wrong approach, logic error)
   └─ Revert to checkpoint → re-reason → try alternative approach
```

---

## Principle 4: Environmental Coupling & Feedback Ingestion

### The insight
The agent's effectiveness is directly tied to how accurately it perceives the
*actual* state of the external environment after each action.

### Agent actions

**After every action with external side-effects:**
1. **Verify the critical path, trust the routine.** You don't need to verify
   every file write or every API call. Reserve verification for:
   - The output artifact you committed to in your exit contract
   - The first time you use a new tool or pattern (build confidence)
   - Actions where a silent failure would be hard to detect
   Skip verification for routine, proven operations — the verification itself
   costs tokens and time.
2. **Parse into a standardized observation.** When you get feedback from the
   environment (file contents, API response, search results, terminal output),
   extract the *signal* from the *noise*. Ask: *what materially changed? what
   do I now know that I didn't before this action?*
3. **Diff against prior state.** If possible, compare the new observation to the
   previous known state. The difference *is* the feedback. Everything else is
   repetition.

### Advanced: Action Space Pruning
**Use when:** Open-ended tasks with 5+ tool categories available, or when
delegating sub-tasks.

The tools available to you at each step are an implicit part of your action
space. An unpruned action space (all tools always available) increases both
token cost and decision entropy.

1. **Phase-constrain your tools.** At the start of each task phase, explicitly
   consider which tools are relevant *right now*:
   - **Read/analyze phase** — do you need write tools? File-creation tools?
     If not, suppress them from consideration. Focus on search, read, and
     observation tools.
   - **Build/write phase** — do you need search tools? Web tools? Block them
     out and focus on file/template tools.
2. **Delegate narrow sub-tasks with restricted toolsets.** When using
   `delegate_task`, explicitly pass `toolsets` that match the sub-task. A
   parsing sub-agent doesn't need `web` tools. A search sub-agent doesn't
   need `terminal` tools.
3. **Hide irrelevant tool categories.** If a phase has no need for `browser`
   (data processing), `web` (local file work), or `vision` (text-only task),
   note it as out-of-scope for the current iteration and avoid browsing
   through options that don't apply.

**Heuristics:**
- If you're about to act based on an assumption about the environment (e.g.,
  "assuming the file was modified"), stop and verify first.
- If an observation exactly matches the previous observation for the same
  action, the environment didn't change — don't treat it as new information.
- For remote systems (APIs, databases), prefer idempotent actions that let you
  check-before-act.

---

## Principle 5: Computational & Latency Budgeting

### The insight
Every loop iteration costs tokens, time, and potentially money. The marginal
gain of one more iteration must justify its cost.

### Agent actions

**While planning the approach:**
1. **Right-size the model strategy.** For parsing, formatting, and observation
   processing — where the reasoning load is low — prefer concise, direct steps
   that don't require expensive reasoning chains. Reserve deep reasoning for
   decision nodes: approach selection, error diagnosis, architecture design.

2. **Implement tiered compute routing (model cascading).** Not every step
   needs the same cognitive horsepower. Dynamically route loop operations
   based on complexity:
   - **Simple/mechanical** (parse API response, extract structured data,
     format output, run a regex) → handle with direct code or a lightweight
     approach. No LLM call needed.
   - **Routine reasoning** (apply known pattern, validate output, compare two
     options) → concise, direct reasoning. Don't overthink.
   - **Complex reasoning** (multi-step planning, architectural decisions,
     ambiguous error diagnosis) → full-depth reasoning. This is where you
     spend the heavy tokens.
   - **Meta-decision** (should I continue? strategy shift?) → the lightest
     possible check that answers the question. 3-second thought, not a
     treatise.
   The goal: spend 80% of your token budget on the 20% of steps that are
   genuinely hard. Everything else gets a crisp, cheap read.

3. **Estimate upfront cost.** Before starting an expensive operation (large file
   generation, batch processing, web scraping), estimate the cost in tokens and
   ask: *could I get 80% of the value with a cheaper approach?*

**During execution:**
4. **Implement early-exit heuristics.** When a sub-task has a simple success
   criterion, check it frequently and exit early. Don't keep polishing.
5. **Track diminishing returns per script.** If you've bundled a script that
   iteratively refines an output, track whether each pass is producing measurable
   improvement. After 2 passes with <5% change, stop.
6. **Batch independent actions.** Actions that don't depend on each other should
   be dispatched in parallel (via delegate_task tasks array). Serial execution
   of independent work multiplies latency unnecessarily.

**Cost-awareness pattern:**
```
Before each iteration, ask:
  - What is the cheapest way to get the information I need next?
  - If I stopped RIGHT NOW, would the output be useful?
  - Is my current iteration producing >10% improvement over the last?
If "no" to all three → stop and deliver.
Also: consult the Proportional Application table at the top. Are you still
in the right depth tier, or did the task expand? Re-assess every 5 iterations.
```

---

## Quick Reference: Loop Health Checklist

Before starting a complex task, mentally run through these 5 questions:

| # | Question | Links to |
|---|----------|----------|
| 0 | What depth is this? (quick/standard/deep/marathon) | Proportional Application ⚖️ |
| 1 | What is my exit contract? (deterministic + heuristic) | Principle 2 |
| 2 | What is my max iteration/resource budget? | Principle 2, 5 |
| 3 | Where will I save state checkpoints? (skip for quick tasks) | Principle 1 |
| 4 | What's my recovery plan if the first approach fails? | Principle 3 |
| 5 | What independent work can I parallelize? | Principle 5 |

At the end of each iteration, answer:
- Am I closer to my exit contract? If not, strategy shift needed.
- Is my context signal-to-noise ratio healthy? If not, prune/summarize or use Recursive Summarization.
- Did my last action actually change the environment? If not, don't re-reason from stale data.
- Could I have short-circuited any step? If yes, note it for next time (Deterministic Short-Circuiting).
- Am I using the cheapest approach that answers the question? If not, apply Tiered Compute Routing.

---

## Bundled Utilities

This skill ships with three scripts under `scripts/`. Run them with
`bash <skill-dir>/scripts/<name>.sh` — or `python <skill-dir>/scripts/<name>.py`
for the Python variants.

- **`context-budget-check.sh`** — Scans your current working directory for
  accumulation artifacts and estimates whether you're in a healthy state for
  further iterations. Use when context feels bloated or you're >10 iterations deep.

- **`loop-stall-detector.sh`** — Checks for stall signatures in your recent
  action history (if logged) or prompts you to self-diagnose: identical repeats,
  oscillation, or progress plateau. Use when you suspect you're going in circles.

- **`termination-heuristics.sh`** — Prompts you through the three termination
  gates (deterministic success, heuristic boundary, diminishing returns) and
  helps decide whether to continue, deliver, or escalate. Use at every "am I
  done?" decision point.
