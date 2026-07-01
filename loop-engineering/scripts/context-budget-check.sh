#!/usr/bin/env bash
# context-budget-check.sh
# Estimates whether the current working directory suggests healthy context state
# for further iterations. Looks for accumulation artifacts, large file outputs,
# and iteration depth signals.
#
# Usage: bash <skill-dir>/scripts/context-budget-check.sh [target-dir]
#   target-dir: directory to analyze (default: current working directory)

TARGET="${1:-.}"
if [ ! -d "$TARGET" ]; then
  echo "ERROR: '$TARGET' is not a directory"
  exit 1
fi

echo "=== Context Budget Check ==="
echo "Target: $(cd "$TARGET" && pwd)"
echo ""

# 1. Count files that look like iteration/output artifacts
ARTIFACT_COUNT=$(find "$TARGET" -maxdepth 3 -type f \( -name "*.log" -o -name "*.tmp" -o -name "*.out" -o -name "output*" -o -name "result*" -o -name "iteration*" -o -name "*.json" \) 2>/dev/null | wc -l)
echo "[Files] Artifact files: $ARTIFACT_COUNT"
if [ "$ARTIFACT_COUNT" -gt 20 ]; then
  echo "  ⚠️  High artifact count — consider cleaning up or summarizing intermediates"
elif [ "$ARTIFACT_COUNT" -gt 10 ]; then
  echo "  📊 Moderate accumulation — manageable but watch it"
else
  echo "  ✅ Low artifact count"
fi

# 2. Check for large files (>500KB) that may bloat context if read
LARGE_FILES=$(find "$TARGET" -maxdepth 3 -type f -size +500k 2>/dev/null | head -10)
LARGE_COUNT=$(echo "$LARGE_FILES" | grep -c . 2>/dev/null || echo 0)
echo ""
echo "[Size] Files >500KB: $LARGE_COUNT"
if [ "$LARGE_COUNT" -gt 0 ]; then
  echo "  ⚠️  Large files present — avoid reading them whole into context:"
  echo "$LARGE_FILES" | while IFS= read -r f; do
    SIZE=$(du -h "$f" 2>/dev/null | cut -f1)
    echo "       $SIZE  $(basename "$f")"
  done
else
  echo "  ✅ No oversized files"
fi

# 3. Count subdirectories as a proxy for iteration depth
SUBDIR_COUNT=$(find "$TARGET" -maxdepth 1 -type d | wc -l)
# subtract . and ..
SUBDIR_COUNT=$((SUBDIR_COUNT - 2))
echo ""
echo "[Depth] Subdirectories: $SUBDIR_COUNT"
if [ "$SUBDIR_COUNT" -gt 10 ]; then
  echo "  ⚠️  Many subdirectories — suggests many iterations; consider if you're plateaued"
elif [ "$SUBDIR_COUNT" -gt 5 ]; then
  echo "  📊 Moderate depth"
else
  echo "  ✅ Shallow structure"
fi

# 4. Total directory size
TOTAL_SIZE=$(du -sh "$TARGET" 2>/dev/null | cut -f1)
echo ""
echo "[Volume] Total workspace size: $TOTAL_SIZE"

# 5. Overall verdict
echo ""
echo "=== Verdict ==="
HEALTH_SCORE=0
[ "$ARTIFACT_COUNT" -le 20 ] && HEALTH_SCORE=$((HEALTH_SCORE + 1))
[ "$ARTIFACT_COUNT" -le 10 ] && HEALTH_SCORE=$((HEALTH_SCORE + 1))
[ "$LARGE_COUNT" -eq 0 ] && HEALTH_SCORE=$((HEALTH_SCORE + 1))
[ "$SUBDIR_COUNT" -le 10 ] && HEALTH_SCORE=$((HEALTH_SCORE + 1))
[ "$SUBDIR_COUNT" -le 5 ] && HEALTH_SCORE=$((HEALTH_SCORE + 1))

if [ "$HEALTH_SCORE" -ge 4 ]; then
  echo "✅ Healthy — context state looks manageable, proceed with confidence"
elif [ "$HEALTH_SCORE" -ge 2 ]; then
  echo "⚠️  Fair — some accumulation, consider summarizing checkpoints"
else
  echo "❌ Bloated — high artifact/depth accumulation. Before continuing:"
  echo "   1. Summarize completed sub-tasks to 1-3 lines each"
  echo "   2. Archive or clean intermediate artifacts"
  echo "   3. Verify your exit contract — are you close to done?"
fi
