"""Configuration of BLADE: the audit's thresholds, the limits of one Jev request and where responses are cached."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence


@dataclass(frozen=True)
class BladeConfig:
    """The defaults are the settings used in the paper."""

    edge_min: float = 0.3            # theta: keep a relation / audit a source when its probability is at least this
    max_sources: int = 2             # K: audited sources per event
    max_questions: int = 50          # questions per Jev request
    max_question_chars: int = 60000  # characters of the questions in one Jev request
    model: Optional[str] = None      # Jev model; None: jev-1.13.0
    cache_dir: Path = Path(".jev_cache")  # where new Jev responses are written (and read first)
    read_caches: Sequence[Path] = ()      # further read-only cache directories, searched in order

    def __post_init__(self):
        if not 0.0 < self.edge_min <= 1.0:
            raise ValueError("edge_min must be in (0, 1]")
        if self.max_sources < 1 or self.max_questions < 1 or self.max_question_chars < 1:
            raise ValueError("max_sources, max_questions and max_question_chars must be positive")


DEFAULT = BladeConfig()
