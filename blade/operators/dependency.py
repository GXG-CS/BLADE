"""(1) Dependency reconstruction: Jev estimates which earlier event each event depends on, repeats, contradicts
and repairs; relations with probability at least edge_min are the probabilistic dependency edges E."""
from __future__ import annotations

from typing import Dict, List

from ..jev import choice
from ..jev.questions import Answer, Question
from ..prompts import NONE, RELATIONS
from ..types import DependencyEdge
from .base import Operator


def dependency_questions(events: List[str]) -> Dict[str, Question]:
    """For every event after the first and every relation, one question whose options are the earlier events and
    NONE. Named "relation|event"; the order (event, then relation) fixes the requests."""
    questions = {}
    for i, v in enumerate(events[1:], 1):
        for relation, (text, none_text) in RELATIONS.items():
            options = {u: None for u in events[:i]}
            options[NONE] = none_text.format(v=v)
            questions[relation + "|" + v] = choice(text.format(v=v), options)
    return questions


def dependency_edges(answers: Dict[str, Answer], edge_min: float) -> List[DependencyEdge]:
    """Every (relation, earlier event) with probability at least edge_min, sorted by event, relation and
    decreasing probability."""
    edges = (DependencyEdge(event=name.split("|")[1], relation=name.split("|")[0], earlier_event=u, p=round(p, 2))
             for name, a in answers.items() for u, p in a["probabilities"].items() if u != NONE and p >= edge_min)
    order = list(RELATIONS)
    return sorted(edges, key=lambda e: (e.event, order.index(e.relation), -e.p))


class DependencyReconstructor(Operator):
    name = "dependency_reconstruction"

    def run(self, ctx):
        ctx.links = ctx.client.ask_all(ctx.state, dependency_questions(ctx.trajectory.events))
        ctx.edges = dependency_edges(ctx.links, self.config.edge_min)
