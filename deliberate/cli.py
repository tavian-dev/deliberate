"""CLI entry point for deliberate."""

import argparse
import json
import sys
from pathlib import Path

from deliberate import WeightClass
from deliberate.classify import classify, check_escalation, CLASS_ORDER
from deliberate.process import (
    create_brief, complete_item, get_brief_status,
    create_campaign, campaign_step, campaign_status,
)


def cmd_brief(args):
    """Create a Class B brief."""
    output_dir = Path(args.dir)
    items = args.items.split(",") if args.items else None

    brief = create_brief(
        args.description,
        output_dir=output_dir,
        checklist_items=items,
        done_criteria=args.done_criteria,
    )

    if args.json:
        status = get_brief_status(output_dir)
        print(json.dumps(status, indent=2))
    else:
        print(f"📋 Brief created: {output_dir / 'brief.md'}")
        print(f"   {len(brief.checklist)} items:")
        for item in brief.checklist:
            print(f"   - [{item.id}] {item.description}")
        print(f"   Done when: {brief.done_criteria}")


def cmd_check(args):
    """Mark a brief checklist item as done."""
    output_dir = Path(args.dir)
    try:
        brief = complete_item(output_dir, args.item_id)
        status = get_brief_status(output_dir)
        emoji = "✅" if status["status"] == "completed" else "☑️"
        print(f"{emoji} Marked {args.item_id} done ({status['done']}/{status['total']})")
        if status["status"] == "completed":
            print("🎉 Brief complete!")
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_status(args):
    """Show brief status."""
    output_dir = Path(args.dir)
    status = get_brief_status(output_dir)

    if args.json:
        print(json.dumps(status, indent=2))
        return

    if status["status"] == "none":
        print("No active brief.")
        return

    emoji = "✅" if status["status"] == "completed" else "📋"
    print(f"{emoji} Brief: {status['done']}/{status['total']} done ({status['status']})")
    for item in status.get("items", []):
        mark = "✓" if item["done"] else " "
        print(f"  [{mark}] [{item['id']}] {item['description']}")


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

    # brief
    brief_parser = subparsers.add_parser("brief", help="Create a Class B brief with checklist")
    brief_parser.add_argument("description", help="Task description")
    brief_parser.add_argument("--dir", "-d", default=".", help="Output directory")
    brief_parser.add_argument("--items", "-i", help="Comma-separated checklist items")
    brief_parser.add_argument("--done-criteria", help="Custom done criteria")
    brief_parser.add_argument("--json", action="store_true", help="JSON output")

    # check
    check_parser = subparsers.add_parser("check", help="Mark a brief item as done")
    check_parser.add_argument("item_id", help="Item ID to mark done (e.g. B001)")
    check_parser.add_argument("--dir", "-d", default=".", help="Brief directory")
    check_parser.add_argument("--json", action="store_true", help="JSON output")

    # status
    status_parser = subparsers.add_parser("status", help="Show brief status")
    status_parser.add_argument("--dir", "-d", default=".", help="Brief directory")
    status_parser.add_argument("--json", action="store_true", help="JSON output")

    # campaign
    camp_parser = subparsers.add_parser("campaign", help="Create a Class C campaign")
    camp_parser.add_argument("name", help="Campaign name (slug)")
    camp_parser.add_argument("description", help="What this campaign is about")
    camp_parser.add_argument("--dir", "-d", default=".deliberate/active", help="Campaigns directory")
    camp_parser.add_argument("--json", action="store_true")

    # step
    step_parser = subparsers.add_parser("step", help="Execute a campaign step (spec/plan/tasks)")
    step_parser.add_argument("step_name", choices=["spec", "plan", "tasks"], help="Step to execute")
    step_parser.add_argument("--campaign", "-c", required=True, help="Campaign directory")
    step_parser.add_argument("--content", help="Content for the artifact (reads stdin if omitted)")
    step_parser.add_argument("--json", action="store_true")

    # escalation check
    esc_parser = subparsers.add_parser("check-escalation", help="Check if weight class should change")
    esc_parser.add_argument("current_class", choices=["A", "B", "C", "D"], help="Current weight class")
    esc_parser.add_argument("--attempts", "-a", type=int, default=1, help="Number of attempts so far")
    esc_parser.add_argument("--scope-grew", action="store_true", help="Scope grew during execution")
    esc_parser.add_argument("--actual-files", type=int, help="Actual files affected (for simplification)")
    esc_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "check-escalation":
        wc_map = {"A": WeightClass.A, "B": WeightClass.B, "C": WeightClass.C, "D": WeightClass.D}
        result = check_escalation(
            wc_map[args.current_class],
            attempts=args.attempts,
            scope_grew=args.scope_grew,
            actual_files=args.actual_files,
        )
        if result is None:
            if args.json:
                print(json.dumps({"change": False}))
            else:
                print("✅ No change recommended. Current weight class is appropriate.")
        else:
            if args.json:
                print(json.dumps({"change": True, "recommendation": result["recommendation"].value, "reason": result["reason"]}))
            else:
                emoji = "⬆️" if CLASS_ORDER.index(result["recommendation"]) > CLASS_ORDER.index(wc_map[args.current_class]) else "⬇️"
                print(f"{emoji} Recommendation: change to Class {result['recommendation'].name} ({result['recommendation'].value})")
                print(f"   {result['reason']}")
    elif args.command == "classify":
        cmd_classify(args)
    elif args.command == "brief":
        cmd_brief(args)
    elif args.command == "check":
        cmd_check(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "campaign":
        output_dir = Path(args.dir)
        result = create_campaign(args.name, args.description, output_dir)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"🏗️ Campaign created: {output_dir / args.name}")
            print(f"   Next: deliberate step spec --campaign {output_dir / args.name}")
    elif args.command == "step":
        campaign_dir = Path(args.campaign)
        content = args.content or sys.stdin.read()
        try:
            result = campaign_step(campaign_dir, args.step_name, content)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"✅ {args.step_name}.md written to {campaign_dir}")
                next_steps = {"spec": "plan", "plan": "tasks", "tasks": "implement"}
                nxt = next_steps.get(args.step_name)
                if nxt:
                    print(f"   Next: deliberate step {nxt} --campaign {campaign_dir}")
        except ValueError as e:
            print(f"❌ Cannot execute '{args.step_name}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
