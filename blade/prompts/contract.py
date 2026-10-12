"""Questions of operator (3), contract auditing, and the groups of its labels."""

DECISION = "AGENT_DECISION"  # the kind of event whose handoffs are audited

KIND_QUESTION = "Is event %s an agent's own decision, or only evidence?"  # only decisions are audited
KIND = {
    "AGENT_DECISION": "An agent's own decision: a plan, instruction, claim, code, calculation, summary or answer.",
    "EVIDENCE": "Only evidence: tool or terminal output, retrieved page content, or a user or system message.",
}
USE_QUESTION = ("Event {v} relies on information from event {u}. How does event {v} use that information? Check "
                "the use against every requirement in state.requirements: the entity, version, time period, unit, "
                "scope and completeness the task asks for.")
EVIDENCE_USE = {  # how decision {v} uses source {u}
    "FAITHFUL_USE": "Event {v} uses the information from event {u} accurately, and it fits the task requirements.",
    "UNVERIFIED_ADOPTION": "Event {v} treats an assumption, example, estimate or unverified claim from event {u} "
                           "as established fact.",
    "INAPPLICABLE_USE": "Event {v} relies on information from event {u} that does not satisfy the task requirements: "
                        "wrong entity, version, time period, unit or scope, or incomplete results treated as complete.",
    "MISINTERPRETATION": "Event {v} misreads, distorts or misapplies what event {u} says.",
    "PROPAGATION": "Event {v} carries forward a problem that was already present in event {u}, adding no new one.",
    "CORRECTION": "Event {v} identifies and corrects a problem in event {u} without introducing a new one.",
    "CORRECTION_WITH_NEW_ERROR": "Event {v} corrects a problem in event {u} but at the same time introduces a new "
                                 "error, or changes a value or condition so that the result no longer fits the task.",
    "UNRELATED": "Event {v} does not actually use the information from event {u}.",
    "UNKNOWN": "The trajectory does not show how event {v} uses event {u}.",
}
EVIDENCE_GROUPS = {  # evidence for the diagnosis, not a verdict
    "kept": ("FAITHFUL_USE", "UNRELATED", "UNKNOWN"),
    # an error enters at the decision
    "breach": ("UNVERIFIED_ADOPTION", "INAPPLICABLE_USE", "MISINTERPRETATION", "CORRECTION_WITH_NEW_ERROR"),
    # an error already in the source is carried forward or removed
    "inherited or repaired": ("PROPAGATION", "CORRECTION"),
}
FINDINGS = set(EVIDENCE_GROUPS["breach"]) | set(EVIDENCE_GROUPS["inherited or repaired"])  # F
GROUP_OF = {label: group for group, labels in EVIDENCE_GROUPS.items() for label in labels}
