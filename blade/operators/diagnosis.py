"""(5) Defeasible diagnosis: Jev weighs the blame graph against the complete trajectory.

The decisive-step question over the full trajectory, with G added to its state:
when = argmax_t P(e_t | q, tau, G) and who = the author of when. The audit's findings may be wrong and every event
remains a candidate, so the diagnosis can overrule them.
"""
from __future__ import annotations

from typing import Tuple

from ..jev import choice
from ..jev.client import JevClient
from ..prompts import DIAGNOSIS_FRAMING, WHEN_QUESTION, WHO_QUESTION
from ..trajectory import Trajectory
from ..types import BlameGraph, Distribution
from .base import Operator

MAX_OPTIONS = 255  # options per Jev question


def diagnosis_request(trajectory: Trajectory, graph: BlameGraph) -> Tuple[dict, dict]:
    """The state (trajectory, framing and blame graph) and the two questions over all agents and all events.

    The request keeps the standard who/when question pair of failure attribution; BLADE reads only the when
    answer and takes the responsible agent as the recorded author of the selected event."""
    agents = {a["actor_id"]: None for a in trajectory.view["agents"] if a["actor_id"]}
    steps = {v: None for v in trajectory.events}
    if not agents or not steps or max(len(agents), len(steps)) > MAX_OPTIONS:
        raise ValueError("Unsupported candidate count")
    state = dict(trajectory.view, attribution_task=DIAGNOSIS_FRAMING, graph=graph.to_state())
    questions = {"who": choice(WHO_QUESTION, agents), "when": choice(WHEN_QUESTION, steps)}
    return state, questions


def diagnose(client: JevClient, trajectory: Trajectory, graph: BlameGraph) -> Tuple[str, Distribution]:
    """The chosen event and the full distribution over events."""
    state, questions = diagnosis_request(trajectory, graph)
    a = client.ask(state, questions)
    return a["when"]["choice"], a["when"]["probabilities"]


class DefeasibleDiagnoser(Operator):
    name = "defeasible_diagnosis"
    needs = ("graph",)

    def run(self, ctx):
        ctx.when, ctx.probabilities = diagnose(ctx.client, ctx.trajectory, ctx.graph)
        ctx.who = ctx.trajectory.authors[ctx.when]
