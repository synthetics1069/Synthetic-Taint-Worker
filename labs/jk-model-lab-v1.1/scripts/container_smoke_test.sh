#!/usr/bin/env bash
set -euo pipefail

smoke_root="$(mktemp -d)"
server_pid=""
sentinel=""

cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  rm -f /opt/ComfyUI/models/diffusers/Kolors
  if [[ -n "$sentinel" ]]; then
    rm -f "$sentinel"
  fi
  rm -rf "$smoke_root"
}
trap cleanup EXIT

# Reproduce the production condition: the parent exists and contains content.
mkdir -p /opt/ComfyUI/models/diffusers
sentinel=/opt/ComfyUI/models/diffusers/.preexisting-content
touch "$sentinel"

export MODEL_LAB_ROOT="$smoke_root/model-lab"
export COMFYUI_ROOT=/opt/ComfyUI

assert_persistence_layout() {
  test -f "$sentinel"
  test -L /opt/ComfyUI/models/diffusers/Kolors
  test "$(readlink /opt/ComfyUI/models/diffusers/Kolors)" = \
    "$MODEL_LAB_ROOT/models/diffusers/Kolors"
}

run_comfyui() {
  local pass_name="$1"
  local log_file="$smoke_root/comfyui-$pass_name.log"
  local healthy=0

  python -u /opt/ComfyUI/main.py \
    --cpu \
    --listen 127.0.0.1 \
    --port 18188 \
    --input-directory "$MODEL_LAB_ROOT/input" \
    --output-directory "$MODEL_LAB_ROOT/output" \
    --user-directory "$MODEL_LAB_ROOT/user" \
    --extra-model-paths-config /opt/model-lab/extra_model_paths.yaml \
    --preview-method none >"$log_file" 2>&1 &
  server_pid=$!

  for _ in $(seq 1 120); do
    if python -c 'import json, urllib.request; data=json.load(urllib.request.urlopen("http://127.0.0.1:18188/system_stats", timeout=2)); assert "system" in data' 2>/dev/null; then
      healthy=1
      break
    fi
    if ! kill -0 "$server_pid" 2>/dev/null; then
      break
    fi
    sleep 1
  done

  if [[ "$healthy" != "1" ]]; then
    cat "$log_file" >&2
    echo "ComfyUI $pass_name start did not return a valid /system_stats response." >&2
    exit 1
  fi

  if grep -q "IMPORT FAILED" "$log_file"; then
    cat "$log_file" >&2
    echo "A ComfyUI custom node failed to import during the $pass_name start." >&2
    exit 1
  fi

  grep -q "ComfyUI-KwaiKolorsWrapper" "$log_file"
  kill "$server_pid"
  wait "$server_pid" 2>/dev/null || true
  server_pid=""
}

# Exercise the same sequence as two separate container starts: initialize,
# boot to a real HTTP response, stop cleanly, then repeat against persisted data.
/opt/model-lab/scripts/initialize.sh
assert_persistence_layout
run_comfyui cold

/opt/model-lab/scripts/initialize.sh
assert_persistence_layout
run_comfyui repeat

echo "PASS: pre-populated parent preserved; cold and repeat starts healthy; custom nodes imported on both starts"
