# Changelog

## 1.1.0

- Redesigned the package as a five-model, generation-only lab.
- Added KREA 2 Turbo, Kolors, and Z-Image Base.
- Retained HiDream-O1-Image Full and Chroma1-HD.
- Removed Wan 2.2, Qwen-Image-Edit-2511, and JoyAI-Image-Edit-Plus.
- Deferred GLM-Image to a later hybrid-model lab.
- Added five independent API workflows for agent execution.
- Added a guarded 15-prompt × 5-model × 12-seed batch runner with resume, metrics, contact sheets, and bounded retries.
- Added the approval-gated prompt manifest and deterministic seed set.
- Sealed the 15-prompt protocol as version 1.0.0 after J.K.'s approval on 2026-09-11.
- Added a deterministic Markdown-to-JSON manifest synchronization script and recorded manifest hash.
- Preserve user-edited persistent workflows on container restart by copying packaged defaults only when absent.
- Add an opt-in Pod self-termination guard for bounded commissioning runs now that RunPod no longer exposes create-time stop/terminate flags.
