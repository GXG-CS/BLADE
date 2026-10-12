"""Command line: attribute one failed run.

    JEV_API_KEY=... python -m blade run.json
    python -m blade run.json --offline          # cached Jev responses only
"""
import argparse
import json
import os
from pathlib import Path

from .config import BladeConfig
from .pipeline import BladePipeline


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m blade", description="Failure attribution with BLADE.")
    parser.add_argument("input", type=Path, help="JSON file of one failed run (see README)")
    parser.add_argument("--cache-dir", type=Path, default=Path(".jev_cache"), help="Jev response cache")
    parser.add_argument("--offline", action="store_true", help="answer from the cache only, never call the API")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = parser.parse_args(argv)
    key = None if args.offline else os.environ.get("JEV_API_KEY")
    if key is None and not args.offline:
        parser.error("set JEV_API_KEY, or use --offline")
    inp = json.loads(args.input.read_text())
    result = BladePipeline(BladeConfig(cache_dir=args.cache_dir)).run(inp, key)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return
    print("decisive step:     %s (p = %.2f)" % (result.when, result.probabilities[result.when]))
    print("responsible agent: %s" % result.who)
    print("findings (event <- source: label, p):")
    for f in result.graph.findings:
        print("  %-8s <- %-8s %s (%.2f)" % (f.event, f.uses, f.label, f.p))
    print("Jev requests: %d, input tokens: %d" % (result.requests, result.input_tokens))


if __name__ == "__main__":
    main()
