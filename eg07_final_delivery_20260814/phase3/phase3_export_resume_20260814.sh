#!/usr/bin/env bash
# =============================================================================
# EG07 Phase 3 — EXPORT-ONLY resume (2026-08-14).
# Exporter fix commit e5fe837. Does NOT call relation_aware_generate_sg.py,
# does NOT re-run or overwrite the 531 generated scenes. Resumes from
# Phase 3 STEP 2 (export) onward.
# =============================================================================
set -uo pipefail

BASE=/root/autodl-tmp/relation_grounding
RUN=$BASE/eg07_formal_20260813
RT=$RUN/runtime
REPO=$BASE/code/eg07-full-export
PY=/root/miniconda3/envs/instructscene_full/bin/python
SUFFIX=floor_prior_max1.8_mesh_p2_close0.75_far1.6
GEN_COMMIT=3a167d813d74ab18df8762d57ff3b4a47789e3af
EXPORTER_FIX_COMMIT=e5fe83731bae789350574312847db5eaeacb8259
FROZEN_SHA=052ace5b295348483ce9b6110b5bd7933235424a55cc2108c966431e516829e2
LOG=$RUN/phase3_export_resume_20260814.log

exec > "$LOG" 2>&1

echo "==================================================================="
echo "PHASE3 EXPORT RESUME START $(date '+%F %T')"
echo "generation commit: $GEN_COMMIT"
echo "exporter fix commit: $EXPORTER_FIX_COMMIT"
echo "frozen config SHA: $FROZEN_SHA"
echo "==================================================================="

blocked() {
  local reason="$1"
  echo ""
  echo "FORMAL_BLOCKED_EXPORT_RESUME: $reason ($(date '+%F %T'))"
  echo "FORMAL_BLOCKED_EXPORT_RESUME: $reason" > "$RUN/export_resume_blocked_20260814.txt"
  {
    echo ""
    echo "## Phase 3 export-only resume BLOCKED ($(date '+%F %T'))"
    echo "- reason: $reason"
    echo "- status: FORMAL_BLOCKED_EXPORT_RESUME"
  } >> "$RUN/status.md"
  sync
  exit 1
}

cd "$REPO" || blocked "cannot cd to repo"
HEAD=$(git rev-parse HEAD)
echo "repo HEAD=$HEAD (expected exporter fix $EXPORTER_FIX_COMMIT)"
[ "$HEAD" = "$EXPORTER_FIX_COMMIT" ] || blocked "repo HEAD $HEAD != exporter fix commit $EXPORTER_FIX_COMMIT"

# Guard: no generation may be running / re-run.
GEN=$(pgrep -af 'relation_aware_generate_sg[.]py' 2>/dev/null || true)
[ -z "$GEN" ] || blocked "generation process running — abort (must not re-run generation)"

# Config blob SHA (must still be frozen).
CONFIG_SHA=$(git show HEAD:configs/eurographics2027/paper_main.yaml | sha256sum | awk '{print $1}')
echo "config blob SHA=$CONFIG_SHA (frozen $FROZEN_SHA)"
[ "$CONFIG_SHA" = "$FROZEN_SHA" ] || blocked "config SHA $CONFIG_SHA != $FROZEN_SHA"

BJ=$RT/out/bedroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01999/relation_aware_parsed_${SUFFIX}_eval_cfg1.0_1.0.json
LJ=$RT/out/livingroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01459/relation_aware_parsed_${SUFFIX}_eval_cfg1.0_1.0.json
DJ=$RT/out/diningroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01239/relation_aware_parsed_${SUFFIX}_eval_cfg1.0_1.0.json

echo ""
echo "--- input JSON identities (SHA-256 + per_scene; read-only) ---"
for f in "$BJ" "$LJ" "$DJ"; do
  [ -f "$f" ] || blocked "missing input JSON $f"
  echo "$(sha256sum "$f" | awk '{print $1}')  $f"
  "$PY" -c "import json;print('  per_scene=',len(json.load(open('$f'))['per_scene']))"
done

# STEP 2 — export formal_candidate.
OUTDIR=$RUN/results/eg07/formal_candidate
mkdir -p "$OUTDIR"
echo ""
echo "=== export_eg07_layouts.py (formal_candidate) $(date '+%F %T') ==="
"$PY" scripts/export_eg07_layouts.py \
  --input "$BJ" --input "$LJ" --input "$DJ" \
  --output "$OUTDIR/layouts.json" \
  --validation-report "$OUTDIR/validation.json" \
  --profile full \
  --artifact-status formal_candidate \
  --code-commit "$GEN_COMMIT" \
  --source-config "$REPO/configs/eurographics2027/paper_main.yaml" \
  --seed-policy "generator_seed=0; one layout per validation scene" \
  --generation-command "$RUN/command_record_20260814.txt" \
  --generation-log "$RUN/phase3.log" \
  --environment "$RUN/environment_record_20260814.txt" \
  || blocked "export_eg07_layouts.py failed"

# STEP 3 — independent re-validation (full profile).
echo ""
echo "=== validate_eg07_layouts.py --profile full $(date '+%F %T') ==="
"$PY" scripts/validate_eg07_layouts.py \
  --input "$OUTDIR/layouts.json" \
  --profile full \
  --report "$OUTDIR/validation_recheck.json" \
  || blocked "validate_eg07_layouts.py --profile full failed"

# STEP 4 — GO/NO-GO summary (frozen structural thresholds).
echo ""
echo "=== GO/NO-GO summary $(date '+%F %T') ==="
GONOGO_OK=1
if "$PY" "$RUN/summarize_phase3_20260814.py" > "$RUN/phase3_gonogo_20260814.txt" 2>&1; then
  cat "$RUN/phase3_gonogo_20260814.txt"
else
  cat "$RUN/phase3_gonogo_20260814.txt"
  GONOGO_OK=0
fi

# Append export-only resume section to status.md.
{
  echo ""
  echo "## Phase 3 EXPORT-ONLY RESUME ($(date '+%F %T'))"
  echo "- supersedes the 10:20:41 FORMAL_BLOCKED (exporter detect_room bug); audit record retained above"
  echo "- generation commit: $GEN_COMMIT (unchanged; no generation re-run)"
  echo "- exporter fix commit: $EXPORTER_FIX_COMMIT"
  echo "- frozen config SHA: $FROZEN_SHA (unchanged)"
  echo "- input JSON SHA-256:"
  echo "  - bedroom:    $(sha256sum "$BJ" | awk '{print $1}') (per_scene=162)"
  echo "  - livingroom: $(sha256sum "$LJ" | awk '{print $1}') (per_scene=192)"
  echo "  - diningroom: $(sha256sum "$DJ" | awk '{print $1}') (per_scene=177)"
  echo "- exported layouts: $OUTDIR/layouts.json"
  echo "- export validation: $OUTDIR/validation.json"
  echo "- independent recheck: $OUTDIR/validation_recheck.json"
  echo "- GO/NO-GO summary: $RUN/phase3_gonogo_20260814.txt"
  echo "- resume log: $LOG"
  echo ""
  cat "$RUN/phase3_gonogo_20260814.txt"
} >> "$RUN/status.md"

if [ "$GONOGO_OK" = "1" ]; then
  echo ""
  echo "FORMAL_PASS ($(date '+%F %T'))"
  echo "FORMAL_PASS" > "$RUN/pass_marker_20260814.txt"
  sync
  exit 0
else
  blocked "GO/NO-GO summary returned NO-GO"
fi
