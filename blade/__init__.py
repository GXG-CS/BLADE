"""BLADE: Blame Localization via Audited Dependency Evidence.

A dependency between two steps shows where information came from, not where it went wrong: the same dependency can
carry a wrong source that is used faithfully (the error is upstream) or a correct source that is misused (the
error enters downstream). BLADE reconstructs the dependencies, uses them to choose which source-decision handoffs to
audit, audits how each receiving decision uses its source against the task's requirements, and leaves the verdict
to a global diagnosis over all events. Every judgment is a multiple-choice decision answered by Jev.

    from blade import BladePipeline
    result = BladePipeline().run(inp, key)   # inp: one run (see README); key: Jev API key
    result.when, result.who, result.graph.findings
"""
from .config import DEFAULT, BladeConfig
from .context import RunContext
from .jev import JevClient, Usage
from .operators import (EVIDENCE_OPERATORS, AuditPlanner, BlameGraphBuilder, ContractAuditor, DefeasibleDiagnoser,
                        DependencyReconstructor, Operator)
from .pipeline import BladePipeline
from .trajectory import Trajectory, answer_blind_view, requirement_spans
from .types import (Attribution, BlameGraph, DependencyEdge, Handoff, HandoffUse, OperatorRecord, Requirement)

__version__ = "0.1.0"

__all__ = [
    "Attribution", "AuditPlanner", "BladeConfig", "BladePipeline", "BlameGraph", "BlameGraphBuilder",
    "ContractAuditor", "DEFAULT", "DefeasibleDiagnoser", "DependencyEdge", "DependencyReconstructor",
    "EVIDENCE_OPERATORS", "Handoff", "HandoffUse", "JevClient", "Operator", "OperatorRecord", "Requirement",
    "RunContext", "Trajectory", "Usage", "answer_blind_view", "requirement_spans",
]
