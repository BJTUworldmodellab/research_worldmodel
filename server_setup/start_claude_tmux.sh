#!/usr/bin/env bash
set -euo pipefail

SESSION="${CLAUDE_TMUX_SESSION:-relation-claude}"
ROOT="${RELATION_ROOT:-/root/RelationAwareInstructScene}"
REPO="${ROOT}/repos/InstructScene"
PROMPT_FILE="${1:-${ROOT}/server_setup/claude_setup_prompt.md}"

if ! command -v tmux >/dev/null 2>&1; then
  echo "[fail] tmux is not installed. Run setup_relation_scene_server.sh first."
  exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "[fail] Claude Code CLI command 'claude' is not installed or not on PATH."
  echo "Install/authenticate Claude Code on the server, then rerun this script."
  exit 1
fi

mkdir -p "${ROOT}/logs"

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "[info] tmux session already exists: ${SESSION}"
  echo "Attach with: tmux attach -t ${SESSION}"
  exit 0
fi

tmux new-session -d -s "${SESSION}" -n main -c "${ROOT}"
tmux send-keys -t "${SESSION}:main" "cd ${ROOT}" C-m
tmux send-keys -t "${SESSION}:main" "bash server_setup/check_relation_scene_server.sh 2>&1 | tee logs/check_\$(date +%Y%m%d_%H%M%S).log" C-m

tmux split-window -h -t "${SESSION}:main" -c "${REPO}"
if [ -f "${PROMPT_FILE}" ]; then
  tmux send-keys -t "${SESSION}:main.1" "claude < ${PROMPT_FILE} 2>&1 | tee ${ROOT}/logs/claude_setup_\$(date +%Y%m%d_%H%M%S).log" C-m
else
  tmux send-keys -t "${SESSION}:main.1" "claude" C-m
fi

tmux split-window -v -t "${SESSION}:main.0" -c "${ROOT}"
tmux send-keys -t "${SESSION}:main.2" "watch -n 5 'nvidia-smi && echo && df -h /root /root/autodl-tmp 2>/dev/null || df -h'" C-m

tmux select-layout -t "${SESSION}:main" tiled
echo "[ok] started tmux session: ${SESSION}"
echo "Attach with: tmux attach -t ${SESSION}"

