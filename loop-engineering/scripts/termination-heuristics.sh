#!/usr/bin/env bash
# termination-heuristics.sh
# Guides the agent through the three termination gates and helps decide
# whether to continue, deliver, or escalate.
#
# Usage: bash <skill-dir>/scripts/termination-heuristics.sh
#   No arguments. Answers prompts interactively.

echo "=== Termination Heuristics ==="
echo "Three gates determine whether to stop or continue."
echo ""

FINISHED=0

# --- Gate 1: Deterministic Success ---
echo "[Gate 1/3] Deterministic Success"
echo "  Does the output artifact meet the explicit success criteria"
echo "  you defined when starting this task?"
echo -n "  (y/n) "
read -r ANSWER
if [ "$ANSWER" = "y" ] || [ "$ANSWER" = "Y" ]; then
  echo "  ✅ EXIT CONDITION MET — deterministic success"
  FINISHED=1
else
  echo "  ➡️  Not met — proceed to Gate 2"
fi
echo ""

# --- Gate 2: Heuristic Boundary ---
if [ "$FINISHED" -eq 0 ]; then
  echo "[Gate 2/3] Heuristic Boundary"
  echo "  Have you exceeded your pre-defined limits?"
  echo -n "    Iteration budget reached? (y/n) "
  read -r ANSWER
  ITER_BUDGET="$ANSWER"
  echo -n "    Token/effort budget feeling exhausted? (y/n) "
  read -r ANSWER
  EFFORT_BUDGET="$ANSWER"
  echo -n "    Time constraint reached? (y/n) "
  read -r ANSWER
  TIME_BUDGET="$ANSWER"

  if [ "$ITER_BUDGET" = "y" ] || [ "$EFFORT_BUDGET" = "y" ] || [ "$TIME_BUDGET" = "y" ]; then
    echo "  ⚠️  BOUNDARY BREACHED — at least one heuristic limit hit"
    echo "     → Deliver best-effort output or escalate to user"
    FINISHED=1
  else
    echo "  ➡️  Within bounds — proceed to Gate 3"
  fi
fi
echo ""

# --- Gate 3: Diminishing Returns ---
if [ "$FINISHED" -eq 0 ]; then
  echo "[Gate 3/3] Diminishing Returns"
  echo "  Compare your last two iterations:"
  echo -n "  Was the latest iteration materially different from the previous? (y/n) "
  read -r ANSWER
  if [ "$ANSWER" = "y" ] || [ "$ANSWER" = "Y" ]; then
    echo "  ➡️  Still making progress — continue iterating"
    echo ""
    echo "=== Result: CONTINUE ==="
    echo "All three gates allow further iteration."
    echo "Remember to re-run this check at the end of the next iteration."
    exit 0
  else
    echo "  ⚠️  DIMINISHING RETURNS — plateau detected"
    echo "     → Current approach is no longer producing meaningful improvement"
    FINISHED=1
  fi
fi
echo ""

# --- Decision ---
if [ "$FINISHED" -eq 1 ]; then
  echo "=== Result: STOP ==="
  echo "At least one termination gate triggered. Choose your action:"
  echo ""
  echo "  [D] Deliver — output is good enough, present results"
  echo "  [E] Escalate — surface partial work to user with summary of blockers"
  echo "  [R] Re-scope — renegotiate the exit contract (different deliverable)"
  echo "  [C] Continue anyway — override heuristics (requires user consent)"
  echo ""
  echo -n "Action (D/E/R/C): "
  read -r ACTION
  case "$ACTION" in
    D|d)
      echo "→ DELIVER: Summarize what was accomplished and present the output."
      exit 10
      ;;
    E|e)
      echo "→ ESCALATE: Surface to user with: what was tried, what was achieved,"
      echo "  what blocked completion, and what alternatives exist."
      exit 11
      ;;
    R|r)
      echo "→ RE-SCOPE: Propose a revised exit contract to the user."
      exit 12
      ;;
    C|c)
      echo "→ CONTINUE (override): Only valid with explicit user approval."
      echo "  State the override request: 'Termination heuristics triggered but"
      echo "  I recommend continuing because [reason]. Do you approve?'"
      exit 13
      ;;
    *)
      echo "→ Unknown action. Defaulting to DELIVER."
      exit 10
      ;;
  esac
fi
