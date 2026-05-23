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
from apg.leaderboard import build_leaderboard, emit_leaderboard
from apg.preflight import preflight_for_runner
from apg.report import write_report
from apg.run import ApgRunError, run_demo, run_dry_run, run_real
from apg.runners import ApgRunnerError, runner_dry_run, runner_execute
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
    assert result["execution"]["baseline_status"] == "dry_run"
    assert result["execution"]["seed"] == 7
    assert result["runtime"]["runner"] == "scenario_simulator_v2"
    assert result["runtime"]["runner_hints"]["dispatched"] is True
    assert result["runtime"]["runner_hints"]["backend"] == "scenario_simulator_v2"
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


def test_lint_flags_dry_run_baselines(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    # Both rosbag_replay baselines (localization/ndt_baseline and
    # perception/lidar_cluster_baseline) have been promoted to real via CI.
    # The two remaining dry-run baselines target scenario_simulator_v2
    # benchmarks (planning + prediction), which still need a pinned
    # Autoware workspace to execute for real.
    assert main(["lint", "."]) == 1
    err = capsys.readouterr().err
    assert "baseline_status='dry_run'" in err
    assert err.count("baseline_status='dry_run'") == 2


def test_lint_allow_dry_run_baselines_passes(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    # With the CI-only allowance, dry-run baselines no longer fail strict lint.
    assert main(["lint", ".", "--allow-dry-run-baselines"]) == 0
    err = capsys.readouterr().err
    assert "baseline_status='dry_run'" not in err


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


def test_runner_dry_run_dispatches_rosbag_replay():
    benchmark = {
        "name": "rosbag_demo",
        "task": "localization",
        "runner": {"type": "rosbag_replay", "timeout_sec": 60},
        "assets": {"rosbag": "assets/rosbag/demo/asset.yaml"},
        "gates": {"required": [{"name": "ok", "op": "==", "value": True}]},
    }
    experiment = {"name": "ndt_baseline", "task": "localization", "mode": "offline_replay"}
    outcome = runner_dry_run(
        "rosbag_replay",
        benchmark=benchmark,
        experiment=experiment,
        headless=True,
        seed=None,
    )
    assert outcome.runner == "rosbag_replay"
    assert outcome.runtime_hints["backend"] == "rosbag_replay"
    assert outcome.runtime_hints["dispatched"] is True
    assert outcome.runtime_hints["rosbag"] == "assets/rosbag/demo/asset.yaml"
    assert outcome.metrics["dry_run"] is True
    assert outcome.failures == ["sim_invalid"]


def test_runner_dry_run_falls_back_for_planning_simulator():
    outcome = runner_dry_run(
        "planning_simulator",
        benchmark={"runner": {"type": "planning_simulator"}, "gates": {"required": []}},
        experiment={"mode": "shadow"},
        headless=False,
        seed=None,
    )
    assert outcome.runner == "planning_simulator"
    assert outcome.runtime_hints["dispatched"] is False


def test_runner_dry_run_rejects_unknown_runner():
    import pytest

    with pytest.raises(ApgRunnerError):
        runner_dry_run(
            "not_a_real_runner",
            benchmark={"runner": {"type": "not_a_real_runner"}, "gates": {"required": []}},
            experiment={"mode": "shadow"},
            headless=False,
            seed=None,
        )


def test_baseline_results_carry_baseline_status():
    for baseline in sorted((ROOT / "benchmarks").glob("*/*/baselines/*/result.json")):
        document = json.loads(baseline.read_text(encoding="utf-8"))
        assert document["execution"]["baseline_status"] in {"dry_run", "real", "unknown"}, baseline


def test_preflight_reports_missing_environment(monkeypatch):
    monkeypatch.delenv("ROS_DISTRO", raising=False)
    monkeypatch.delenv("AUTOWARE_WORKSPACE", raising=False)
    report = preflight_for_runner("scenario_simulator_v2", root=ROOT)
    assert report.ok is False
    names = {check.name for check in report.checks}
    assert {"ROS_DISTRO", "ros2", "autoware_workspace", "scenario_test_runner"}.issubset(names)


def test_preflight_rosbag_replay_does_not_require_autoware_workspace(monkeypatch):
    monkeypatch.delenv("AUTOWARE_WORKSPACE", raising=False)
    report = preflight_for_runner("rosbag_replay", root=ROOT)
    names = {check.name for check in report.checks}
    assert "autoware_workspace" not in names
    assert "scenario_test_runner" not in names


def test_runner_execute_raises_for_unconnected_runner():
    import pytest

    with pytest.raises(ApgRunnerError, match="not connected yet"):
        runner_execute(
            "scenario_simulator_v2",
            benchmark={"runner": {"type": "scenario_simulator_v2"}},
            experiment={"mode": "shadow"},
            headless=True,
            seed=None,
        )


def test_rosbag_replay_execute_errors_when_bag_missing(monkeypatch):
    import pytest

    monkeypatch.delenv("APG_DATA", raising=False)
    with pytest.raises(ApgRunnerError, match="unresolved variables|not found"):
        runner_execute(
            "rosbag_replay",
            benchmark={"runner": {"type": "rosbag_replay", "rosbag": "$APG_DATA/missing"}},
            experiment={"mode": "offline_replay"},
            headless=True,
            seed=None,
        )


def test_rosbag_replay_execute_errors_when_path_missing(tmp_path):
    import pytest

    missing = tmp_path / "no_such_bag"
    with pytest.raises(ApgRunnerError, match="not found"):
        runner_execute(
            "rosbag_replay",
            benchmark={"runner": {"type": "rosbag_replay", "rosbag": str(missing)}},
            experiment={"mode": "offline_replay"},
            headless=True,
            seed=None,
        )


def test_rosbag_replay_execute_end_to_end(tmp_path):
    import importlib.util
    import shutil as _shutil
    import sys as _sys

    import pytest

    if importlib.util.find_spec("rosbag2_py") is None:
        pytest.skip("rosbag2_py not available")
    if importlib.util.find_spec("std_msgs") is None:
        pytest.skip("std_msgs not available")
    if not _shutil.which("ros2"):
        pytest.skip("ros2 not on PATH")

    _sys.path.insert(0, str(ROOT / "tools" / "scripts"))
    try:
        from make_sample_rosbag import write_bag
    finally:
        _sys.path.pop(0)

    bag_dir = tmp_path / "sample_bag"
    write_bag(bag_dir, messages=5)

    outcome = runner_execute(
        "rosbag_replay",
        benchmark={
            "runner": {
                "type": "rosbag_replay",
                "rosbag": str(bag_dir),
                "timeout_sec": 30,
            },
            "gates": {},
        },
        experiment={"mode": "offline_replay"},
        headless=True,
        seed=None,
    )
    assert outcome.runner == "rosbag_replay"
    assert outcome.metrics["play_returncode"] == 0
    assert outcome.metrics["rosbag_message_count"] == 5
    assert outcome.metrics["rosbag_topic_count"] == 1
    assert outcome.failures == []


def test_run_real_fails_preflight(monkeypatch):
    import pytest

    monkeypatch.delenv("ROS_DISTRO", raising=False)
    monkeypatch.delenv("AUTOWARE_WORKSPACE", raising=False)
    with pytest.raises(ApgRunError, match="preflight failed"):
        run_real(
            ROOT / "benchmarks" / "planning" / "lane_change_cut_in_001",
            ROOT / "experiments" / "planning" / "autoware_baseline",
        )


def test_run_real_writes_record_when_runner_succeeds(monkeypatch, tmp_path):
    # Stub out preflight and runner_execute so we can exercise the
    # RunRecord-writing branch without launching real ROS processes.
    from apg import run as run_module
    from apg.preflight import PreflightCheck, PreflightReport
    from apg.runners.base import RunnerOutcome

    def fake_preflight(runner_type, *, root=None):
        return PreflightReport(
            runner=runner_type,
            checks=[PreflightCheck(name="stub", ok=True, detail="ok")],
        )

    def fake_execute(runner_type, *, benchmark, experiment, headless, seed):
        return RunnerOutcome(
            runner=runner_type,
            metrics={"rosbag_duration_sec": 1.5, "rosbag_message_count": 42},
            failures=[],
            runtime_hints={"backend": "rosbag_replay", "executed": True, "rosbag": "/tmp/x"},
        )

    monkeypatch.setattr(run_module, "preflight_for_runner", fake_preflight)
    monkeypatch.setattr(run_module, "runner_execute", fake_execute)
    monkeypatch.setenv("ROS_DISTRO", "jazzy")

    result_path = run_real(
        ROOT / "benchmarks" / "localization" / "lidar_localization_replay_001",
        ROOT / "experiments" / "localization" / "ndt_baseline",
        output_root=tmp_path,
    )
    assert result_path.is_file()
    record = json.loads(result_path.read_text(encoding="utf-8"))
    assert record["execution"]["dry_run"] is False
    assert record["execution"]["baseline_status"] == "real"
    assert record["execution"]["status"] == "completed"
    assert record["runtime"]["runner"] == "rosbag_replay"
    assert record["runtime"]["preflight"]["ok"] is True
    assert record["metrics"]["rosbag_duration_sec"] == 1.5


def test_apg_run_without_dry_run_uses_real_path(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    monkeypatch.delenv("ROS_DISTRO", raising=False)
    monkeypatch.delenv("AUTOWARE_WORKSPACE", raising=False)
    rc = main([
        "run",
        "benchmarks/planning/lane_change_cut_in_001",
        "--experiment",
        "experiments/planning/autoware_baseline",
    ])
    err = capsys.readouterr().err
    assert rc == 1
    assert "preflight failed" in err


def test_apg_preflight_cli(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    monkeypatch.delenv("ROS_DISTRO", raising=False)
    monkeypatch.delenv("AUTOWARE_WORKSPACE", raising=False)
    rc = main([
        "preflight",
        "benchmarks/planning/lane_change_cut_in_001",
        "--json",
    ])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["runner"] == "scenario_simulator_v2"
    assert payload["ok"] is False


def test_leaderboard_picks_baseline_and_runs(tmp_path):
    board = build_leaderboard(ROOT)
    by_key = {(e.benchmark, e.experiment): e for e in board.entries}
    # localization/ndt_baseline is a committed real baseline
    ndt = by_key[("lidar_localization_replay_001", "ndt_baseline")]
    assert ndt.source == "baseline"
    assert ndt.baseline_status == "real"
    assert ndt.status == "completed"
    # planning/autoware_baseline is still a dry-run baseline
    autoware = by_key[("lane_change_cut_in_001", "autoware_baseline")]
    assert autoware.source == "baseline"
    assert autoware.baseline_status == "dry_run"
    # safe_gap_ttc_planner has no committed baseline; row should be missing
    safe = by_key[("lane_change_cut_in_001", "safe_gap_ttc_planner")]
    assert safe.source == "missing"
    # column union includes a localization gate
    assert "pose_output_available" in board.columns


def test_leaderboard_blocks_are_per_benchmark(tmp_path):
    board = build_leaderboard(ROOT)
    benchmarks = [block.benchmark for block in board.blocks]
    assert "lidar_localization_replay_001" in benchmarks
    assert "static_obstacle_lidar_001" in benchmarks
    assert "lane_change_cut_in_001" in benchmarks
    assert "cut_in_prediction_001" in benchmarks
    # Each block has its own column list scoped to its gates + generic metrics.
    loc_block = next(b for b in board.blocks if b.benchmark == "lidar_localization_replay_001")
    assert "pose_output_available" in loc_block.columns  # localization-specific gate
    assert "no_collision" not in loc_block.columns      # planning-specific gate must not leak
    assert "play_returncode" in loc_block.columns       # generic execution column
    assert loc_block.runner == "rosbag_replay"


def test_leaderboard_markdown_has_per_benchmark_headers(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    assert main(["leaderboard", "--format", "markdown"]) == 0
    out = capsys.readouterr().out
    assert "## lidar_localization_replay_001 (localization)" in out
    assert "## lane_change_cut_in_001 (planning)" in out
    # planning columns must not appear in the localization block.
    loc_section = out.split("##")[1]
    assert "lidar_localization_replay_001" in loc_section
    assert "no_collision" not in loc_section


def test_leaderboard_json_is_parseable(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    assert main(["leaderboard", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, dict)
    assert "blocks" in payload
    assert "entries" in payload  # back-compat flat view
    assert len(payload["entries"]) >= 4
    assert len(payload["blocks"]) >= 4


def test_leaderboard_emit_helper(tmp_path):
    text = emit_leaderboard(ROOT, fmt="text")
    assert "lidar_localization_replay_001" in text
    assert "ndt_baseline" in text
    # New text format groups by benchmark header.
    assert "===" in text


def test_leaderboard_entry_links_to_record(tmp_path):
    board = build_leaderboard(ROOT)
    by_key = {(e.benchmark, e.experiment): e for e in board.entries}
    # ndt_baseline is a committed baseline; record_link must point to its result.json
    ndt = by_key[("lidar_localization_replay_001", "ndt_baseline")]
    assert ndt.record_link == (
        "benchmarks/localization/lidar_localization_replay_001"
        "/baselines/ndt_baseline/result.json"
    )
    # A missing row has no record_link.
    safe = by_key[("lane_change_cut_in_001", "safe_gap_ttc_planner")]
    assert safe.record_link is None
    assert safe.report_link is None


def test_leaderboard_html_renders_per_benchmark_headers(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    assert main(["leaderboard", "--format", "html"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("<!doctype html>")
    assert "<title>autoware-playground leaderboard</title>" in out
    assert "lidar_localization_replay_001" in out
    assert "lane_change_cut_in_001" in out
    # Runner tag rendered for rosbag_replay benchmarks
    assert "rosbag_replay" in out
    # Localization gate column header is present
    assert "pose_output_available" in out


def test_leaderboard_html_link_base_prefixes_links(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    assert main(["leaderboard", "--format", "html", "--link-base", ".."]) == 0
    out = capsys.readouterr().out
    # ndt_baseline result.json must be reachable via the link_base prefix
    expected = (
        '<a href="../benchmarks/localization/lidar_localization_replay_001'
        '/baselines/ndt_baseline/result.json">ndt_baseline</a>'
    )
    assert expected in out


def test_leaderboard_html_marks_missing_rows_without_link(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)
    assert main(["leaderboard", "--format", "html"]) == 0
    out = capsys.readouterr().out
    # safe_gap_ttc_planner has no record so the experiment cell is plain text,
    # not an anchor.
    assert "<td>safe_gap_ttc_planner</td>" in out


def test_leaderboard_html_uses_report_link_when_available(tmp_path):
    # Build a fake repo with a baseline result.json plus a sibling report.html
    # and verify the entry surfaces report_link, not just record_link.
    repo = tmp_path / "repo"
    bench_dir = repo / "benchmarks" / "fake" / "fake_bench_001"
    baseline_dir = bench_dir / "baselines" / "fake_baseline"
    baseline_dir.mkdir(parents=True)
    (bench_dir / "benchmark.yaml").write_text(
        "api_version: apg/v0\nkind: Benchmark\nname: fake_bench_001\ntask: fake\n"
        "runner:\n  type: rosbag_replay\n"
        "gates:\n  required: []\n  diagnostic: []\n",
        encoding="utf-8",
    )
    (repo / "experiments" / "fake" / "fake_baseline").mkdir(parents=True)
    (repo / "experiments" / "fake" / "fake_baseline" / "experiment.yaml").write_text(
        "api_version: apg/v0\nkind: Experiment\nname: fake_baseline\ntask: fake\n"
        "mode: shadow\nbenchmarks:\n  smoke:\n    - benchmarks/fake/fake_bench_001\n",
        encoding="utf-8",
    )
    (baseline_dir / "result.json").write_text(
        json.dumps(
            {
                "api_version": "apg/v0",
                "kind": "RunRecord",
                "run_id": "fake_run_001",
                "experiment": "fake_baseline",
                "benchmark": "fake_bench_001",
                "execution": {"baseline_status": "real", "status": "completed", "dry_run": False},
                "metrics": {},
                "failures": [],
            }
        ),
        encoding="utf-8",
    )
    (baseline_dir / "report.html").write_text("<html></html>", encoding="utf-8")
    board = build_leaderboard(repo)
    entry = next(
        e for e in board.entries if e.experiment == "fake_baseline"
    )
    assert entry.report_link == (
        "benchmarks/fake/fake_bench_001/baselines/fake_baseline/report.html"
    )


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
