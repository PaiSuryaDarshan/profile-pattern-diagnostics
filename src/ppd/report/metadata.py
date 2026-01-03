from __future__ import annotations

from datetime import datetime
from typing import Dict


def build_metadata(*, axis: str, version: str = "1.1.2") -> Dict[str, str]:
    """Standard metadata attached to every PPD output."""
    if axis not in {"within-candidate", "across-candidate"}:
        raise ValueError(f"Invalid axis: {axis}")

    return {
        "tool": "Profile Pattern Diagnostics (PPD)",
        "version": version,
        "axis": axis,
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "scope_note": (
            "Diagnostic + descriptive only. No predictions, rankings, or suitability decisions."
        ),
    }
