#!/bin/bash
# =============================================================================
# ci_hook.sh — Non-RTL Parameter DB CI Integration Hook
# =============================================================================
# Part of the Non-RTL Parameter DB update workflow
# (see ../docs/nonrtl_db_update_workflow.html)
#
# This script is called by CI (GitHub Actions / GitLab CI / Jenkins) on every
# commit. It detects changes to .prm files and memory map XLSX files, then
# triggers the gap analyzer to check if the JSON database is out of sync.
#
# Integration:
#   GitHub Actions:
#     - name: Check Non-RTL DB Sync
#       run: tools/nonrtl-db-workflow/ci_hook.sh
#
#   GitLab CI:
#     nonrtl-db-check:
#       script: tools/nonrtl-db-workflow/ci_hook.sh
#       allow_failure: true
#
# Exit codes:
#   0 — DB in sync, no gaps
#   1 — Gaps detected (contribution YAML generated, PR auto-opened)
#   Non-zero other — Script error
# =============================================================================

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────
SPEC_REPO="vlsi/ChipNexus/spec-repo"
DB_PATH="vlsi/ChipNexus/nonrtl-params-db/nonrtl_param_db.json"
CONTRIB_DIR="vlsi/ChipNexus/nonrtl-params-db/db-contributions"
GAP_ANALYZER="vlsi/ChipNexus/tools/nonrtl-db-workflow/gap_analyzer.py"
SCHEMA_VALIDATOR="vlsi/ChipNexus/tools/nonrtl-db-workflow/schema_validator.py"
CHIP_PREFIX="${CHIP_PREFIX:-MCU_X}"

# Ensure we're in the repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

echo "============================================================"
echo "  Non-RTL Parameter DB CI Hook"
echo "  Chip Prefix: $CHIP_PREFIX"
echo "============================================================"

# ── Step 1: Detect changed files ──────────────────────────────────
CHANGED_FILES=""
BRANCH="${GITHUB_HEAD_REF:-${CI_MERGE_REQUEST_SOURCE_BRANCH_NAME:-HEAD}}"
TARGET_BRANCH="${GITHUB_BASE_REF:-${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-main}}"

# Detect changes between current commit and target branch
if git rev-parse "$TARGET_BRANCH" >/dev/null 2>&1; then
    CHANGED_FILES=$(git diff --name-only "origin/$TARGET_BRANCH...$BRANCH" 2>/dev/null || git diff --name-only HEAD~1 2>/dev/null || echo "")
else
    CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null || echo "")
fi

if [ -z "$CHANGED_FILES" ]; then
    echo "No changed files detected. Checking full DB sync..."
elif echo "$CHANGED_FILES" | grep -qE '\.(prm|xlsx)$'; then
    echo "🔍  .prm or .xlsx changes detected — running gap analysis..."
    echo "    Changed files:"
    echo "$CHANGED_FILES" | grep -E '\.(prm|xlsx)$' | sed 's/^/      /'
else
    echo "No .prm or .xlsx changes in this commit. Skipping gap analysis."
    exit 0
fi

# ── Step 2: Run gap analyzer ──────────────────────────────────────
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTRIB_FILE="$CONTRIB_DIR/contribution_${CHIP_PREFIX}_${TIMESTAMP}.yaml"

mkdir -p "$CONTRIB_DIR"

echo ""
echo "📊  Running gap analyzer..."

python3 "$GAP_ANALYZER" \
    --spec-repo "$SPEC_REPO" \
    --db "$DB_PATH" \
    --chip-prefix "$CHIP_PREFIX" \
    --output-contribution "$CONTRIB_FILE" \
    || GAP_EXIT_CODE=$?

# ── Step 3: Process results ───────────────────────────────────────
if [ "${GAP_EXIT_CODE:-0}" -eq 1 ]; then
    echo ""
    echo "⚠️   Gaps detected between .prm definitions and Non-RTL Parameter DB!"
    echo ""
    echo "    Contribution YAML generated:"
    echo "      $CONTRIB_FILE"
    echo ""

    # Run schema validation on the contribution
    echo "🔬  Running schema validation..."
    if python3 "$SCHEMA_VALIDATOR" \
        --contribution "$CONTRIB_FILE" \
        --db "$DB_PATH"; then
        echo "✅  Contribution YAML passed schema validation."
    else
        echo "❌  Contribution YAML failed schema validation!"
        echo "    Please fix the following errors before merging:"
        echo ""
        exit 1
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  NEXT STEPS:"
    echo "  1. Review the contribution YAML at: $CONTRIB_FILE"
    echo "  2. Fill in missing parameter values"
    echo "  3. Create a PR from branch: db-contributions/${CHIP_PREFIX}-${TIMESTAMP}"
    echo "  4. After review + schema validation passes, merge into DB"
    echo ""
    echo "  Quick commands:"
    echo "    cat $CONTRIB_FILE"
    echo "    git checkout -b db-contributions/${CHIP_PREFIX}-${TIMESTAMP}"
    echo "    git add $CONTRIB_FILE"
    echo "    git commit -m 'db: add contribution slots for $CHIP_PREFIX gaps'"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    exit 1  # Fail CI to prompt action
elif [ "${GAP_EXIT_CODE:-0}" -eq 0 ]; then
    echo ""
    echo "✅  Non-RTL Parameter DB is in sync with .prm definitions."
    echo "    No gaps detected for chip prefix: $CHIP_PREFIX"

    # Validate the database integrity anyway
    echo ""
    echo "🔬  Running database integrity check..."
    python3 "$SCHEMA_VALIDATOR" --db "$DB_PATH" --validate-db

    echo ""
    echo "✅  CI hook completed successfully."
    exit 0
else
    echo ""
    echo "❌  Gap analyzer failed with unexpected exit code: ${GAP_EXIT_CODE:-unknown}"
    exit 2
fi