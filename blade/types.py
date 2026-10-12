"""The objects BLADE passes between its operators.

Each object that reaches Jev has to_state(): the exact JSON form sent in the request.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, NamedTuple, Optional

from .prompts import GRAPH_NOTE, GROUP_OF

Distribution = Dict[str, float]


@dataclass(frozen=True)
class Requirement:
    """One exact span of the task (R)."""
    rid: str
    text: str

    def to_state(self) -> dict:
        return {"id": self.rid, "text": self.text}


@dataclass(frozen=True)
class DependencyEdge:
    """event has relation (depends_on, repeats, contradicts, repairs) to earlier_event with probability p (E)."""
    event: str
    relation: str
    earlier_event: str
    p: float  # rounded to two decimals

    def to_state(self) -> dict:
        return {"event": self.event, "relation": self.relation, "earlier_event": self.earlier_event, "p": self.p}


class Handoff(NamedTuple):
    """Information of event source used by event decision: one unit of the audit."""
    source: str
    decision: str


@dataclass(frozen=True)
class HandoffUse:
    """The audit of one handoff into an agent decision: how event uses event uses, as label with probability p."""
    event: str
    uses: str
    label: str
    p: float  # rounded to two decimals

    @property
    def group(self) -> str:
        """kept, breach, or inherited or repaired."""
        return GROUP_OF[self.label]

    @property
    def is_finding(self) -> bool:
        return self.group != "kept"

    def to_state(self) -> dict:
        return {"event": self.event, "uses": self.uses, "label": self.label, "p": self.p}


@dataclass
class BlameGraph:
    """G = (V, E, R, F): V the trajectory's events (in the state already), E the dependency edges, R the requirement
    spans, F the findings (handoff uses that are not kept). Evidence for the diagnosis, not a verdict."""
    edges: List[DependencyEdge]
    findings: List[HandoffUse]
    requirements: List[Requirement]
    note: str = GRAPH_NOTE

    def to_state(self) -> dict:
        """The graph as sent to the diagnosis; F goes under the field name "flags" used by the note."""
        return {"note": self.note, "edges": [e.to_state() for e in self.edges],
                "requirements": [r.to_state() for r in self.requirements],
                "flags": [f.to_state() for f in self.findings]}


@dataclass(frozen=True)
class OperatorRecord:
    """What one operator cost on one run."""
    operator: str
    requests: int
    input_tokens: int
    paid_input_tokens: int
    seconds: float

    def to_dict(self) -> dict:
        return {"operator": self.operator, "requests": self.requests, "input_tokens": self.input_tokens,
                "paid_input_tokens": self.paid_input_tokens, "seconds": round(self.seconds, 3)}


@dataclass
class Attribution:
    """BLADE's answer on one run: the decisive step (when), its author (who), and the evidence behind them."""
    when: str
    who: Optional[str]
    probabilities: Distribution
    graph: BlameGraph
    kind: Dict[str, str]
    uses: List[HandoffUse]
    links: Dict[str, dict]
    records: List[OperatorRecord] = field(default_factory=list)

    @property
    def requests(self) -> int:
        return sum(r.requests for r in self.records)

    @property
    def input_tokens(self) -> int:
        return sum(r.input_tokens for r in self.records)

    @property
    def paid_input_tokens(self) -> int:
        return sum(r.paid_input_tokens for r in self.records)

    def to_dict(self) -> dict:
        return {"when": self.when, "who": self.who, "probabilities": self.probabilities,
                "graph": self.graph.to_state(), "kind": self.kind, "uses": [u.to_state() for u in self.uses],
                "links": self.links, "requests": self.requests, "input_tokens": self.input_tokens,
                "paid_input_tokens": self.paid_input_tokens, "operators": [r.to_dict() for r in self.records]}
