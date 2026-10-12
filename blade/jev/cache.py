"""Response cache addressed by the hash of the full request (model, state and questions).

A request that was answered before is read from the first cache directory that holds it and costs nothing. New
responses are written, with their request, to the write directory."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Sequence

from . import api


class ResponseCache:
    def __init__(self, write_dir: Path, read_dirs: Sequence[Path] = ()):
        self.write_dir = Path(write_dir)
        self.read_dirs = [self.write_dir] + [Path(d) for d in read_dirs]

    @staticmethod
    def key(payload: dict) -> str:
        return api.digest(payload) + ".json"

    def find(self, key: str) -> Optional[Path]:
        return next((d / key for d in self.read_dirs if (d / key).exists()), None)

    @staticmethod
    def response(path: Path) -> dict:
        return json.loads(path.read_text())["response"]

    def store(self, key: str, payload: dict, result: dict) -> None:
        self.write_dir.mkdir(parents=True, exist_ok=True)
        (self.write_dir / key).write_text(json.dumps({"request": payload, **result}, ensure_ascii=False))
