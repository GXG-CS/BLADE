"""(4) Blame graph construction: G = (V, E, R, F), the evidence the diagnosis is given.

V are the trajectory's events (already in the state), E the dependency edges, F the findings of the contract audit
and R the requirement spans. No Jev question; nothing is propagated over the graph.
"""
from __future__ import annotations

from ..types import BlameGraph
from .base import Operator


class BlameGraphBuilder(Operator):
    name = "blame_graph_construction"
    needs = ("edges", "findings")

    def run(self, ctx):
        ctx.graph = BlameGraph(edges=ctx.edges, findings=ctx.findings, requirements=ctx.trajectory.requirements)
