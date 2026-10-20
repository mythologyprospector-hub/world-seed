"""Write sensitive local audit reports with owner-only file permissions."""
from __future__ import annotations

import json
import os
from pathlib import Path


def write_private_json(path: Path, report: object) -> None:
    """Write JSON to a file readable only by its owner (mode 0600 where supported)."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            fd = -1
            json.dump(report, stream, indent=2)
            stream.write("\n")
    finally:
        if fd >= 0:
            os.close(fd)
