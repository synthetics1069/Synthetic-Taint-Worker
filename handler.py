import platform
import subprocess
import time

import runpod


def get_gpu_info():
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return result.stdout.strip()
    except Exception as error:
        return f"GPU information unavailable: {error}"


def handler(job):
    job_input = job.get("input", {})
    action = job_input.get("action", "diagnostics")

    if action == "diagnostics":
        return {
            "ok": True,
            "service": "Synthetic Taint Worker",
            "version": "0.1.0",
            "python": platform.python_version(),
            "gpu": get_gpu_info(),
            "timestamp": int(time.time()),
            "capabilities": [
                "diagnostics",
                "echo",
            ],
        }

    if action == "echo":
        return {
            "ok": True,
            "job_id": job.get("id"),
            "payload": job_input.get("payload"),
        }

    return {
        "ok": False,
        "error": f"Unknown action: {action}",
        "supported_actions": ["diagnostics", "echo"],
    }


runpod.serverless.start({"handler": handler})
