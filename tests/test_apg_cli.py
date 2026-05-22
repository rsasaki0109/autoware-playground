from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "apg"))

from apg.cli import main
from apg.compare import compare_run_records
from apg.report import write_report
from apg.run import run_demo, run_dry_run
from apg.schema import (
    find_repo_root,
    load_failure_taxonomy,
    validate_manifest,
    validate_path,
)


def test_find_repo_root():
    assert find_repo_root(ROOT / "benchmarks" / "planning" / "lane_change_cut_in_001") == ROOT


def test_repository_validation_passes():
    result = validate_path(ROOT)
    assert result.ok, "\n".join(result.errors)
    assert result.files >= 30


def test_list_benchmarks_and_experiments(capsys, monkeypatch):
    monkeypatch.chdir(ROOT)
    assert main(["list", "benchmarks"]) == 0
    benchmark_output = capsys.readouterr().out
    assert "benchmarks/planning/lane_change_cut_in_001" in benchmark_output

    assert main(["list", "experiments"]) == 0
    experiment_output = capsys.readouterr().out
    assert "experiments/planning/safe_gap_ttc_planner" in experiment_output


def test_dry_run_writes_result_report_and_failure_card(tmp_path):
    result_path = run_dry_run(
        ROOT / "benchmarks" / "planning" / "lane_change_cut_in_001",
        ROOT / "experiments" / "planning" / "safe_gap_ttc_planner",
        output_root=tmp_path,
        headless=True,
        seed=7,
        report=True,
    )
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["kind"] == "RunRecord"
    assert result["execution"]["dry_run"] is True
    assert result["execution"]["seed"] == 7
    assert result["benchmark"] == "lane_change_cut_in_001"
    assert result["experiment"] == "safe_gap_ttc_planner"
    assert (result_path.parent / "report.html").is_file()
    assert (tmp_path / "latest" / "result.json").is_file()
    assert (tmp_path / "latest" / "report.html").is_file()

    card_paths = result["artifacts"]["failure_cards"]
    assert card_paths and card_paths == ["failure_cards/sim_invalid.yaml"]
    card = yaml.safe_load((result_path.parent / "failure_cards" / "sim_invalid.yaml").read_text())
    assert card["kind"] == "FailureCard"
    assert card["failure"]["tag"] == "sim_invalid"
    assert (tmp_path / "latest" / "failure_cards" / "sim_invalid.yaml").is_file()

    report_html = (result_path.parent / "report.html").read_text(encoding="utf-8")
    assert "Failure Cards" in report_html
    assert "failure_cards/sim_invalid.yaml" in report_html


def test_report_command_accepts_run_directory(tmp_path):
    result_path = run_dry_run(
        ROOT / "benchmarks" / "localization" / "lidar_localization_replay_001",
        ROOT / "experiments" / "localization" / "icp_registration_toy",
        output_root=tmp_path,
    )
    report_path = write_report(result_path.parent)
    assert report_path.is_file()
    assert "APG Run Report" in report_path.read_text(encoding="utf-8")


def test_lint_passes_in_repo(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    assert main(["lint", "."]) == 0
    out = capsys.readouterr().out
    assert "validated" in out


def test_validate_json_output(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    assert main(["validate", ".", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["files"] >= 30
    assert payload["errors"] == []


def test_unknown_failure_tag_rejected(tmp_path):
    benchmark_dir = tmp_path / "benchmarks" / "planning" / "bad_case"
    benchmark_dir.mkdir(parents=True)
    (benchmark_dir / "README.md").write_text(
        "\n".join(
            f"## {section}"
            for section in (
                "Purpose",
                "Autoware Slot",
                "Assets",
                "How To Run Smoke Benchmark",
                "Expected Result",
                "Known Failure Modes",
                "Files You Are Allowed To Edit",
            )
        ),
        encoding="utf-8",
    )
    (benchmark_dir / "metrics.yaml").write_text(
        "api_version: apg/v0\nkind: MetricConfig\nsources: []\nmetrics: {}\n",
        encoding="utf-8",
    )
    (benchmark_dir / "assets.yaml").write_text(
        "api_version: apg/v0\nkind: BenchmarkAssets\nassets: {}\n",
        encoding="utf-8",
    )
    (benchmark_dir / "expected_failures.yaml").write_text(
        "api_version: apg/v0\nkind: ExpectedFailures\nexpected_failures:\n  - tag: not_a_real_tag\n    reason: testing\n",
        encoding="utf-8",
    )

    benchmark_doc = {
        "api_version": "apg/v0",
        "kind": "Benchmark",
        "name": "bad_case",
        "task": "planning",
        "runner": {"type": "scenario_simulator_v2"},
        "assets": {},
        "metrics": {"config": "metrics.yaml"},
        "gates": {"required": [{"name": "ok", "op": "==", "value": True}]},
        "failure_taxonomy": ["this_tag_does_not_exist"],
    }
    (benchmark_dir / "benchmark.yaml").write_text(
        yaml.safe_dump(benchmark_doc, sort_keys=False),
        encoding="utf-8",
    )

    # Symlink schemas + contracts + AGENTS.md so the temp root looks like a repo.
    (tmp_path / "schemas").symlink_to(ROOT / "schemas")
    (tmp_path / "contracts").symlink_to(ROOT / "contracts")
    (tmp_path / "AGENTS.md").symlink_to(ROOT / "AGENTS.md")

    result = validate_path(benchmark_dir)
    error_text = "\n".join(result.errors)
    assert "unknown tag 'this_tag_does_not_exist'" in error_text
    assert "unknown failure tag 'not_a_real_tag'" in error_text


def test_missing_readme_section_warns(tmp_path):
    benchmark_src = ROOT / "benchmarks" / "planning" / "lane_change_cut_in_001"
    dst = tmp_path / "benchmarks" / "planning" / "lane_change_cut_in_001"
    dst.mkdir(parents=True)
    for child in benchmark_src.iterdir():
        if child.name == "README.md":
            (dst / "README.md").write_text("# Bare README without sections\n", encoding="utf-8")
        elif child.is_dir():
            (dst / child.name).symlink_to(child)
        else:
            (dst / child.name).symlink_to(child)
    (tmp_path / "schemas").symlink_to(ROOT / "schemas")
    (tmp_path / "contracts").symlink_to(ROOT / "contracts")
    (tmp_path / "AGENTS.md").symlink_to(ROOT / "AGENTS.md")
    (tmp_path / "assets").symlink_to(ROOT / "assets")

    result = validate_path(dst)
    assert any(
        "missing recommended README section '## Purpose'" in warning
        for warning in result.warnings
    )
    assert result.ok


def test_failure_taxonomy_loaded():
    tags = load_failure_taxonomy(ROOT)
    assert "collision" in tags
    assert "sim_invalid" in tags


def test_compare_run_records(tmp_path):
    left = run_dry_run(
        ROOT / "benchmarks" / "planning" / "lane_change_cut_in_001",
        ROOT / "experiments" / "planning" / "autoware_baseline",
        output_root=tmp_path / "left",
    )
    right = run_dry_run(
        ROOT / "benchmarks" / "planning" / "lane_change_cut_in_001",
        ROOT / "experiments" / "planning" / "safe_gap_ttc_planner",
        output_root=tmp_path / "right",
    )
    cmp = compare_run_records(left, right)
    assert cmp.benchmark_match is True
    assert cmp.left_run_id != cmp.right_run_id
    # both runs are dry-run so most metrics are equal/None; diff list may be empty
    assert isinstance(cmp.metric_diffs, list)
    assert cmp.failure_only_left == []
    assert cmp.failure_only_right == []


def test_demo_runs_known_demo(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(ROOT)
    records = run_demo(
        "benchmarks/planning/lane_change_cut_in_001",
        [
            "experiments/planning/autoware_baseline",
            "experiments/planning/safe_gap_ttc_planner",
        ],
        headless=True,
        report=True,
    )
    try:
        assert len(records) == 2
        for record in records:
            assert record.is_file()
    finally:
        for record in records:
            run_dir = record.parent
            import shutil

            shutil.rmtree(run_dir, ignore_errors=True)


def test_compare_cli_outputs_json(tmp_path, capsys):
    left = run_dry_run(
        ROOT / "benchmarks" / "planning" / "lane_change_cut_in_001",
        ROOT / "experiments" / "planning" / "autoware_baseline",
        output_root=tmp_path / "a",
    )
    right = run_dry_run(
        ROOT / "benchmarks" / "planning" / "lane_change_cut_in_001",
        ROOT / "experiments" / "planning" / "safe_gap_ttc_planner",
        output_root=tmp_path / "b",
    )
    assert main(["compare", str(left), str(right), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["benchmark_match"] is True
    assert "metric_diffs" in payload


def test_failure_card_schema_validates(tmp_path):
    card = {
        "api_version": "apg/v0",
        "kind": "FailureCard",
        "failure": {
            "benchmark": "lane_change_cut_in_001",
            "experiment": "safe_gap_ttc_planner",
            "tag": "near_miss",
        },
    }
    path = tmp_path / "card.yaml"
    path.write_text(yaml.safe_dump(card, sort_keys=False), encoding="utf-8")
    result = validate_manifest(ROOT, path)
    assert result.ok, "\n".join(result.errors)
