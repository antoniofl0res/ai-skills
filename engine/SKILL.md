---
name: engine
description: "Route work between execution engines — Claude (default driver), GLM-5.2 via Z.ai, and DeepSeek — and invoke each correctly. ALWAYS trigger when the user says /engine, \"delegate to GLM\", \"hand off to glm\", \"run this on glm\", \"use deepseek\", \"send to deepseek\", \"deepseek review\", \"cross-check\", \"multi-model\", \"which engine/model should run this\", \"switch engine\", or asks to run a task on another model/agent. Covers three things: in-session hand-off (Claude stays the driver and shells out to the standalone agent at C:\\dev\\code-agent\\agent.py), DeepSeek consult via MCP, and the pre-session toggle (cc-glm.ps1, run in a terminal). Gate state-changing or irreversible actions through /preflight first. deepseek_chat = v4-flash (fast); deepseek_reason = v4-pro (chain-of-thought)."
---

# Engine Router

Three execution engines are available. **Claude is the default driver** of this session and is good at orchestration, planning, and reconciling. Use another engine deliberately — route on **stakes × complexity, not reflex.**

There are exactly **two** ways to use another engine, and they are different:

1. **In-session hand-off** — Claude stays the driver and delegates a chunk of work to GLM or DeepSeek, then reconciles the result. Available inside any session.
2. **Pre-session toggle** — launch a whole Claude Code session that *is* GLM. Chosen at launch, from a terminal — not from the chat box.

## The engines

| Engine | Reach it via | Best for |
|--------|--------------|----------|
| **Claude** (default) | this session | orchestration, planning, reconciling, most coding |
| **GLM-5.2** (Z.ai) | `agent.py --provider zai`, or `cc-glm.ps1` | execution-heavy or cost-sensitive coding tasks |
| **DeepSeek** | `mcp__deepseek__*` tools (in-session) | heavy reasoning, stats/methods validation, second opinion |

---

## 1. In-session hand-off (Claude stays the driver)

### Delegate a coding task to GLM-5.2
Claude shells out to the standalone agent; GLM runs the agentic loop and reports back.

```
python C:/dev/code-agent/agent.py "<bounded task>" --provider zai --workdir <repo> --auto
```

- **`--auto` is mandatory** for delegated/non-interactive runs — the harness prompts for confirmation via `input()` on state-changing tools, and neither the chat box nor the Bash tool can answer it, so it hangs without `--auto`.
- Run it for the user via Bash, then reconcile the agent's final report into the conversation.
- Requires `ZAI_API_KEY` (set via `setx`; a `setx` value only reaches a **freshly launched** Claude Code — restart needed after setting it).
- GLM runs through Z.ai's Anthropic-compatible endpoint (`https://api.z.ai/api/anthropic`); the harness drops the Claude-only `thinking` param automatically.

### Consult DeepSeek (reasoning / cross-check)
Use the MCP tools — Claude keeps driving and folds the result in.

- `deepseek_reason` (v4-pro, chain-of-thought): stats/methods validation, causal logic, multi-step proofs. Takes `prompt` + `max_tokens` **only**. Set `max_tokens ≥ 4000` — the trace and the final answer **share** the budget, so a low value returns an **empty `## Answer`**. No `system`/`temperature`.
- `deepseek_chat` (v4-flash): synthesis, extraction, translation, code review. Accepts `prompt`, `max_tokens`, `system`, `temperature`. Use `temperature: 0` for validation/extraction; set a sharp reviewer `system` prompt.
- Output is **capped at 8192 tokens** for both. Defaults truncate — always set `max_tokens` explicitly.
- Strong-fit triggers: stats/methods validation for a real decision, cross-model consensus on a critical claim, multi-step reasoning where edge cases bite.

---

## 2. Pre-session toggle (the whole session runs on GLM)

```
C:\dev\code-agent\cc-glm.ps1          # GLM-5.2 session;  cc-glm.ps1 glm-4.6 for another model
```

- **Run it in a regular terminal (PowerShell), NOT the chat box.** It launches a *new* GLM-backed Claude Code session; it can't be run from inside an existing session.
- It saves/restores your Anthropic env, so plain `claude` stays your untouched default.
- This is a "how you start Claude Code," not a command you run inside it.

---

## Invoke correctly — gotchas

- **Delegated `agent.py` runs:** always `--auto` (see above).
- **`cc-glm.ps1`:** terminal only; never from the chat box.
- **DeepSeek `deepseek_reason`:** budget ≥ 4000 or the answer comes back empty; trace + answer share `max_tokens`.
- **Which engine is THIS session on?** Check `ANTHROPIC_BASE_URL`: contains `z.ai` → GLM; `api.anthropic.com` or unset → Claude. (Claude Code's own auth may not appear as a shell env var — the base URL is the reliable tell.)
- **`ZAI_API_KEY` via `setx`** needs a Claude Code restart to be inherited (a running process keeps its launch environment).

---

## Preflight first

Before any **state-changing or irreversible** action an engine performs — file/dir deletion, `git push`/`reset --hard`, sending email/messages/PRs, overwriting files with uncommitted changes, external POST/PUT/DELETE — run the **`/preflight`** gate-check. This matters *more* for delegated `--auto` runs, which skip the harness's own confirmations. See the `preflight` skill.

## Fallback

If an engine errors (GLM `429 code 1113` = Z.ai balance exhausted; DeepSeek timeout/empty), say so plainly and fall back to Claude for the work. Never let an outage block the task.
