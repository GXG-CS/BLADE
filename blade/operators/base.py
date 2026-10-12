"""The operator interface: one step of BLADE that reads from and writes to the RunContext."""
from __future__ import annotations

from abc import ABC, abstractmethod
import time

from ..config import DEFAULT, BladeConfig
from ..context import RunContext
from ..types import OperatorRecord


class Operator(ABC):
    name: str = "operator"
    needs: tuple = ()  # context fields that must be produced before this operator runs

    def __init__(self, config: BladeConfig = DEFAULT):
        self.config = config

    def __call__(self, ctx: RunContext) -> RunContext:
        """Run the operator and record its Jev requests, input tokens and time on the context."""
        ctx.require(*self.needs)
        before, start = ctx.client.usage(), time.perf_counter()
        self.run(ctx)
        used = ctx.client.usage() - before
        ctx.records.append(OperatorRecord(self.name, used.requests, used.input_tokens, used.paid_input_tokens,
                                          time.perf_counter() - start))
        return ctx

    @abstractmethod
    def run(self, ctx: RunContext) -> None:
        """Read earlier products from ctx and write this operator's product to it."""
