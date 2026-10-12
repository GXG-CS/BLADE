"""(2) Audit planning: the dependency graph chooses which handoffs Jev audits.

For every event v, the handoffs are its max_sources most likely depends_on sources u with probability at least
edge_min. The plan is made before the event kinds are known; handoffs into events that turn out to be evidence are
asked about with the others and then left out (operator 3). Planning reuses the dependency probabilities and asks
Jev nothing.
"""
from __future__ import annotations

from typing import Dict, List

from ..jev import ranked
from ..prompts import NONE
from ..types import Handoff
from .base import Operator


def plan_handoffs(links: Dict[str, dict], events: List[str], edge_min: float, max_sources: int) -> List[Handoff]:
    """The handoffs to audit, in trajectory order and, per event, from the most likely source."""
    handoffs = []
    for v in events[1:]:
        dist = links["depends_on|" + v]["probabilities"]
        sources = [u for u, p in ranked(dist) if u != NONE and p >= edge_min]
        handoffs += [Handoff(u, v) for u in sources[:max_sources]]
    return handoffs


class AuditPlanner(Operator):
    name = "audit_planning"
    needs = ("links",)

    def run(self, ctx):
        ctx.handoffs = plan_handoffs(ctx.links, ctx.trajectory.events, self.config.edge_min, self.config.max_sources)
