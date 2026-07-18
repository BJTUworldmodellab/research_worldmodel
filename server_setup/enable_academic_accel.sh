#!/usr/bin/env bash
set -euo pipefail

mkdir -p /root/.pip /root/.config/pip /root/.conda

cat > /root/.pip/pip.conf <<'PIP'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
extra-index-url = https://pypi.org/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
retries = 10
timeout = 120
PIP
cp /root/.pip/pip.conf /root/.config/pip/pip.conf

cat > /root/.condarc <<'CONDA'
channels:
  - defaults
show_channel_urls: true
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  nvidia: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
CONDA

cat > /root/RelationAwareInstructScene/activate_accel.sh <<'ACCEL'
#!/usr/bin/env bash
if [ -f /etc/network_turbo ]; then
  source /etc/network_turbo
fi
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
export PIP_EXTRA_INDEX_URL="${PIP_EXTRA_INDEX_URL:-https://pypi.org/simple}"
export GIT_LFS_SKIP_SMUDGE="${GIT_LFS_SKIP_SMUDGE:-0}"
ACCEL
chmod +x /root/RelationAwareInstructScene/activate_accel.sh

echo '[ok] academic acceleration config written'
echo 'Use: source /root/RelationAwareInstructScene/activate_accel.sh'
