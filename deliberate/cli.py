"""CLI entry point for deliberate."""

import argparse
import json
import sys
from pathlib import Path

from deliberate import WeightClass
from deliberate.classify import get_guide, check_escalation, CLASS_ORDER
from deliberate.process import (
    create_brief, complete_item, get_brief_status,
    create_campaign, campaign_step, campaign_status,
)
from deliberate.templates import find_step_guide


def cmd_guide(args):
    """Print the weight class guide."""
    if args.json:
        print(json.dumps({"guide": get_guide()}))
    else:
        print(get_guide())


def cmd_guide(args):
    """Print the weight class guide."""
    if args.json:
        print(json.dumps({"guide": get_guide()}))
    else:
        print(get_guide())


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
        try:
            guide_path = find_step_guide("brief")
            print(f"   Working guide: {guide_path}")
        except FileNotFoundError:
            pass


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


def main():
    parser = argparse.ArgumentParser(
        prog="deliberate",
        description="Adaptive planning for AI coding agents.",
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument("--version", action="version", version="deliberate 2.0.0")
    subparsers = parser.add_subparsers(dest="command")

    # guide
    guide_parser = subparsers.add_parser("guide", help="Show weight class reference guide")
    guide_parser.add_argument("--json", action="store_true", help="JSON output")

    # classify (deprecated alias for guide)
    cls_parser = subparsers.add_parser("classify", help="Deprecated: use 'guide' instead")
    cls_parser.add_argument("--json", action="store_true", help="JSON output")

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
    elif args.command == "guide":
        cmd_guide(args)
    elif args.command == "classify":
        print("Note: 'classify' is deprecated. Use 'deliberate guide' instead.\n")
        cmd_guide(args)
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
            guide_path = find_step_guide("spec")
            print(f"🏗️ Campaign created: {output_dir / args.name}")
            print(f"   Next step: spec")
            print(f"   Read the step guide: {guide_path}")
            print(f"   Then run: deliberate step spec --campaign {output_dir / args.name} --content \"...\"")

    elif args.command == "step":
        campaign_dir = Path(args.campaign)
        if args.content:
            content = args.content
        elif not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            content = ""

        # Empty content — show the step guide instead of writing empty artifact
        if not content.strip():
            try:
                guide_path = find_step_guide(args.step_name)
                template_path = Path(__file__).parent.parent / "templates" / f"{args.step_name}.md"
                print(f"📖 Step: {args.step_name}")
                print(f"   Guide (how to approach this step): {guide_path}")
                if template_path.exists():
                    print(f"   Template (output format): {template_path}")
                print(f"\n   Read the guide, write your {args.step_name}, then run:")
                print(f"   deliberate step {args.step_name} --campaign {campaign_dir} --content \"...\"")
            except FileNotFoundError:
                print(f"No step guide found for '{args.step_name}'.", file=sys.stderr)
            sys.exit(0)
        try:
            result = campaign_step(campaign_dir, args.step_name, content)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"✅ {args.step_name}.md written to {campaign_dir}")
                next_steps = {"spec": "plan", "plan": "tasks", "tasks": None}
                nxt = next_steps.get(args.step_name)
                if nxt:
                    guide_path = find_step_guide(nxt)
                    print(f"   Next step: {nxt}")
                    print(f"   Read the guide: {guide_path}")
                    print(f"   Then run: deliberate step {nxt} --campaign {campaign_dir} --content \"...\"")
                else:
                    print(f"   All planning artifacts complete. Implement the tasks.")
        except ValueError as e:
            print(f"❌ Cannot execute '{args.step_name}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
