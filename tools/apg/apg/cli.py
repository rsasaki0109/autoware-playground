from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compare import compare_run_records, format_compare_text
from .leaderboard import emit_leaderboard
from .leaderboard_diff import diff_paths, format_diff_markdown
from .preflight import format_preflight_text, preflight_for_runner
from .report import write_report
from .run import ApgRunError, run_demo, run_dry_run, run_real
from .schema import (
    find_repo_root,
    iter_benchmark_manifests,
    iter_experiment_manifests,
    load_document,
    validate_path,
)


DEMOS = {
    "lane_change_cut_in": {
        "benchmark": "benchmarks/planning/lane_change_cut_in_001",
        "experiments": [
            "experiments/planning/autoware_baseline",
            "experiments/planning/safe_gap_ttc_planner",
        ],
    },
}


def _emit_validation_text(result, *, strict: bool) -> int:
    for warning in result.warnings:
        if strict:
            print(f"error: {warning}", file=sys.stderr)
        else:
            print(f"warning: {warning}", file=sys.stderr)
    if result.errors:
        for error in result.errors:
            print(f"error: {error}", file=sys.stderr)
    total = len(result.errors) + (len(result.warnings) if strict else 0)
    if total:
        print(f"validation failed: {total} issue(s)", file=sys.stderr)
        return 1
    print(f"validated {result.files} schema-backed file(s)")
    return 0


def _emit_validation_json(result, *, strict: bool) -> int:
    payload = {
        "files": result.files,
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "strict": strict,
    }
    payload["ok"] = not result.errors and (not strict or not result.warnings)
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["ok"] else 1


def _run_validation(
    path: Path,
    *,
    strict: bool,
    as_json: bool,
    allow_dry_run_baselines: bool = False,
) -> int:
    result = validate_path(path, allow_dry_run_baselines=allow_dry_run_baselines)
    if as_json:
        return _emit_validation_json(result, strict=strict)
    return _emit_validation_text(result, strict=strict)


def cmd_validate(args: argparse.Namespace) -> int:
    return _run_validation(Path(args.path), strict=False, as_json=args.json)


def cmd_lint(args: argparse.Namespace) -> int:
    return _run_validation(
        Path(args.path),
        strict=True,
        as_json=args.json,
        allow_dry_run_baselines=args.allow_dry_run_baselines,
    )


def cmd_list(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd())
    if args.entity == "benchmarks":
        for path in iter_benchmark_manifests(root):
            manifest = load_document(path)
            rel = path.parent.relative_to(root).as_posix()
            runner = manifest.get("runner", {}).get("type", "unknown")
            print(f"{rel}\t{manifest.get('task')}\t{manifest.get('name')}\t{runner}")
        return 0
    if args.entity == "experiments":
        for path in iter_experiment_manifests(root):
            manifest = load_document(path)
            rel = path.parent.relative_to(root).as_posix()
            print(f"{rel}\t{manifest.get('task')}\t{manifest.get('name')}\t{manifest.get('mode')}")
        return 0
    raise AssertionError(args.entity)


def cmd_run(args: argparse.Namespace) -> int:
    try:
        if args.dry_run:
            result_path = run_dry_run(
                Path(args.benchmark),
                Path(args.experiment),
                output_root=Path(args.output) if args.output else None,
                headless=args.headless,
                seed=args.seed,
                report=args.report,
            )
        else:
            result_path = run_real(
                Path(args.benchmark),
                Path(args.experiment),
                output_root=Path(args.output) if args.output else None,
                headless=args.headless,
                seed=args.seed,
                report=args.report,
            )
    except (ApgRunError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(result_path)
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd())
    if args.benchmark:
        manifest_path = Path(args.benchmark)
        if manifest_path.is_dir():
            manifest_path = manifest_path / "benchmark.yaml"
        runner_type = (load_document(manifest_path).get("runner") or {}).get("type")
    else:
        runner_type = args.runner
    if not runner_type:
        print("error: pass --runner or a benchmark to infer the runner type", file=sys.stderr)
        return 2
    report = preflight_for_runner(runner_type, root=root)
    if args.json:
        print(json.dumps(report.to_dict(), sort_keys=True, indent=2))
    else:
        print(format_preflight_text(report), end="")
    return 0 if report.ok else 1


def cmd_leaderboard(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd())
    output = emit_leaderboard(root, fmt=args.format, link_base=args.link_base)
    print(output, end="")
    return 0


def cmd_leaderboard_diff(args: argparse.Namespace) -> int:
    try:
        diff = diff_paths(Path(args.base), Path(args.head))
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(diff.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_diff_markdown(diff), end="")
    if args.fail_on_change and diff.has_changes:
        return 1
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    try:
        report_path = write_report(Path(args.result), Path(args.output) if args.output else None)
    except Exception as exc:
        print(f"error: could not write report: {exc}", file=sys.stderr)
        return 1
    print(report_path)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    try:
        result = compare_run_records(Path(args.left), Path(args.right))
    except Exception as exc:
        print(f"error: could not compare run records: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    else:
        print(format_compare_text(result), end="")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    spec = DEMOS.get(args.demo)
    if spec is None:
        print(f"error: unknown demo {args.demo!r} (known: {sorted(DEMOS)})", file=sys.stderr)
        return 2
    if not args.dry_run:
        print("error: apg demo only supports --dry-run in MVP", file=sys.stderr)
        return 2
    try:
        records = run_demo(
            spec["benchmark"],
            spec["experiments"],
            headless=args.headless,
            seed=args.seed,
            report=args.report,
        )
    except (ApgRunError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for record in records:
        print(record)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="apg")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate manifests.")
    validate.add_argument("path", nargs="?", default=".")
    validate.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    validate.set_defaults(func=cmd_validate)

    lint = subparsers.add_parser("lint", help="Strict validation (warnings become errors).")
    lint.add_argument("path", nargs="?", default=".")
    lint.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    lint.add_argument(
        "--allow-dry-run-baselines",
        action="store_true",
        help=(
            "Skip the dry_run baseline warning. Use in CI while baselines are still"
            " stubs; remove once real RunRecords replace them."
        ),
    )
    lint.set_defaults(func=cmd_lint)

    list_cmd = subparsers.add_parser("list", help="List known repository objects.")
    list_cmd.add_argument("entity", choices=["benchmarks", "experiments"])
    list_cmd.set_defaults(func=cmd_list)

    run = subparsers.add_parser("run", help="Run a benchmark.")
    run.add_argument("benchmark")
    run.add_argument("--experiment", required=True)
    run.add_argument("--headless", action="store_true")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--seed", type=int)
    run.add_argument("--output")
    run.add_argument("--report", action="store_true")
    run.set_defaults(func=cmd_run)

    report = subparsers.add_parser("report", help="Generate a static report from result.json.")
    report.add_argument("result")
    report.add_argument("--output")
    report.set_defaults(func=cmd_report)

    compare = subparsers.add_parser("compare", help="Compare two run records.")
    compare.add_argument("left")
    compare.add_argument("right")
    compare.add_argument("--json", action="store_true")
    compare.set_defaults(func=cmd_compare)

    demo = subparsers.add_parser("demo", help="Run a curated demo benchmark/experiment combo.")
    demo.add_argument("demo", choices=sorted(DEMOS))
    demo.add_argument("--dry-run", action="store_true")
    demo.add_argument("--headless", action="store_true")
    demo.add_argument("--seed", type=int)
    demo.add_argument("--report", action="store_true")
    demo.set_defaults(func=cmd_demo)

    leaderboard = subparsers.add_parser(
        "leaderboard",
        help="Aggregate baselines and run records into a benchmark x experiment table.",
    )
    leaderboard.add_argument(
        "--format",
        choices=["text", "markdown", "json", "html"],
        default="text",
        help="Output format (default: text).",
    )
    leaderboard.add_argument(
        "--link-base",
        default=".",
        help=(
            "Prefix prepended to report.html / result.json links in html output."
            " Use '..' when writing the page to reports/leaderboard.html so that"
            " links escape that directory and reach files at the repo root."
        ),
    )
    leaderboard.set_defaults(func=cmd_leaderboard)

    leaderboard_diff = subparsers.add_parser(
        "leaderboard-diff",
        help=(
            "Diff two leaderboard JSON dumps. Useful in CI pull_request jobs"
            " to surface benchmark regressions introduced by a PR."
        ),
    )
    leaderboard_diff.add_argument("base", help="Baseline leaderboard JSON path (e.g. main).")
    leaderboard_diff.add_argument("head", help="Head leaderboard JSON path (e.g. this PR).")
    leaderboard_diff.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    leaderboard_diff.add_argument(
        "--fail-on-change",
        action="store_true",
        help="Exit non-zero when any benchmark row changed (useful as a PR gate).",
    )
    leaderboard_diff.set_defaults(func=cmd_leaderboard_diff)

    preflight = subparsers.add_parser(
        "preflight",
        help="Check the local environment for a runner before non-dry-run execution.",
    )
    preflight.add_argument("benchmark", nargs="?", help="Benchmark dir or benchmark.yaml")
    preflight.add_argument("--runner", help="Runner type (overrides benchmark.runner.type)")
    preflight.add_argument("--json", action="store_true")
    preflight.set_defaults(func=cmd_preflight)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
