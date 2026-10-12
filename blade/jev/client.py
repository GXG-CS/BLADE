"""JevClient: typed choice questions on one state, answered from the cache or by the Jev API.

One client per run. It counts the requests, all input tokens, and the input tokens paid in this run (requests not
found in the cache). With key None it never calls the API: a cache miss raises an error.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Optional

from ..config import DEFAULT, BladeConfig
from . import api
from .batching import batches
from .cache import ResponseCache
from .questions import Answer, Question, checked


@dataclass(frozen=True)
class Usage:
    requests: int = 0
    input_tokens: int = 0
    paid_input_tokens: int = 0

    def __sub__(self, other: "Usage") -> "Usage":
        return Usage(self.requests - other.requests, self.input_tokens - other.input_tokens,
                     self.paid_input_tokens - other.paid_input_tokens)


class JevClient:
    def __init__(self, key: Optional[str] = None, config: BladeConfig = DEFAULT):
        self.key = key
        self.config = config
        self.model = config.model or api.MODEL
        self.cache = ResponseCache(config.cache_dir, config.read_caches)
        self.tokens = self.paid = self.requests = 0

    def usage(self) -> Usage:
        return Usage(self.requests, self.tokens, self.paid)

    def ask(self, state: dict, questions: Dict[str, Question]) -> Dict[str, Answer]:
        """All questions in one request; if the API returns no response, the batch is split in half."""
        payload = {"model": self.model, "state": state, "questions": questions}
        key = self.cache.key(payload)
        hit = self.cache.find(key)
        if hit:
            response = self.cache.response(hit)
        else:
            if self.key is None:
                raise RuntimeError("Jev response not in the cache; pass an API key to call the Jev API")
            result = api.call_api(payload, self.key)
            response = result["response"]
            if response is None:
                if len(questions) == 1:
                    raise RuntimeError("Jev API request failed: " + json.dumps(result["attempts"]))
                names = list(questions)
                half = len(names) // 2
                return {**self.ask(state, {k: questions[k] for k in names[:half]}),
                        **self.ask(state, {k: questions[k] for k in names[half:]})}
            self.cache.store(key, payload, result)
        used = response.get("usage", {}).get("input_tokens", 0)
        self.tokens, self.requests = self.tokens + used, self.requests + 1
        self.paid += 0 if hit else used
        return {name: checked(name, question, response["answers"][name]) for name, question in questions.items()}

    def ask_all(self, state: dict, questions: Dict[str, Question]) -> Dict[str, Answer]:
        """Any number of questions on one state, in consecutive requests within the configured limits."""
        answers = {}
        for part in batches(questions, self.config.max_questions, self.config.max_question_chars):
            answers.update(self.ask(state, part))
        return answers
