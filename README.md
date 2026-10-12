# BLADE: Blame Localization via Audited Dependency Evidence

Code for the paper *BLADE: Dependency Tracing Is Not Enough for Failure Attribution in LLM Multi-Agent Systems*.

Given the task and the recorded trajectory of a failed multi-agent run, BLADE identifies the decisive error step
and the responsible agent, without access to a reference answer. A dependency between two steps shows where
information came from, not where it went wrong: a receiving decision may faithfully carry forward a faulty source,
or misuse a correct one. BLADE therefore audits how information is *used* at source–decision handoffs and combines
the resulting evidence in a global diagnosis.

## Method

BLADE runs five operators. Every judgment is a multiple-choice question answered by
[Jev](https://docs.typesafe.ai) (TypeSafe, `jev-1.13.0`), which returns a probability for every option.

1. **Dependency reconstruction.** For every event, Jev identifies which earlier event it *depends on*, *repeats*,
   *contradicts* and *repairs*. Relations with probability at least θ = 0.3 form the dependency edges E.
2. **Audit planning.** The *depends-on* probabilities select, for every event, its K = 2 most likely sources as the
   source–decision handoffs to audit. No additional model calls.
3. **Contract auditing.** Jev judges how each receiving agent decision uses its source against requirement spans R
   extracted from the task, with nine labels in three groups: *kept*, *breach* (an error enters at the decision),
   and *inherited or repaired*. Non-kept labels are the findings F.
4. **Blame graph.** G = (V, E, R, F) connects where information came from with how it was used.
5. **Defeasible diagnosis.** Jev reads the complete trajectory together with G and selects the decisive step;
   every event remains a candidate, so the diagnosis can overrule uncertain findings. The responsible agent is the
   recorded author of that step.

## Installation

Python ≥ 3.9; no third-party dependencies.

```bash
pip install -e .
export JEV_API_KEY=...   # a TypeSafe Jev API key
```

Jev responses are cached in `.jev_cache/` by the hash of each request, so rerunning a trajectory costs nothing.

## Quick start

`examples/who_and_when_ag68.json` is a failed run from Who&When (Algorithm-Generated, task 68), with its Jev
responses cached in `examples/jev_cache/`, so it runs without an API key:

```bash
python -m blade examples/who_and_when_ag68.json --offline --cache-dir examples/jev_cache
```

```text
decisive step:     e0003 (p = 0.47)
responsible agent: verification_expert
findings (event <- source: label, p):
  e0001    <- e0000    UNVERIFIED_ADOPTION (0.25)
  e0003    <- e0002    MISINTERPRETATION (0.60)
  e0004    <- e0003    PROPAGATION (0.40)
  e0005    <- e0003    PROPAGATION (0.33)
Jev requests: 3, input tokens: 18275
```

The code execution in `e0002` returns Braintree and Honolulu; the verification expert misreads it in `e0003`, and
later agents carry the misreading forward. BLADE flags the misreading as a breach and its reuse as propagation, and
the diagnosis selects `e0003`, the annotated decisive step.

## Usage

Command line:

```bash
python -m blade run.json            # calls Jev for requests not in the cache
python -m blade run.json --json     # full result: graph, audit labels, probabilities, cost
python -m blade run.json --offline  # cached responses only
```

Python:

```python
import json, os
from blade import BladePipeline, BladeConfig

inp = json.load(open("run.json"))
result = BladePipeline(BladeConfig()).run(inp, key=os.environ["JEV_API_KEY"])

result.when              # decisive step (event id)
result.who               # responsible agent (author of result.when)
result.probabilities     # distribution over all events
result.graph.edges       # dependency edges E
result.graph.findings    # audit findings F (event, source, label, p)
result.records           # Jev requests and input tokens per operator
```

The evidence can also be collected without the diagnosis: `BladePipeline().collect(inp, client)` returns the run
context after operators (1)–(4).

## Input format

One JSON object per failed run:

```json
{
  "task": {"query": "Which two U.S. presidential birthplaces are farthest apart? ..."},
  "agents": [
    {"actor_id": "verification_expert", "recorded_name": "Verification_Expert",
     "role": "assistant", "system_prompt": "..."}
  ],
  "events": [
    {"event_id": "e0001", "order": 1, "actor_id": "verification_expert",
     "recorded_actor": "Verification_Expert", "recorded_role": "assistant",
     "content": "...", "ledger": null, "tool_actions": null},
    {"event_id": "e0002", "order": 2, "actor_id": null,
     "recorded_actor": "Computer_terminal", "recorded_role": "user",
     "content": "exitcode: 0 ...", "ledger": null, "tool_actions": null}
  ]
}
```

`actor_id` is `null` for tool, user and system events. Every event is a candidate for the decisive step, and the
responsible agent is the recorded author (`actor_id`) of the selected event. An optional `execution_context`
object may hold `agent_configuration` and `agent_system_intro`. Only these fields are shown to Jev; `ledger` is
always cleared, and any other field (run identifiers, reference answers, annotations) is ignored.

## Configuration

| `BladeConfig` field | Default | Meaning |
|---|---|---|
| `edge_min` | 0.3 | θ: minimum probability of a dependency edge and of an audited source |
| `max_sources` | 2 | K: audited sources per event |
| `max_questions` | 50 | questions per Jev request (questions on the same state are batched) |
| `max_question_chars` | 60000 | characters of the questions in one request |
| `model` | `jev-1.13.0` | Jev model |
| `cache_dir` | `.jev_cache` | where responses are written and read |
| `read_caches` | `()` | further read-only cache directories |

## Repository layout

```text
blade/
├── config.py        # BladeConfig
├── trajectory.py    # answer-blind view of a run and requirement spans R
├── types.py         # DependencyEdge, Handoff, HandoffUse, BlameGraph, Attribution
├── context.py       # RunContext shared by the operators
├── pipeline.py      # BladePipeline: collect() = operators 1-4, run() = all five
├── operators/       # dependency, planning, contract, blame_graph, diagnosis
├── prompts/         # every text sent to Jev
└── jev/             # Jev client: typed choice questions, batching, response cache
examples/
├── who_and_when_ag68.json   # one failed run from Who&When
└── jev_cache/               # its cached Jev responses
```

## License

MIT. The example run is taken from Who&When (Zhang et al., ICML 2025), released under the MIT License
(`examples/WHO_AND_WHEN_LICENSE`).
