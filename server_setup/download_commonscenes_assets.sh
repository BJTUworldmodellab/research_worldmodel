#!/usr/bin/env bash
set -euo pipefail

ROOT=/root/RelationAwareInstructScene
ASSET_DIR=/root/autodl-tmp/RelationAwareInstructScene/commonscenes_assets
LOG_DIR=$ROOT/logs/commonscenes
TS=$(date +%Y%m%d_%H%M%S)
LOG=$LOG_DIR/download_assets_$TS.log

mkdir -p "$ASSET_DIR" "$LOG_DIR"
exec > >(tee -a "$LOG") 2>&1

echo "START=$(date -Is)"
echo "ASSET_DIR=$ASSET_DIR"
echo "LOG=$LOG"
df -h /root/autodl-tmp

download() {
  local url="$1"
  local out="$2"
  echo "DOWNLOAD $url -> $out"
  if command -v curl >/dev/null 2>&1; then
    curl -L --retry 5 --retry-delay 10 -C - -o "$out" "$url"
  else
    wget -c -O "$out" "$url"
  fi
  ls -lh "$out"
}

download "https://www.campar.in.tum.de/public_datasets/2023_commonscenes_zhai/SG_FRONT.zip" "$ASSET_DIR/SG_FRONT.zip"
download "https://www.campar.in.tum.de/public_datasets/2023_commonscenes_zhai/bbox.zip" "$ASSET_DIR/bbox.zip"
download "https://www.campar.in.tum.de/public_datasets/2023_commonscenes_zhai/vqvae_threedfront_best.pth" "$ASSET_DIR/vqvae_threedfront_best.pth"
download "https://www.campar.in.tum.de/public_datasets/2023_commonscenes_zhai/balancing.zip" "$ASSET_DIR/balancing.zip"

echo "ZIP_LIST_BALANCING"
unzip -l "$ASSET_DIR/balancing.zip" | sed -n '1,120p'
echo "SUMMARY"
du -sh "$ASSET_DIR"
df -h /root/autodl-tmp
echo "END=$(date -Is)"
