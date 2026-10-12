"""BladePipeline: the five operators in order on one run.

  (q, tau) --(1) Jev--> E --(2) graph--> handoffs --(3) Jev--> F --(4)--> G = (V, E, R, F) --(5) Jev--> (when, who)

Operators (1) to (4) collect the evidence (collect()); (5) decides (run()). Each operator records its Jev requests,
input tokens and time on the run's context.
"""
from __future__ import annotations

from typing import Optional, Sequence

from .config import DEFAULT, BladeConfig
from .context import RunContext
from .jev import JevClient
from .operators import EVIDENCE_OPERATORS, DefeasibleDiagnoser, Operator
from .trajectory import Trajectory
from .types import Attribution


class BladePipeline:
    def __init__(self, config: BladeConfig = DEFAULT, evidence: Optional[Sequence[Operator]] = None,
                 diagnosis: Optional[Operator] = None):
        self.config = config
        self.evidence = tuple(evidence) if evidence is not None else tuple(op(config) for op in EVIDENCE_OPERATORS)
        self.diagnosis = diagnosis or DefeasibleDiagnoser(config)

    @property
    def operators(self) -> tuple:
        return self.evidence + (self.diagnosis,)

    def context(self, inp: dict, client: JevClient) -> RunContext:
        return RunContext(trajectory=Trajectory.from_input(inp), client=client, config=self.config)

    def collect(self, inp: dict, client: Optional[JevClient] = None) -> RunContext:
        """Operators (1) to (4): the context with the blame graph, before the diagnosis."""
        ctx = self.context(inp, client or JevClient(None, self.config))
        for op in self.evidence:
            op(ctx)
        return ctx

    def run(self, inp: dict, key: Optional[str] = None) -> Attribution:
        """BLADE on one run. key: Jev API key; None answers from the cache only."""
        ctx = self.collect(inp, JevClient(key, self.config))
        self.diagnosis(ctx)
        return ctx.attribution()
