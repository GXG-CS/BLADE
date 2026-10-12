"""The input of BLADE on one run: the answer-blind view of the trajectory and the requirement spans of the task."""
from __future__ import annotations

import copy
from dataclasses import dataclass
import re
from typing import Dict, List, Optional

from .types import Requirement

AGENT_FIELDS = ("actor_id", "recorded_name", "role", "system_prompt")
EVENT_FIELDS = ("event_id", "order", "actor_id", "recorded_actor", "recorded_role", "content", "ledger",
                "tool_actions")
CONTEXT_FIELDS = ("agent_configuration", "agent_system_intro")


def _event_view(event: dict) -> dict:
    view = {k: copy.deepcopy(event.get(k)) for k in EVENT_FIELDS}
    view["ledger"] = None  # orchestrator progress ledgers are never shown: they can reveal benchmark annotations
    return view


def answer_blind_view(inp: dict) -> dict:
    """The state shown to Jev: the task, the agents and the events, restricted to a fixed set of fields. Run
    identifiers, metadata, progress ledgers, reference answers and annotations are never exposed."""
    view = {
        "task": {"query": inp["task"]["query"]},
        "agents": [{k: copy.deepcopy(a.get(k)) for k in AGENT_FIELDS} for a in inp["agents"]],
        "events": [_event_view(e) for e in inp["events"]],
    }
    if "execution_context" in inp:
        view["execution_context"] = {k: copy.deepcopy(inp["execution_context"][k])
                                     for k in CONTEXT_FIELDS if k in inp["execution_context"]}
    return view


@dataclass
class Trajectory:
    """One run as BLADE reads it."""
    raw: dict                          # the input as given
    view: dict                         # answer-blind view: the state shown to Jev
    events: List[str]                  # event ids in trajectory order (V)
    authors: Dict[str, Optional[str]]  # event id -> agent that wrote it (None for tool, user or system events)
    requirements: List[Requirement]    # R

    @classmethod
    def from_input(cls, inp: dict) -> "Trajectory":
        view = answer_blind_view(inp)
        return cls(raw=inp, view=view, events=[e["event_id"] for e in view["events"]],
                   authors={e["event_id"]: e["actor_id"] for e in view["events"]},
                   requirements=[Requirement("R%d" % i, t)
                                 for i, t in enumerate(requirement_spans(view["task"]["query"]), 1)])


def requirement_spans(text: str) -> List[str]:
    """R: the task split into exact text spans: list items, discourse markers or semicolons, else sentences."""
    lines = [m.group(1).strip() for m in re.finditer(r"(?m)^[ \t]*(?:[-*]+|\d+[.)])\s+(.+?)\s*$", text)
             if m.group(1).strip()]
    if len(lines) >= 2:
        return lines
    pattern = (r"(?i)(?:(?<=^)|(?<=[.!?]))\s*(?:first(?:ly)?|second(?:ly)?|third(?:ly)?|next|then|additionally|"
               r"furthermore|moreover|(?:i(?:'|’)m\s+)?also|finally|lastly)\b")
    starts = [m.start() for m in re.finditer(pattern, text)]
    if len(starts) >= 2:
        cuts = [0] + starts[1:] + [len(text)]
        return [text[a:b].strip() for a, b in zip(cuts, cuts[1:]) if text[a:b].strip()]
    semicolons = [m.end() for m in re.finditer(";", text)]
    if len(semicolons) >= 2:
        cuts = [0] + semicolons + [len(text)]
        return [text[a:b].strip() for a, b in zip(cuts, cuts[1:]) if text[a:b].strip()]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if s.strip()]
    return sentences if len(sentences) >= 2 else [text.strip()]
