"""RunContext: everything the operators share on one run.

The pipeline creates it from the input; each operator reads what earlier operators produced and writes its own
product. The fields are filled in operator order:

  (1) dependency reconstruction  links, edges
  (2) audit planning             handoffs
  (3) contract auditing          kind, uses, findings
  (4) blame graph construction   graph
  (5) defeasible diagnosis       when, probabilities, who
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .config import BladeConfig
from .jev import JevClient
from .prompts import FRAMING
from .trajectory import Trajectory
from .types import Attribution, BlameGraph, DependencyEdge, Distribution, Handoff, HandoffUse, OperatorRecord


@dataclass
class RunContext:
    trajectory: Trajectory
    client: JevClient
    config: BladeConfig
    links: Optional[Dict[str, dict]] = None        # relation answers, "relation|event" -> answer
    edges: Optional[List[DependencyEdge]] = None   # E
    handoffs: Optional[List[Handoff]] = None       # audit plan
    kind: Optional[Dict[str, str]] = None          # event -> AGENT_DECISION or EVIDENCE
    uses: Optional[List[HandoffUse]] = None        # audited handoffs into agent decisions
    findings: Optional[List[HandoffUse]] = None    # F
    graph: Optional[BlameGraph] = None             # G
    when: Optional[str] = None
    probabilities: Optional[Distribution] = None
    who: Optional[str] = None
    records: List[OperatorRecord] = field(default_factory=list)

    @property
    def state(self) -> dict:
        """The state of the local questions (1) and (3): the answer-blind trajectory and the framing."""
        return dict(self.trajectory.view, attribution_task=FRAMING)

    @property
    def audit_state(self) -> dict:
        """The state of the contract audit (3): the local state with the requirement spans."""
        return dict(self.state, requirements=[r.to_state() for r in self.trajectory.requirements])

    def require(self, *names: str) -> None:
        """Stop if an operator runs before the operators whose products it needs."""
        missing = [n for n in names if getattr(self, n) is None]
        if missing:
            raise RuntimeError("operator order: %s not produced yet" % ", ".join(missing))

    def attribution(self) -> Attribution:
        self.require("links", "kind", "uses", "graph", "when", "probabilities")
        return Attribution(when=self.when, who=self.who, probabilities=self.probabilities, graph=self.graph,
                           kind=self.kind, uses=self.uses, links=self.links, records=list(self.records))
