FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

ARG COMFYUI_COMMIT=6f3895ed8d1e0f1d5fad11b48b3f159f7de1cc15
ARG KOLORS_WRAPPER_COMMIT=6fc1cd9d20bb7537facf180e5494b486b9710e24

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/workspace/model-lab/.cache/huggingface \
    MODEL_LAB_ROOT=/workspace/model-lab \
    COMFYUI_ROOT=/opt/ComfyUI

RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg git git-lfs jq libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/Comfy-Org/ComfyUI.git /opt/ComfyUI \
    && git -C /opt/ComfyUI checkout "$COMFYUI_COMMIT" \
    && git -C /opt/ComfyUI submodule update --init --recursive \
    && git clone https://github.com/kijai/ComfyUI-KwaiKolorsWrapper.git \
       /opt/ComfyUI/custom_nodes/ComfyUI-KwaiKolorsWrapper \
    && git -C /opt/ComfyUI/custom_nodes/ComfyUI-KwaiKolorsWrapper checkout "$KOLORS_WRAPPER_COMMIT"

WORKDIR /opt/ComfyUI
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --break-system-packages -r requirements.txt \
    && pip install --break-system-packages \
       -r custom_nodes/ComfyUI-KwaiKolorsWrapper/requirements.txt \
       "huggingface_hub[cli]>=0.35,<2"

COPY . /opt/model-lab
RUN chmod +x /opt/model-lab/scripts/*.sh /opt/model-lab/scripts/*.py

EXPOSE 8188 8888
CMD ["/opt/model-lab/scripts/start.sh"]
