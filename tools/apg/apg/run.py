from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from .report import write_report
from .schema import find_repo_root, load_document, validate_path


class ApgRunError(RuntimeError):
    pass


def _git_value(root: Path, *args: str) -> str | None:
    try:
        output = subprocess.check_output(
            ["git", *args],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None
    return output or None


def _asset_hashes(root: Path, benchmark: dict[str, Any]) -> dict[str, str | None]:
    hashes: dict[str, str | None] = {}
    for asset_name, asset_path in benchmark.get("assets", {}).items():
        if not asset_path or not isinstance(asset_path, str) or asset_path.startswith("$"):
            continue
        manifest_path = root / asset_path
        if not manifest_path.is_file():
            hashes[f"{asset_name}_sha256"] = None
            continue
        asset_manifest = load_document(manifest_path)
        hashes[f"{asset_name}_sha256"] = asset_manifest.get("integrity", {}).get("sha256")
    return hashes


def _dry_run_metrics(benchmark: dict[str, Any]) -> dict[str, Any]:
    metrics: dict[str, Any] = {"dry_run": True}
    gates = benchmark.get("gates", {})
    for group in ("required", "diagnostic"):
        for gate in gates.get(group, []) or []:
            metrics.setdefault(gate.get("name"), None)
    return metrics


def _copy_latest(result_path: Path, report: bool, failure_cards: list[Path]) -> None:
    latest = result_path.parents[1] / "latest"
    if latest.is_symlink() or latest.is_file():
        latest.unlink()
    elif latest.is_dir():
        shutil.rmtree(latest)
    latest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(result_path, latest / "result.json")
    if report and (result_path.parent / "report.html").is_file():
        shutil.copy2(result_path.parent / "report.html", latest / "report.html")
    if failure_cards:
        cards_dir = latest / "failure_cards"
        cards_dir.mkdir(exist_ok=True)
        for card in failure_cards:
            shutil.copy2(card, cards_dir / card.name)


def _write_failure_cards(
    run_dir: Path,
    *,
    benchmark_name: str,
    experiment_name: str,
    run_id: str,
    failures: Iterable[str],
) -> list[Path]:
    failures = list(failures)
    if not failures:
        return []
    cards_dir = run_dir / "failure_cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for tag in failures:
        card = {
            "api_version": "apg/v0",
            "kind": "FailureCard",
            "failure": {
                "benchmark": benchmark_name,
                "experiment": experiment_name,
                "tag": tag,
                "run_id": run_id,
                "time_range_sec": None,
                "symptoms": [
                    "Stub generated automatically from a dry-run RunRecord.",
                    "Replace with real symptoms once a real runner attaches.",
                ],
                "artifacts": {
                    "rosbag": None,
                    "plot": None,
                    "rviz_config": None,
                },
                "suggested_next_scenarios": [],
                "notes": (
                    "Dry-run mode emits a sim_invalid stub by default."
                    " Update or remove this card after a real benchmark run."
                ),
            },
        }
        card_path = cards_dir / f"{tag}.yaml"
        card_path.write_text(
            yaml.safe_dump(card, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        written.append(card_path)
    return written


def _resolve_manifest_path(path: Path, basename: str) -> tuple[Path, Path]:
    if path.is_dir():
        return path / basename, path
    return path, path.parent


def run_dry_run(
    benchmark_path: Path,
    experiment_path: Path,
    *,
    output_root: Path | None = None,
    headless: bool = False,
    seed: int | None = None,
    report: bool = False,
) -> Path:
    root = find_repo_root(benchmark_path)
    benchmark_path = benchmark_path.resolve()
    experiment_path = experiment_path.resolve()

    benchmark_manifest_path, benchmark_dir = _resolve_manifest_path(
        benchmark_path, "benchmark.yaml"
    )
    experiment_manifest_path, experiment_dir = _resolve_manifest_path(
        experiment_path, "experiment.yaml"
    )

    validation = validate_path(benchmark_dir)
    validation.extend(validate_path(experiment_dir))
    if not validation.ok:
        raise ApgRunError("\n".join(validation.errors))

    benchmark = load_document(benchmark_manifest_path)
    experiment = load_document(experiment_manifest_path)
    if benchmark.get("task") != experiment.get("task"):
        raise ApgRunError(
            f"benchmark task {benchmark.get('task')!r} does not match"
            f" experiment task {experiment.get('task')!r}"
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"{timestamp}_{benchmark['name']}_{experiment['name']}_dry_run"
    runs_root = output_root or (root / "runs")
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    benchmark_rel = benchmark_dir.relative_to(root).as_posix()
    experiment_rel = experiment_dir.relative_to(root).as_posix()
    command = f"apg run {benchmark_rel} --experiment {experiment_rel} --dry-run"
    if headless:
        command += " --headless"
    if seed is not None:
        command += f" --seed {seed}"
    if report:
        command += " --report"

    failures = ["sim_invalid"]
    failure_card_paths = _write_failure_cards(
        run_dir,
        benchmark_name=benchmark["name"],
        experiment_name=experiment["name"],
        run_id=run_id,
        failures=failures,
    )
    failure_card_rels = [
        path.relative_to(run_dir).as_posix() for path in failure_card_paths
    ]

    result = {
        "api_version": "apg/v0",
        "kind": "RunRecord",
        "run_id": run_id,
        "experiment": experiment["name"],
        "benchmark": benchmark["name"],
        "mode": experiment["mode"],
        "git": {
            "autoware_playground": _git_value(root, "rev-parse", "--short", "HEAD"),
            "autoware_universe": None,
        },
        "runtime": {
            "container_digest": None,
            "ros_distro": "not_executed",
            "headless": headless,
            "runner": benchmark.get("runner", {}).get("type"),
        },
        "assets": _asset_hashes(root, benchmark),
        "metrics": _dry_run_metrics(benchmark),
        "failures": failures,
        "artifacts": {
            "rosbag": None,
            "report": "report.html" if report else None,
            "plots": None,
            "failure_cards": failure_card_rels or None,
        },
        "execution": {
            "status": "not_executed",
            "dry_run": True,
            "seed": seed if seed is not None else experiment.get("reproducibility", {}).get("random_seed"),
        },
        "reproduce": command,
    }

    result_path = run_dir / "result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report:
        write_report(result_path)
    _copy_latest(result_path, report=report, failure_cards=failure_card_paths)
    return result_path


def run_demo(
    benchmark_rel: str,
    experiment_rels: Iterable[str],
    *,
    headless: bool = False,
    seed: int | None = None,
    report: bool = False,
) -> list[Path]:
    root = find_repo_root(Path.cwd())
    benchmark_path = (root / benchmark_rel).resolve()
    records: list[Path] = []
    for experiment_rel in experiment_rels:
        experiment_path = (root / experiment_rel).resolve()
        records.append(
            run_dry_run(
                benchmark_path,
                experiment_path,
                headless=headless,
                seed=seed,
                report=report,
            )
        )
    return records
