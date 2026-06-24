---
name: engine
description: "Route work between execution engines — Claude and Antigravity (Gemini) as primary drivers, GLM-5.2 via Z.ai, and DeepSeek — and invoke each correctly. ALWAYS trigger when the user says /engine, \"delegate to GLM\", \"hand off to glm\", \"run this on glm\", \"use deepseek\", \"send to deepseek\", \"deepseek review\", \"cross-check\", \"multi-model\", \"which engine/model should run this\", \"switch engine\", or asks to run a task on another model/agent. Covers: in-session hand-off (shelling out to C:\\dev\\code-agent\\agent.py or using Antigravity native subagents), DeepSeek consult via MCP, and the pre-session toggle (launching Antigravity vs Claude Code). Gate state-changing or irreversible actions through /preflight first. deepseek_chat = v4-flash (fast); deepseek_reason = v4-pro (chain-of-thought)."
---

# Engine Router

Four execution engines are available. **Claude and Antigravity (Gemini) are the primary drivers** (depending on which CLI you launched) and are good at orchestration, planning, and reconciling. Use another engine deliberately — route on **stakes × complexity, not reflex.**

There are exactly **three** ways to use another engine, and they are different:

1. **In-session hand-off (via script)** — The driver delegates a chunk of work to GLM by shelling out to `agent.py`, then reconciles the result.
2. **In-session hand-off (via subagents)** — When Antigravity is the driver, it delegates work to Gemini subagents natively using the `invoke_subagent` tool.
3. **Pre-session toggle** — Launch a different CLI entirely (Claude Code vs Antigravity) or use `cc-glm.ps1`. Chosen at launch, from a terminal — not from the chat box.

## The engines

| Engine | Reach it via | Best for |
|--------|--------------|----------|
| **Antigravity (Gemini)** | Native CLI, native subagents (`invoke_subagent`) | deep Google ecosystem integration, large context windows, native subagent routing |
| **Claude** | Native CLI | orchestration, planning, reconciling, most coding |
| **GLM-5.2** (Z.ai) | `agent.py --provider zai`, or `cc-glm.ps1` | execution-heavy or cost-sensitive coding tasks |
| **DeepSeek** | `mcp__deepseek__*` tools (in-session) | heavy reasoning, stats/methods validation, second opinion |

---

## 1. In-session hand-off (The primary CLI stays the driver)

### The autonomy model
The driver sets a **clear objective + a safety boundary**, and either launches GLM with `--auto` via `agent.py`, or (if using Antigravity) spawns a native Gemini subagent. It lets the delegate run its full agentic loop end-to-end — one objective in, one report out. The driver does **not** supervise each step. Safety is enforced **in code**, not by hovering:

- **Reversible work runs free.** Reads, writes, edits, tests, builds, `git add`/`commit`/`status`/`diff` on a clean tree — GLM does these autonomously, no check-in, no per-step approval.
- **Irreversible ops auto-escalate.** `agent.py` blocks publish/discard/delete/external-side-effect commands (`git push`, `git reset --hard`, `git clean -f`, `rm -rf`, `curl -X POST`, `npm publish`, `docker push`, `kubectl apply`, `terraform apply`, registry uploads, `reg`/`schtasks`/`setx /m`, …) **even under `--auto`**. GLM gets an `ESCALATE` error and must halt and report the step as a blocker. Claude then gates that one step through `/preflight`; if it clears, re-run with `--allow-irreversible` for that execution only.

The reversibility **backstop** is a git-tracked workdir with a clean tree — any reversible change GLM makes is one `git restore`/`reset` away. That backstop is what buys the autonomy; **don't delegate into a dirty or untracked tree** (run `git stash`/commit first, or scope GLM to a fresh branch).

### Delegate a task to GLM-5.2
```
python C:/dev/code-agent/agent.py "<objective>" --provider zai --workdir <repo> --auto
```
- **`--auto` is mandatory** for delegated runs — the harness prompts via `input()` on state-changing tools, and neither the chat box nor the Bash tool can answer it, so it hangs without `--auto`.
- Hand GLM the **objective and done-condition, not a step list** — let it plan. Good: "Make `npm test` pass in `src/auth/`; don't touch other modules." Bad: "open auth.js, find the bug, edit line 42…".
- Run it for the user via Bash, then fold GLM's final report into the conversation.
- Requires `ZAI_API_KEY` (set via `setx`; a `setx` value only reaches a **freshly launched** Claude Code — restart needed after setting it).
- GLM runs through Z.ai's Anthropic-compatible endpoint (`https://api.z.ai/api/anthropic`); the harness drops the Claude-only `thinking` param automatically.

### When to auto-delegate (fire without asking)
Delegate to GLM proactively — no need to wait for "hand off" — when **either** safety condition holds:
- **Verifiable:** the repo has a detectable verification command (`package.json` script, `pytest`, `Makefile`, etc.) that can prove the work correct; **or**
- **Reversible:** the workdir is git-tracked with a clean tree, so any change is one `git restore` away.

These two cover the vast majority of coding tasks — fixes, features, refactors, mechanical sweeps of any size (no N≥10 floor, no "one module" ceiling). **Do not** auto-delegate when *neither* holds (untracked tree, no verification, and the task mutates state): keep it manual and route the state-changing step through `/preflight` first. Open-ended design work ("improve the architecture") also stays with Claude — GLM executes a defined objective, it doesn't decide product direction.

### Reconcile lightly — don't re-do the work
On GLM's report, audit the **safety invariants**, not the diff line-by-line:
1. **No unexpected escalation.** Scan the run for `ESCALATE`. If GLM reports an irreversible blocker, decide it via `/preflight` — don't accept a GLM-devised workaround.
2. **Verification ran real green** (if a command existed). GLM reports the exact command + real result; re-run it yourself only if the claim is implausible.
3. **Objective met** per the report. Spot-check one or two changed files only if something flags.

Trust the backstop: clean + git-tracked means `git diff` shows the full change and `git restore` undoes it. You're verifying the invariants held — not re-executing the task.

### If GLM hits an irreversible step
1. Run `/preflight` on the **named** irreversible action GLM reached (e.g. "push branch `x` to `origin`", "delete `./build/`") — never a glob/class.
2. **CLEARED** → re-launch the same task with `--allow-irreversible`. The guard still logs each irreversible op it runs. Do **not** leave `--allow-irreversible` on as a default — it's per-execution, and a scripted/recurring run needs its own gate each time.
3. **BLOCKED** → surface the constraint brief to the user, or substitute a reversible alternative (e.g. commit to a branch instead of pushing).

### Consult DeepSeek (reasoning / cross-check)
Use the MCP tools — the primary driver keeps driving and folds the result in.

- `deepseek_reason` (v4-pro, chain-of-thought): stats/methods validation, causal logic, multi-step proofs. Takes `prompt` + `max_tokens` **only**. Set `max_tokens ≥ 4000` — the trace and the final answer **share** the budget, so a low value returns an **empty `## Answer`**. No `system`/`temperature`.
- `deepseek_chat` (v4-flash): synthesis, extraction, translation, code review. Accepts `prompt`, `max_tokens`, `system`, `temperature`. Use `temperature: 0` for validation/extraction; set a sharp reviewer `system` prompt.
- Output is **capped at 8192 tokens** for both. Defaults truncate — always set `max_tokens` explicitly.
- Strong-fit triggers: stats/methods validation for a real decision, cross-model consensus on a critical claim, multi-step reasoning where edge cases bite.

---

## 2. Pre-session toggle (Changing the Primary CLI)

To change which engine drives the main session, launch the corresponding CLI from your terminal:
- **Antigravity**: Launch the Antigravity CLI for the native Gemini experience.
- **Claude**: Run `claude` for the default Claude Code experience.

For GLM specifically:
```powershell
C:\dev\code-agent\cc-glm.ps1          # GLM-5.2 session;  cc-glm.ps1 glm-4.6 for another model
```
- **Run it in a regular terminal (PowerShell), NOT the chat box.** It launches a *new* GLM-backed Claude Code session. It saves/restores your Anthropic env, so plain `claude` stays your untouched default.

---

## Invoke correctly — gotchas

- **Delegated `agent.py` runs:** always `--auto` (see above).
- **`--allow-irreversible`:** per-execution escape from the runtime guard; set only after `/preflight` clears the named irreversible action. The guard still logs each op it runs. Never a default.
- **`--allow-payg-fallback`:** ZAI-only, per-execution. When the Coding Plan's 5-hour quota is spent (signalled as **HTTP 200 + `rate_limit_error` code 1308**, NOT a 429), `agent.py` spills over **mid-task, no state lost** to the credit-billed **General endpoint** (`https://api.z.ai/api/paas/v4`, OpenAI format, key `ZAI_PAYG_API_KEY`, model `ZAI_PAYG_MODEL`/default `glm-5.2`) — translating the in-flight history Anthropic→OpenAI. **Spends real cash balance**; logs the switch. The Anthropic endpoint `/api/anthropic` will NOT bill credits (Coding-Plan-only) — that's why spillover must change endpoints, not just keys. Off by default; opt in per run like `--allow-irreversible`, never standing. Live-verified 2026-06-22.
- **DeepSeek `deepseek_reason`:** budget ≥ 4000 or the answer comes back empty; trace + answer share `max_tokens`.
- **Which engine is THIS session on?** Check `ANTHROPIC_BASE_URL`: contains `z.ai` → GLM; `api.anthropic.com` or unset → Claude. (Claude Code's own auth may not appear as a shell env var — the base URL is the reliable tell.)
- **`ZAI_API_KEY` via `setx`** needs a Claude Code restart to be inherited (a running process keeps its launch environment).

---

## Preflight is the safety floor

Two layers compose — **runtime** + **decision**:

- **Runtime floor (code-enforced, in `agent.py`):** the `IRREVERSIBLE` guard stops an `--auto` GLM run from executing publish/discard/delete/external-side-effect ops and escalates them back to Claude as an `ESCALATE` blocker. This runs unconditionally; it does not depend on Claude remembering to check.
- **Decision floor (`/preflight`):** how Claude decides whether an escalated (or pre-known irreversible) step may proceed. Run `/preflight` on the **named** action; on CLEARED, re-run with `--allow-irreversible`. On BLOCKED, surface the brief or substitute a reversible alternative.

Code-enforced autonomy on reversible work + a gated irreversible frontier = GLM runs free where it's safe to, and cannot escape the boundary where it isn't. See the `preflight` skill.

## Fallback

If an engine errors, say so plainly and fall back to Claude for the work (or to GLM's PAYG key via `--allow-payg-fallback`, if the block is a quota). Never let an outage block the task. Z.ai quota signals — verified live: the **5-hour Coding Plan limit** comes back as **HTTP 200 with a `rate_limit_error` body, code 1308** (NOT a 429); `code 1113` = balance exhausted. Detect by payload, not HTTP status — `agent.py`'s `is_quota_error()` does this. DeepSeek failure = timeout/empty answer.
