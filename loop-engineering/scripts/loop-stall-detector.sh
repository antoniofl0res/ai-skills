#!/usr/bin/env bash
# loop-stall-detector.sh
# Checks for three stall signatures in agentic loops:
#   1. Identical-repeat — same tool call with same arguments
#   2. Oscillation — alternating between two states without convergence
#   3. Progress-plateau — no net change in output quality over iterations
#
# This is a SELF-DIAGNOSIS tool — the agent answers questions about its own state.
#
# Usage: bash <skill-dir>/scripts/loop-stall-detector.sh
#   No arguments. Answers prompts interactively or accepts pre-answered flags.

echo "=== Loop Stall Detector ==="
echo ""

STALL_FOUND=0

# --- Check 1: Identical-repeat ---
echo "[1/3] Identical-repeat check"
echo "  Have you issued the same tool call (same command, same arguments)"
echo -n "  more than once in your last 3 actions? (y/n) "
read -r ANSWER
if [ "$ANSWER" = "y" ] || [ "$ANSWER" = "Y" ]; then
  echo "  ⚠️  STALL SIGNATURE: Identical-repeat detected"
  echo "     → This action is producing the same output each time."
  echo "     → Repeating it will not produce a different result."
  echo "     → Action needed: change approach or abort this sub-task."
  STALL_FOUND=1
else
  echo "  ✅ No identical-repeat detected"
fi
echo ""

# --- Check 2: Oscillation ---
echo "[2/3] Oscillation check"
echo "  Are you alternating between two approaches/states without"
echo -n "  converging toward your goal? (y/n) "
read -r ANSWER
if [ "$ANSWER" = "y" ] || [ "$ANSWER" = "Y" ]; then
  echo "  ⚠️  STALL SIGNATURE: Oscillation detected"
  echo "     → You're cycling: A → B → A → B with no progress"
  echo "     → Neither approach is working. You need a third option."
  echo "     → Action needed: synthesize what you learned from both and"
  echo "       design a new strategy that incorporates the best of each."
  STALL_FOUND=1
else
  echo "  ✅ No oscillation detected"
fi
echo ""

# --- Check 3: Progress-plateau ---
echo "[3/3] Progress-plateau check"
echo "  Have your last 2-3 iterations produced <10% meaningful change"
echo -n "  in the output or state? (y/n) "
read -r ANSWER
if [ "$ANSWER" = "y" ] || [ "$ANSWER" = "Y" ]; then
  echo "  ⚠️  STALL SIGNATURE: Progress-plateau detected"
  echo "     → You're past the point of diminishing returns."
  echo "     → Each new iteration costs tokens but adds little value."
  echo "     → Action needed: deliver what you have or escalate to user."
  STALL_FOUND=1
else
  echo "  ✅ No plateau detected"
fi
echo ""

# --- Summary ---
echo "=== Result ==="
if [ "$STALL_FOUND" -eq 1 ]; then
  echo "❌ STALL DETECTED — at least one stall signature found."
  echo ""
  echo "Recommended actions (in order):"
  echo "  1. STOP current approach — do not repeat the same pattern"
  echo "  2. DIAGNOSE root cause: is this a tool issue, approach issue,"
  echo "     or a goal that's harder than expected?"
  echo "  3. REVERT to last known-good checkpoint (Principle 3)"
  echo "  4. REDESIGN strategy or ESCALATE to the user"
  echo ""
  echo "  If you cannot make progress after redesign, escalate with:"
  echo "    - What was tried (3 attempts max)"
  echo "    - What failed (specific error or stall signature)"
  echo "    - What alternatives remain"
  exit 1
else
  echo "✅ No stall signatures detected — proceed with confidence"
  echo ""
  echo "Optional optimization: run termination-heuristics.sh to"
  echo "confirm you're still in the productive zone."
  exit 0
fi
