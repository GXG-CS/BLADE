"""Typed choice questions: how a question is built, how an answer is checked, and how it is read."""
from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Tuple

Question = Dict[str, object]
Answer = Dict[str, object]  # {"choice": option, "probabilities": {option: p}}, probabilities summing to 1


def choice(text: str, options: Mapping[str, Optional[str]]) -> Question:
    """A multiple-choice question; options maps each option key to its description (None: the key says it all)."""
    return {"type": "choice", "instructions": text, "criteria": options}


def checked(name: str, question: Question, answer: Mapping) -> Answer:
    """The answer to one question with its probabilities renormalized; rejects an option that was not offered."""
    probs = answer["probabilities"]
    if answer["choice"] not in question["criteria"] or set(probs) != set(question["criteria"]):
        raise ValueError("Invalid answer for " + name)
    total = sum(probs.values())
    return {"choice": answer["choice"], "probabilities": {k: v / total for k, v in probs.items()}}


def ranked(probabilities: Mapping[str, float]) -> List[Tuple[str, float]]:
    """Options from the most to the least probable (ties keep the answer's order)."""
    return sorted(probabilities.items(), key=lambda kv: -kv[1])


def best(answer: Answer) -> Tuple[str, float]:
    """The most probable option and its probability rounded to two decimals."""
    label, p = ranked(answer["probabilities"])[0]
    return label, round(p, 2)
