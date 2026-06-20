---
name: deepseek-orchestration
description: "Route work between Claude and DeepSeek and call DeepSeek correctly. ALWAYS trigger when the user types /deepseek, says \"use deepseek\", \"send to deepseek\", \"deepseek review\", \"run this through deepseek\", \"deepseek mode\", \"force deepseek\", \"cross-check\", or \"multi-model\". Also consider DeepSeek for: statistical/methodological validation, causal/multi-step reasoning, cross-model fact consensus, large-scale data extraction, simulation/modeling code review, multilingual technical work, and research synthesis. deepseek_chat = deepseek-v4-flash (fast, scale, supports system+temperature); deepseek_reason = deepseek-v4-pro (chain-of-thought, returns reasoning trace + answer separately). Set max_tokens explicitly — defaults truncate. Decision-guide + correct-invocation reference."
---

# DeepSeek Orchestration

Route work between Claude and DeepSeek, and — just as important — **call DeepSeek correctly**. Most of the value in this skill is in getting the invocation right; the routing is something Claude can largely reason about on its own.

**Core principles**
1. Route on stakes × complexity, not reflex. Not everything needs DeepSeek.
2. Invoke correctly: set `max_tokens`, pick `temperature`, use `system`, handle the reasoning split.
3. Be honest about cost and limits (8192-token output cap; pricing not reliably known here).
4. Offer choices; respect the user's QUICK-vs-DEEP call.
5. Adapt within the session; propose a skill edit when a durable pattern appears.

---

## The two tools (ground truth)

The live API (`deepseek_models`) serves **`deepseek-v4-flash`** and **`deepseek-v4-pro`**.
> ⚠️ The tool *descriptions* still say "DeepSeek-V3 / DeepSeek-R1" — they lag the model rename. Trust `deepseek_models`, not the description strings. If unsure which models are live, call `deepseek_models` once at the start of a DeepSeek-heavy session.

| Tool | Model | Use for | Params it accepts |
|------|-------|---------|-------------------|
| `deepseek_chat` | v4-flash | speed/scale: synthesis, extraction, translation, code review, drafting | `prompt`, `max_tokens`, `system`, `temperature` |
| `deepseek_reason` | v4-pro | chain-of-thought: stats/methods validation, causal logic, proofs, multi-step inference | `prompt`, `max_tokens` **only** |

Legacy aliases (old skill language): "V3" → v4-flash, "R1" → v4-pro.

---

## How to call DeepSeek correctly  ← the part that matters most

### max_tokens — set it every time
- Hard cap is **8192** for both tools — `max_tokens > 8192` is rejected at the call interface, not silently clamped. Defaults are **1000** (chat) and **2000** (reason); these don't error, they just cut the output short — on `deepseek_reason` this typically leaves the `## Answer` section **empty** (the trace ate the budget), so it's detectable if you actually look at the response.
- Rule of thumb: short check/extraction → 1500–2500; substantive review or synthesis → 3500–6000; long structured output → up to 8192.
- **`deepseek_reason` gotcha:** its `max_tokens` covers the *reasoning trace AND the final answer together*. The trace can be long, so at low budgets it consumes everything and the `## Answer` block returns empty — an empty Answer almost always means budget, not model failure; rerun higher. For any non-trivial reasoning task, budget **≥4000** (verified: a multi-step problem returned a blank Answer at 700 and a complete one at 4500).

### temperature (deepseek_chat only)
- `0` — validation, fact-check, data extraction, anything where determinism and reproducibility matter (default 0.7 is wrong for these).
- `0.7` (default) — synthesis, drafting, generative work.
- `deepseek_reason` does **not** take temperature; don't pass it.

### system (deepseek_chat only)
Set a sharp reviewer/persona to lift quality at no extra cost, e.g.
`"You are a biostatistician red-teaming a methods section. List concrete errors and unstated assumptions only — no praise, no restating the input."`
`deepseek_reason` takes no system prompt; fold the role into the `prompt` instead.

### Handling the reasoning response
`deepseek_reason` returns the reasoning trace and the final answer **separately**. Use the final answer as the deliverable. Surface the trace only when the *chain itself* is the point (e.g. a methodological critique where the user needs to see the logic), and then summarize it — don't paste it raw.

### Large inputs (the "50-page doc / 100+ records" cases)
The prompt has to carry the input, and output is capped at 8192. So:
- **Don't** dump a whole PDF and expect a full summary — Claude already does bulk reading well, and the output cap makes it lossy anyway.
- **Do** use Claude to pre-distill/chunk, then send DeepSeek a *focused analytical pass*: "find the statistical errors in this Methods extract", "stress-test these three assumptions", "cross-check these five claims". That is where a second model earns its place.
- For 100+ record extraction: chunk to fit, `temperature: 0`, and specify a strict output schema (e.g. "return JSON only, no prose").

---

## Explicit triggers (obey immediately)

| Phrase | Action |
|--------|--------|
| `/deepseek` | route to v4-flash (or v4-pro if the task is reasoning-heavy) |
| `use deepseek` / `send to deepseek` / `run this through deepseek` | same |
| `deepseek review` | comprehensive review via DeepSeek |
| `deepseek mode` | route all outputs this session through DeepSeek |
| `force deepseek` | override any LOW-ROI classification |
| `multi-model` / `cross-check` | Claude + DeepSeek, compare and reconcile |
| `/deepseek pro` (or `r1`) | force `deepseek_reason` (v4-pro) |
| `/deepseek flash` (or `v3`) | force `deepseek_chat` (v4-flash) |

On an explicit trigger: name the model, set an appropriate `max_tokens`, run, and give a one-line cost-shape note (approximate output size; the tools return no token/usage telemetry and pricing isn't reliably known here, so don't quote a token count you can't see). No multi-step ceremony.

---

## When DeepSeek earns its place (no explicit trigger)

**Strong fit — offer a DeepSeek pass:**
- Statistical / methodological validation for publication or a real decision → **v4-pro**
- Causal or multi-step reasoning on a complex scenario → **v4-pro**
- Cross-model consensus on a critical fact or claim → both, reconcile
- Simulation / modeling / numerical code where edge cases bite → **v4-pro**
- Research synthesis or extraction across many sources → **v4-flash** (extract) + Claude (narrative)
- Multilingual technical work → **v4-flash** + Claude refinement

**Let the user choose QUICK vs DEEP:** exploratory analysis scripts, internal tools, prototypes, one-offs.

**Skip DeepSeek (Claude only):** utility scripts, syntax/import fixes, scaffolding, throwaway code, personal notes — unless explicitly triggered.

When it's a judgment call, ask in one line: *"Quick Claude pass, or a v4-pro red-team of the stats (~4–5k tokens)?"*

---

## Workflow efficiency

- **Batch edits.** 3+ changes to a file → one batched pass, not serial `str_replace` calls.
- **Artifact v2 for major rewrites.** Fresh file beats many in-place edits; keeps clean version history.
- **Parallel when speed matters.** Run DeepSeek and Claude on the same input, then reconcile.

| Situation | Approach |
|-----------|----------|
| 1–2 changes | serial is fine |
| 3+ changes | batch |
| major rewrite | artifact v2 |
| speed + second opinion | parallel + reconcile |

---

## In-session adaptation

Claude has no cross-session memory here, so there are no persistent "hit-rate" stats — but **within a session** Claude should adapt to what it sees:
- DeepSeek returning false alarms or low-value notes on a task type → stop offering it there; say so.
- User says "too many DeepSeek offers" → switch to explicit-trigger-only for the session.
- User says "always use deepseek" → enter `deepseek mode`.
- A pass gets truncated → it almost always means `max_tokens` was too low; rerun higher, don't blame the model.

**`/optimise deepseek`** — on demand, give an honest session recap: how many DeepSeek calls, what they were for, which added real value, and **one** concrete suggestion (e.g. "you've routed three MSF methods sections to v4-pro today — want me to add that as a standing pattern in this skill?"). If yes, draft the SKILL.md edit. No fabricated percentages.

---

## Fallback when DeepSeek is unavailable

If a DeepSeek call errors, times out, or returns empty:
1. Say so plainly: *"DeepSeek unavailable ([reason]) — running a Claude comprehensive review instead."*
2. Claude does the full pass itself: edge cases, statistical/algorithmic soundness, assumptions, failure modes, clarity.
3. Flag it: *"⚠️ Claude-only — re-run with /deepseek when the service recovers if you want the second model."*

Never let an outage block the work.

---

## Quick reference

```
chat  (v4-flash): synthesis, extraction, translation, drafting, code review
                  → set max_tokens 3500–6000; temperature 0 for validation/extraction; use a sharp system prompt
reason (v4-pro):  stats/methods validation, causal logic, proofs, multi-step
                  → set max_tokens ≥4000 (trace + answer share the budget); no system/temperature
both:             output capped at 8192; verify live models with deepseek_models
```
