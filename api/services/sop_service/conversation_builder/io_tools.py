from __future__ import annotations

import base64
from pathlib import Path
from typing import List


ARTIFACTS_DIR = Path("_artifacts")


def ensure_artifacts_dir() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def write_mermaid_topology(content: str, path: Path | None = None) -> str:
    target = path or Path("graph_sop_builder.mmd")
    target.write_text(content, encoding="utf-8")
    return str(target)


def write_mermaid_trace(thread_id: str, visited_nodes: List[str]) -> str:
    ensure_artifacts_dir()
    lines = ["graph TD"]
    for i in range(len(visited_nodes) - 1):
        a = visited_nodes[i]
        b = visited_nodes[i + 1]
        lines.append(f"    {a} --> {b}")
    content = "\n".join(lines)
    path = ARTIFACTS_DIR / f"{thread_id}_trace.mmd"
    path.write_text(content, encoding="utf-8")
    return str(path)


def transcribe_audio_stub(audio_b64: str | None) -> str:
    if not audio_b64:
        return ""
    try:
        base64.b64decode(audio_b64)
        # Stub: return empty string to avoid external calls
        return ""
    except Exception:
        return ""


