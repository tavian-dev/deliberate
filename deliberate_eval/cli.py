"""CLI entry point for deliberate-eval."""

import argparse
import sys
from pathlib import Path

from deliberate_eval import AgentType, Treatment


def cmd_run(args: argparse.Namespace) -> None:
    """Run the eval."""
    from deliberate_eval.runner import run_pilot
    from deliberate_eval.tasks import load_tasks

    tasks_path = Path(args.tasks)
    output_path = Path(args.output)
    eval_dir = Path(args.eval_dir) if args.eval_dir else None
    clone_dir = Path(args.clone_dir) if args.clone_dir else None

    agent = AgentType(args.agent)

    print(f"Running eval: {tasks_path}")
    tasks = load_tasks(tasks_path)
    print(f"  Tasks: {len(tasks)}")
    print(f"  Agent: {agent.value}")
    print(f"  Seeds: {args.seeds}")
    print(f"  Total runs: {len(tasks) * 2 * args.seeds}")
    print(f"  Output: {output_path}")
    print()

    runs = run_pilot(
        tasks_path=tasks_path,
        output_path=output_path,
        agent=agent,
        seeds=args.seeds,
        eval_dir=eval_dir,
        clone_dir=clone_dir,
        agent_timeout=args.timeout,
    )

    passed = sum(1 for r in runs if r.trajectory.passed)
    failed = sum(1 for r in runs if r.status == "completed" and not r.trajectory.passed)
    errors = sum(1 for r in runs if r.status == "failed")
    print(f"\nDone: {passed} passed, {failed} failed, {errors} errors")
    print(f"Results: {output_path}")


def cmd_report(args: argparse.Namespace) -> None:
    """Generate a comparison report."""
    from deliberate_eval.report import load_runs, format_comparison, format_per_task
    from deliberate_eval.metrics import compare_treatments

    runs = load_runs(Path(args.results))
    comp = compare_treatments(runs)

    print(format_comparison(comp))
    if args.per_task:
        print(format_per_task(runs))


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate tasks in a JSONL file."""
    from deliberate_eval.tasks import load_tasks, validate_task

    tasks = load_tasks(Path(args.tasks))
    all_ok = True
    for task in tasks:
        errors = validate_task(task)
        if errors:
            all_ok = False
            for e in errors:
                print(f"  ERROR: {e}")
        else:
            print(f"  OK: {task.id} [{task.difficulty}]")

    if all_ok:
        print(f"\nAll {len(tasks)} tasks valid.")
    else:
        print(f"\nSome tasks have errors.")
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="deliberate-eval",
        description="Evaluate whether AI planning tools improve agent coding outcomes.",
    )
    sub = parser.add_subparsers(dest="command")

    # run
    p_run = sub.add_parser("run", help="Run the eval")
    p_run.add_argument("tasks", help="Path to tasks JSONL file")
    p_run.add_argument("-o", "--output", default="results.jsonl", help="Output JSONL path")
    p_run.add_argument("-a", "--agent", default="claude", choices=["claude", "codex"])
    p_run.add_argument("-s", "--seeds", type=int, default=3, help="Seeds per treatment")
    p_run.add_argument("-t", "--timeout", type=int, default=300, help="Agent timeout (seconds)")
    p_run.add_argument("--eval-dir", help="Base eval directory (for patches, etc.)")
    p_run.add_argument("--clone-dir", help="Directory with pre-cloned repos")
    p_run.set_defaults(func=cmd_run)

    # report
    p_report = sub.add_parser("report", help="Generate comparison report")
    p_report.add_argument("results", help="Path to results JSONL file")
    p_report.add_argument("--per-task", action="store_true", help="Show per-task breakdown")
    p_report.set_defaults(func=cmd_report)

    # validate
    p_validate = sub.add_parser("validate", help="Validate tasks JSONL")
    p_validate.add_argument("tasks", help="Path to tasks JSONL file")
    p_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
