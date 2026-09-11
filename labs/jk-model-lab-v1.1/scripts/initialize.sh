#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="${MODEL_LAB_ROOT:-/workspace/model-lab}"
COMFY_ROOT="${COMFYUI_ROOT:-/opt/ComfyUI}"

mkdir -p \
  "$LAB_ROOT/models/checkpoints" \
  "$LAB_ROOT/models/diffusion_models" \
  "$LAB_ROOT/models/text_encoders" \
  "$LAB_ROOT/models/vae" \
  "$LAB_ROOT/models/loras" \
  "$LAB_ROOT/models/LLM" \
  "$LAB_ROOT/models/diffusers/Kolors" \
  "$LAB_ROOT/input" \
  "$LAB_ROOT/output" \
  "$LAB_ROOT/runs" \
  "$LAB_ROOT/user/default/workflows" \
  "$LAB_ROOT/.cache/huggingface"

# Preserve ComfyUI's populated diffusers parent. Only the Kolors model directory
# is redirected to persistent storage.
runtime_kolors="$COMFY_ROOT/models/diffusers/Kolors"
persistent_kolors="$LAB_ROOT/models/diffusers/Kolors"
mkdir -p "$COMFY_ROOT/models/diffusers"

if [[ -L "$runtime_kolors" ]]; then
  ln -sfn "$persistent_kolors" "$runtime_kolors"
elif [[ -d "$runtime_kolors" ]] && [[ -z "$(find "$runtime_kolors" -mindepth 1 -print -quit)" ]]; then
  rmdir "$runtime_kolors"
  ln -s "$persistent_kolors" "$runtime_kolors"
elif [[ ! -e "$runtime_kolors" ]]; then
  ln -s "$persistent_kolors" "$runtime_kolors"
else
  echo "ERROR: $runtime_kolors is populated and cannot be redirected safely." >&2
  exit 1
fi

for workflow in /opt/model-lab/workflows/*.json; do
  cp -n "$workflow" "$LAB_ROOT/user/default/workflows/$(basename "$workflow")"
done

