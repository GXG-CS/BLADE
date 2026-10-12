"""(3) Contract auditing: Jev judges how each agent decision uses each planned source.

Each handoff carries an implicit contract: the decision has to use its source faithfully and in a way that fits
the task's requirement spans R (entity, version, time period, unit, scope, completeness). Jev labels every audited
use with one of nine labels in three groups: kept, breach (an error enters at the decision) and inherited or
repaired (an error already in the source is carried forward or removed). Uses that are not kept are the findings
F: evidence for the diagnosis, not a verdict on who is responsible.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from ..jev import best, choice
from ..jev.questions import Answer, Question
from ..prompts import DECISION, EVIDENCE_USE, KIND, KIND_QUESTION, USE_QUESTION
from ..types import Handoff, HandoffUse
from .base import Operator


def audit_questions(events: List[str], handoffs: List[Handoff]) -> Dict[str, Question]:
    """The kind of every event ("kind|event"), then the use of every handoff ("use|source|decision")."""
    questions = {"kind|" + v: choice(KIND_QUESTION % v, KIND) for v in events}
    for u, v in handoffs:
        questions["use|%s|%s" % (u, v)] = choice(USE_QUESTION.format(u=u, v=v),
                                                 {k: d.format(u=u, v=v) for k, d in EVIDENCE_USE.items()})
    return questions


def read_audit(answers: Dict[str, Answer], events: List[str],
               handoffs: List[Handoff]) -> Tuple[Dict[str, str], List[HandoffUse]]:
    """Event kinds, and the most likely label of every handoff into an agent decision (by decision, then source
    rank)."""
    kind = {v: best(answers["kind|" + v])[0] for v in events}
    uses = []
    for v in events:
        if kind[v] != DECISION:
            continue
        for h in handoffs:
            if h.decision == v:
                label, p = best(answers["use|%s|%s" % (h.source, v)])
                uses.append(HandoffUse(event=v, uses=h.source, label=label, p=p))
    return kind, uses


class ContractAuditor(Operator):
    name = "contract_auditing"
    needs = ("handoffs",)

    def run(self, ctx):
        events = ctx.trajectory.events
        answers = ctx.client.ask_all(ctx.audit_state, audit_questions(events, ctx.handoffs))
        ctx.kind, ctx.uses = read_audit(answers, events, ctx.handoffs)
        ctx.findings = [u for u in ctx.uses if u.is_finding]
