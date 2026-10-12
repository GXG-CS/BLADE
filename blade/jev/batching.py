"""Splitting the questions on one state into Jev requests, in the order given."""
from __future__ import annotations

from typing import Dict, List

from . import api
from .questions import Question


def batches(questions: Dict[str, Question], max_questions: int, max_chars: int) -> List[Dict[str, Question]]:
    """Consecutive groups of at most max_questions questions and max_chars characters (a single question longer
    than max_chars forms its own group). The order of the questions decides the requests, and with them the cache
    keys."""
    out, current, size = [], {}, 0
    for name, question in questions.items():
        chars = len(api.canonical(question))
        if current and (len(current) >= max_questions or size + chars > max_chars):
            out.append(current)
            current, size = {}, 0
        current[name] = question
        size += chars
    return out + [current] if current else out
