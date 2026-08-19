#!/usr/bin/env bash
# =============================================================================
# EG07 Phase 3 — formal 531-scene frozen rerun (2026-08-14).
#
# Sequential (no parallel GPU), no rendering, no mesh copying. Uses the exact
# checkpoints/seed/relation_source/repair_strategy/mesh_collision and frozen
# params as the passing smoke; only n_scenes switches 1 -> 0 (full post-filter).
#
# Terminal markers (greppable):
#   FORMAL_PASS     -> all 3 rooms + export + validate + GO/NO-GO passed
#   FORMAL_BLOCKED  -> any stage failed
# =============================================================================
set -uo pipefail

BASE=/root/autodl-tmp/relation_grounding
RUN=$BASE/eg07_formal_20260813
RT=$RUN/runtime
REPO=$BASE/code/eg07-full-export
PY=/root/miniconda3/envs/instructscene_full/bin/python
SUFFIX=floor_prior_max1.8_mesh_p2_close0.75_far1.6
CODE_COMMIT=3a167d813d74ab18df8762d57ff3b4a47789e3af
FROZEN_SHA=052ace5b295348483ce9b6110b5bd7933235424a55cc2108c966431e516829e2
MAIN_LOG=$RUN/phase3.log

export NLTK_DATA=$BASE/cache/nltk_data
export PYTHONPATH=$RT
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

exec >> "$MAIN_LOG" 2>&1
echo "==================================================================="
echo "PHASE3 FORMAL START $(date '+%F %T')"
echo "==================================================================="

blocked() {
  local reason="$1"
  echo ""
  echo "FORMAL_BLOCKED: $reason ($(date '+%F %T'))"
  echo "FORMAL_BLOCKED: $reason" > "$RUN/blocked_reason_20260814.txt"
  {
    echo ""
    echo "## Phase 3 BLOCKED ($(date '+%F %T'))"
    echo "- reason: $reason"
    echo "- main log: $MAIN_LOG"
    echo "- status: FORMAL_BLOCKED"
  } >> "$RUN/status.md"
  sync
  exit 1
}

# ---------------------------------------------------------------------------
# Step 0 — preflight (no re-download / re-extract / re-smoke)
# ---------------------------------------------------------------------------
echo ""
echo "=== STEP 0 preflight $(date '+%F %T') ==="

# git identity + clean tree
cd "$REPO" || blocked "cannot cd to repo"
HEAD=$(git rev-parse HEAD)
echo "git HEAD=$HEAD (expected $CODE_COMMIT)"
[ "$HEAD" = "$CODE_COMMIT" ] || blocked "git HEAD $HEAD != $CODE_COMMIT"
DIRTY=$(git status --porcelain -- configs/eurographics2027/paper_main.yaml results/relation_aware_generate_sg.py scripts/export_eg07_layouts.py scripts/validate_eg07_layouts.py)
[ -z "$DIRTY" ] || blocked "frozen files dirty: $DIRTY"
CONFIG_SHA=$(git show HEAD:configs/eurographics2027/paper_main.yaml | sha256sum | awk '{print $1}')
echo "config blob sha=$CONFIG_SHA (expected $FROZEN_SHA)"
[ "$CONFIG_SHA" = "$FROZEN_SHA" ] || blocked "config sha $CONFIG_SHA != $FROZEN_SHA"

# residual generation/download processes (narrow .py match to avoid self-match
# with any launcher command line; exclude this script's own PID)
RESID=$(pgrep -af 'relation_aware_generate_sg\.py|aria2c' 2>/dev/null | grep -vF "$BASHPID" || true)
[ -z "$RESID" ] || blocked "residual process detected: $RESID"
echo "no residual generation/download processes"

# asset + checkpoint symlink resolution
OBJS=$(find "$BASE/eg07_assets/3D-FRONT" -name 'raw_model.obj' 2>/dev/null | wc -l)
echo "raw_model.obj count=$OBJS (expected 4232)"
[ "$OBJS" = "4232" ] || blocked "raw_model.obj count $OBJS != 4232"
for tag in bedroom_sgdiffusion_vq_objfeat bedroom_sg2scdiffusion_objfeat livingroom_sgdiffusion_vq_objfeat livingroom_sg2scdiffusion_objfeat diningroom_sgdiffusion_vq_objfeat diningroom_sg2scdiffusion_objfeat threedfront_objfeat_vqvae; do
  resolved=$(readlink -f "$RT/out/$tag/checkpoints/"*.pth 2>/dev/null | head -1)
  [ -n "$resolved" ] && [ -f "$resolved" ] || blocked "checkpoint missing for $tag"
  echo "ckpt $tag -> $resolved"
done

# disk + GPU
df -h /root/autodl-tmp | tail -1
nvidia-smi --query-gpu=name,memory.free --format=csv,noheader
[ "$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)" -gt 10000 ] \
  || blocked "GPU free VRAM < 10 GiB"

echo "PREFLIGHT_OK $(date '+%F %T')"

# ---------------------------------------------------------------------------
# Step 1 — sequential three-room full generation + per-room validation
# ---------------------------------------------------------------------------
ALL_OK=1
for pair in "bedroom 1999 162" "livingroom 1459 192" "diningroom 1239 177"; do
  set -- $pair; R=$1; E=$2; TARGET=$3
  echo ""
  echo "--- FORMAL RUN $R epoch=$E target=$TARGET $(date '+%F %T') ---"
  if ! bash "$RUN/run_formal_room_20260814.sh" "$R" "$E"; then
    echo "FORMAL_RUN_FAIL $R"
    ALL_OK=0
    continue
  fi
  if ! "$PY" "$RUN/verify_formal_room_20260814.py" "$R" "$E" "$TARGET" > "$RUN/verify_formal_${R}_20260814.log" 2>&1; then
    echo "FORMAL_VERIFY_FAIL $R"
    cat "$RUN/verify_formal_${R}_20260814.log"
    ALL_OK=0
    continue
  fi
  cat "$RUN/verify_formal_${R}_20260814.log"
  {
    echo ""
    echo "## Phase 3 room DONE — $R ($(date '+%F %T'))"
    echo "- target: $TARGET, epoch: $E, output_suffix: $SUFFIX"
    echo "- generation log: $RUN/formal_${R}_20260814.log"
    echo "- verification log: $RUN/verify_formal_${R}_20260814.log"
    echo "- result JSON: $RT/out/${R}_sgdiffusion_vq_objfeat/generated_scenes/epoch_$(printf %05d $E)/relation_aware_parsed_${SUFFIX}_eval_cfg1.0_1.0.json"
  } >> "$RUN/status.md"
  echo "FORMAL_ROOM_OK $R"
done

[ "$ALL_OK" = "1" ] || blocked "one or more rooms failed generation/verification"

# ---------------------------------------------------------------------------
# Step 2 — export normalized formal_candidate artifact
# ---------------------------------------------------------------------------
echo ""
echo "=== STEP 2 export $(date '+%F %T') ==="
OUTDIR=$RUN/results/eg07/formal_candidate
mkdir -p "$OUTDIR"
BJ=$RT/out/bedroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01999/relation_aware_parsed_${SUFFIX}_eval_cfg1.0_1.0.json
LJ=$RT/out/livingroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01459/relation_aware_parsed_${SUFFIX}_eval_cfg1.0_1.0.json
DJ=$RT/out/diningroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01239/relation_aware_parsed_${SUFFIX}_eval_cfg1.0_1.0.json

cd "$REPO" || blocked "cannot cd to repo for export"
"$PY" scripts/export_eg07_layouts.py \
  --input "$BJ" --input "$LJ" --input "$DJ" \
  --output "$OUTDIR/layouts.json" \
  --validation-report "$OUTDIR/validation.json" \
  --profile full \
  --artifact-status formal_candidate \
  --code-commit "$CODE_COMMIT" \
  --source-config "$REPO/configs/eurographics2027/paper_main.yaml" \
  --seed-policy "generator_seed=0; one layout per validation scene" \
  --generation-command "$RUN/command_record_20260814.txt" \
  --generation-log "$MAIN_LOG" \
  --environment "$RUN/environment_record_20260814.txt" \
  || blocked "export_eg07_layouts.py failed"

# ---------------------------------------------------------------------------
# Step 3 — independent re-validation (full profile)
# ---------------------------------------------------------------------------
echo ""
echo "=== STEP 3 independent validate $(date '+%F %T') ==="
"$PY" scripts/validate_eg07_layouts.py \
  --input "$OUTDIR/layouts.json" \
  --profile full \
  --report "$OUTDIR/validation_recheck.json" \
  || blocked "validate_eg07_layouts.py --profile full failed"

# ---------------------------------------------------------------------------
# Step 4 — GO/NO-GO summary table
# ---------------------------------------------------------------------------
echo ""
echo "=== STEP 4 GO/NO-GO summary $(date '+%F %T') ==="
if "$PY" "$RUN/summarize_phase3_20260814.py" > "$RUN/phase3_gonogo_20260814.txt" 2>&1; then
  cat "$RUN/phase3_gonogo_20260814.txt"
  {
    echo ""
    echo "## Phase 3 COMPLETE — FORMAL_PASS ($(date '+%F %T'))"
    echo "- exported layouts: $OUTDIR/layouts.json"
    echo "- export validation: $OUTDIR/validation.json"
    echo "- independent recheck: $OUTDIR/validation_recheck.json"
    echo "- GO/NO-GO summary: $RUN/phase3_gonogo_20260814.txt"
    echo "- command record: $RUN/command_record_20260814.txt"
    echo "- environment record: $RUN/environment_record_20260814.txt"
    echo "- main log: $MAIN_LOG"
    echo ""
    cat "$RUN/phase3_gonogo_20260814.txt"
  } >> "$RUN/status.md"
else
  cat "$RUN/phase3_gonogo_20260814.txt"
  blocked "GO/NO-GO summary returned NO-GO"
fi

echo ""
echo "==================================================================="
echo "FORMAL_PASS ($(date '+%F %T'))"
echo "==================================================================="
echo "FORMAL_PASS" > "$RUN/pass_marker_20260814.txt"
sync
exit 0
