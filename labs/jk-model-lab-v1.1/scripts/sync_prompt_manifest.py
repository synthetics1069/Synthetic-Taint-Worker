#!/usr/bin/env python3
"""Generate the approved machine manifest from the canonical Markdown protocol."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "MODEL_LAB_PROMPTS_AND_EXECUTION.md"
MANIFEST = ROOT / "experiments" / "prompt_manifest.json"
HASH_FILE = ROOT / "experiments" / "prompt_manifest.sha256"
SEEDS = [
    104729,
    130363,
    155921,
    181081,
    205759,
    230969,
    256019,
    281117,
    306239,
    331337,
    356387,
    381481,
]


def main() -> None:
    source = PROTOCOL.read_text(encoding="utf-8")
    if "**Protocol version:** `1.0.0`" not in source or "**Protocol status:** `APPROVED`" not in source:
        raise SystemExit("protocol must be version 1.0.0 and APPROVED")

    pattern = re.compile(
        r"^### (Prompt_\d{2}) — (.+?)\n\n"
        r"(.*?)\n\n\*\*Test intent:\*\* (.*?)\n\n"
        r"\*\*Expected failure signals:\*\* (.*?)"
        r"(?=\n\n### Prompt_|\n\n## 7\.)",
        re.MULTILINE | re.DOTALL,
    )
    matches = pattern.findall(source)
    if len(matches) != 15:
        raise SystemExit(f"expected 15 canonical prompts, found {len(matches)}")

    prompts = []
    for prompt_id, title, prompt, intent, failures in matches:
        prompts.append(
            {
                "prompt_id": prompt_id,
                "status": "APPROVED",
                "title": title.strip(),
                "prompt": " ".join(prompt.split()),
                "negative_prompt": "",
                "category": title.strip(),
                "test_intent": " ".join(intent.split()),
                "failure_signals": [item.strip().rstrip(".") for item in failures.split(";")],
            }
        )

    expected_ids = [f"Prompt_{index:02d}" for index in range(1, 16)]
    if [item["prompt_id"] for item in prompts] != expected_ids:
        raise SystemExit("prompt IDs are missing or out of order")

    manifest = {
        "schema_version": 1,
        "lab_id": "JK_MODEL_LAB_01",
        "protocol_version": "1.0.0",
        "protocol_document": "docs/MODEL_LAB_PROMPTS_AND_EXECUTION.md",
        "approved_by": "J.K.",
        "approval_date_utc": "2026-09-11",
        "manifest_status": "APPROVED",
        "samples_per_prompt_per_model": 12,
        "seed_set": SEEDS,
        "prompts": prompts,
    }
    encoded = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    MANIFEST.write_bytes(encoded)
    digest = hashlib.sha256(encoded).hexdigest()
    HASH_FILE.write_text(f"{digest}  prompt_manifest.json\n", encoding="utf-8")
    print(f"Wrote {MANIFEST} with 15 approved prompts")
    print(digest)


if __name__ == "__main__":
    main()
