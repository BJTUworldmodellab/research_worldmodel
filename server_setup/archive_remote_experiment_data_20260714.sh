#!/usr/bin/env bash
set -euo pipefail

UPLOAD_ROOT="/root/autodl-tmp/github_upload"
LOG="$UPLOAD_ROOT/upload_20260714.log"
REPO_URL="https://github.com/jomify/research_worldmodel.git"
CLONE="$UPLOAD_ROOT/research_worldmodel"
ARCHIVE_REL="experiment_archive/remote_autodl_20260714"
ARCHIVE="$CLONE/$ARCHIVE_REL"
SRC_CODE="/root/RelationAwareInstructScene"
SRC_DATA="/root/autodl-tmp/RelationAwareInstructScene"

mkdir -p "$UPLOAD_ROOT"
exec > >(tee -a "$LOG") 2>&1

echo "== archive_remote_experiment_data_20260714 start =="
date -Is
hostname
whoami

if [ ! -d "$SRC_CODE" ]; then
  echo "missing source code workspace: $SRC_CODE" >&2
  exit 2
fi
if [ ! -d "$SRC_DATA" ]; then
  echo "missing source data workspace: $SRC_DATA" >&2
  exit 2
fi

if [ ! -d "$CLONE/.git" ]; then
  rm -rf "$CLONE"
  git clone "$REPO_URL" "$CLONE"
else
  git -C "$CLONE" remote set-url origin "$REPO_URL"
  git -C "$CLONE" fetch origin
fi

cd "$CLONE"
DEFAULT_BRANCH="$(git remote show origin | awk '/HEAD branch/ {print $NF}')"
if [ -z "$DEFAULT_BRANCH" ]; then
  DEFAULT_BRANCH="main"
fi
git checkout "$DEFAULT_BRANCH"
git pull --ff-only origin "$DEFAULT_BRANCH" || true

rm -rf "$ARCHIVE"
mkdir -p "$ARCHIVE"/{commonscenes_comparison,original_instructscene,logs,scripts,reports,manifests}

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    cp -a "$src" "$dst"
    echo "copied: $src -> $dst"
  else
    echo "skip missing: $src"
  fi
}

rsync_small_tree() {
  local src="$1"
  local dst="$2"
  if [ ! -d "$src" ]; then
    echo "skip missing tree: $src"
    return 0
  fi
  mkdir -p "$dst"
  rsync -a --prune-empty-dirs \
    --include='*/' \
    --include='*.json' --include='*.jsonl' --include='*.csv' --include='*.tsv' \
    --include='*.md' --include='*.txt' --include='*.log' \
    --include='*.sh' --include='*.py' --include='*.yaml' --include='*.yml' \
    --include='*.html' --include='*.png' \
    --exclude='*.pt' --exclude='*.pth' --exclude='*.safetensors' --exclude='*.ckpt' \
    --exclude='*.glb' --exclude='*.obj' --exclude='*.ply' --exclude='*.pkl' \
    --exclude='object_meshes/***' --exclude='glb/***' --exclude='3D-FRONT/***' \
    --exclude='3D-FUTURE-model/***' --exclude='3D-FUTURE-SDF/***' \
    --exclude='hf_cache/***' --exclude='__pycache__/***' \
    --exclude='*' \
    "$src"/ "$dst"/
  echo "rsynced small tree: $src -> $dst"
}

echo "== copying CommonScenes comparison data =="
rsync_small_tree "$SRC_CODE/results/commonscenes_repair_compare_20260713" "$ARCHIVE/commonscenes_comparison/results/commonscenes_repair_compare_20260713"
rsync_small_tree "$SRC_CODE/results/commonscenes_ours_repair_compare_epoch195_bedroom" "$ARCHIVE/commonscenes_comparison/results/commonscenes_ours_repair_compare_epoch195_bedroom"
rsync_small_tree "$SRC_CODE/results/commonscenes_ours_gated_t3_compare_epoch195_bedroom" "$ARCHIVE/commonscenes_comparison/results/commonscenes_ours_gated_t3_compare_epoch195_bedroom"
rsync_small_tree "$SRC_CODE/logs/commonscenes" "$ARCHIVE/commonscenes_comparison/logs/commonscenes"
rsync_small_tree "$SRC_DATA/results_generic_repair" "$ARCHIVE/commonscenes_comparison/results_generic_repair"
rsync_small_tree "$SRC_DATA/results_official_search" "$ARCHIVE/commonscenes_comparison/results_official_search_excluded_from_main"
rsync_small_tree "$SRC_DATA/results_archive_rootfs" "$ARCHIVE/commonscenes_comparison/results_archive_rootfs_summaries"
rsync_small_tree "$SRC_CODE/server_setup/commonscenes_experiments" "$ARCHIVE/commonscenes_comparison/scripts"
rsync_small_tree "$SRC_CODE/scripts" "$ARCHIVE/scripts/root_scripts"

echo "== copying original InstructScene experiment data =="
rsync_small_tree "$SRC_CODE/results/strong_baseline_a100_compare" "$ARCHIVE/original_instructscene/strong_baseline_a100_compare"
rsync_small_tree "$SRC_CODE/results/tables" "$ARCHIVE/original_instructscene/tables"
rsync_small_tree "$SRC_CODE/logs/strong_baseline_a100_compare" "$ARCHIVE/original_instructscene/logs/strong_baseline_a100_compare"
rsync_small_tree "$SRC_DATA/instructscene_out" "$ARCHIVE/original_instructscene/instructscene_out_metadata"

echo "== copying reports from code workspace if present =="
rsync_small_tree "$SRC_CODE/docs" "$ARCHIVE/reports/docs"
rsync_small_tree "$SRC_CODE/visual" "$ARCHIVE/reports/visual"

echo "== writing manifests =="
{
  echo "# Remote Large Assets Not Stored In Git"
  echo
  echo "Generated: $(date -Is)"
  echo
  echo "These assets were intentionally not committed because they are too large for normal GitHub storage or are reproducible caches/intermediates."
  echo
  echo "| remote path | size | reason | reproduction note |"
  echo "|---|---:|---|---|"
  for p in \
    "$SRC_DATA/raw_data/3D-FRONT" \
    "$SRC_DATA/hf_cache" \
    "$SRC_DATA/commonscenes_models/balancing/all" \
    "$SRC_DATA/respace_ckpts" \
    "$SRC_DATA/datasets/InstructScene" \
    "$SRC_DATA/commonscenes_FRONT/3D-FUTURE-SDF" \
    "$SRC_DATA/results_archive_rootfs" \
    "$SRC_DATA/results_generic_repair" \
    "$SRC_DATA/results_official_search"; do
    if [ -e "$p" ]; then
      size="$(du -sh "$p" | awk '{print $1}')"
      case "$p" in
        *raw_data*|*hf_cache*|*datasets*) reason="downloadable source dataset/cache" ;;
        *models*|*ckpts*) reason="large checkpoint/model weights" ;;
        *results*) reason="contains large per-scene tensors/meshes; small summaries copied separately" ;;
        *) reason="large reproducible asset" ;;
      esac
      echo "| \`$p\` | $size | $reason | keep on AutoDL or move via object storage/Git LFS if needed |"
    fi
  done
} > "$ARCHIVE/manifests/MANIFEST_REMOTE_LARGE_ASSETS.md"

{
  echo "# AutoDL Experiment Data Archive 20260714"
  echo
  echo "This archive contains small, reusable experiment evidence copied from the AutoDL machine."
  echo
  echo "## Layout"
  echo
  echo "- \`commonscenes_comparison/\`: CommonScenes comparison summaries, metrics, logs, scripts, selected PNG panels, and no-official-search / official-search separated outputs."
  echo "- \`original_instructscene/\`: original InstructScene validation summaries, tables, and logs."
  echo "- \`scripts/\`: scripts used during remote experiment execution."
  echo "- \`reports/\`: markdown/html/png reports copied from the remote workspace when present."
  echo "- \`manifests/MANIFEST_REMOTE_LARGE_ASSETS.md\`: large datasets/checkpoints/intermediates intentionally excluded from Git."
  echo
  echo "## Exclusion policy"
  echo
  echo "The archive excludes checkpoint files, raw 3D-FRONT/3D-FUTURE assets, Hugging Face cache, per-scene .pt tensors, GLB/OBJ/PLY meshes, and SDF caches. These are either public/downloadable, reproducible from scripts, or too large for normal GitHub storage."
} > "$ARCHIVE/README.md"

{
  echo "# File Inventory"
  echo
  echo "Generated: $(date -Is)"
  echo
  find "$ARCHIVE" -type f | sed "s#^$CLONE/##" | sort
} > "$ARCHIVE/manifests/FILE_INVENTORY.md"

echo "== archive size and counts =="
du -sh "$ARCHIVE"
find "$ARCHIVE" -type f | wc -l
find "$ARCHIVE/commonscenes_comparison" -type f | wc -l

echo "== git add/commit/push =="
git add "$ARCHIVE_REL"
if git diff --cached --quiet; then
  echo "No archive changes to commit."
else
  git commit -m "archive autodl experiment data 20260714"
fi

git push origin "$DEFAULT_BRANCH"

echo "== final status =="
git rev-parse HEAD
git status --short
date -Is
echo "== archive_remote_experiment_data_20260714 done =="
