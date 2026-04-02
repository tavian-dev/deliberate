"""CLI entry point for deliberate."""

import argparse
import json
import sys

from deliberate import WeightClass
from deliberate.classify import classify


def cmd_classify(args):
    """Classify a task's complexity."""
    context = {}
    if args.file_count is not None:
        context["file_count"] = args.file_count
    if args.familiarity is not None:
        context["familiarity"] = args.familiarity

    result = classify(args.description, context=context or None)

    if args.json:
        output = {
            "weight_class": result.weight_class.value,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "signals": {k: round(v, 3) for k, v in result.signals.items()},
        }
        print(json.dumps(output, indent=2))
    else:
        emoji = {"act": "⚡", "brief": "📋", "campaign": "🏗️", "deliberate": "🔬"}
        e = emoji.get(result.weight_class.value, "")
        print(f"{e} Class {result.weight_class.name}: {result.weight_class.value}")
        print(f"  Confidence: {result.confidence:.0%}")
        print(f"  {result.reasoning}")
        if args.verbose:
            print(f"\n  Signals:")
            for k, v in result.signals.items():
                bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
                print(f"    {k:15s} {bar} {v:.2f}")


def main():
    parser = argparse.ArgumentParser(
        prog="deliberate",
        description="Adaptive planning for autonomous AI agents.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # classify
    cls_parser = subparsers.add_parser("classify", help="Classify task complexity")
    cls_parser.add_argument("description", help="Task description")
    cls_parser.add_argument("--file-count", "-f", type=int, help="Estimated file count")
    cls_parser.add_argument("--familiarity", type=float, help="Area familiarity 0.0-1.0")
    cls_parser.add_argument("--json", action="store_true", help="JSON output")
    cls_parser.add_argument("--verbose", "-v", action="store_true", help="Show signal details")

    args = parser.parse_args()

    if args.command == "classify":
        cmd_classify(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
