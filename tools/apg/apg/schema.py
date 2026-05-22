from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


SCHEMA_BY_KIND = {
    "Asset": "asset.schema.json",
    "Benchmark": "benchmark.schema.json",
    "BenchmarkAssets": "benchmark_assets.schema.json",
    "Experiment": "experiment.schema.json",
    "ExpectedFailures": "expected_failures.schema.json",
    "FailureCard": "failure_card.schema.json",
    "MetricConfig": "metric.schema.json",
    "RunRecord": "result.schema.json",
}

EXPERIMENT_README_SECTIONS = (
    "What This Method Does",
    "Paper Summary",
    "Autoware Slot",
    "Inputs And Outputs",
    "How To Run Smoke Benchmark",
    "Expected Result",
    "Known Failure Modes",
    "Files You Are Allowed To Edit",
)

BENCHMARK_README_SECTIONS = (
    "Purpose",
    "Autoware Slot",
    "Assets",
    "How To Run Smoke Benchmark",
    "Expected Result",
    "Known Failure Modes",
    "Files You Are Allowed To Edit",
)


@dataclass
class ValidationResult:
    files: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def extend(self, other: "ValidationResult") -> None:
        self.files += other.files
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def find_repo_root(start: Path | str) -> Path:
    path = Path(start).resolve()
    if path.is_file():
        path = path.parent
    for candidate in (path, *path.parents):
        if (candidate / "schemas").is_dir() and (candidate / "AGENTS.md").is_file():
            return candidate
    raise ValueError(f"could not find autoware-playground root from {start}")


def load_document(path: Path) -> Any:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_schema(root: Path, schema_name: str) -> dict[str, Any]:
    schema_path = root / "schemas" / schema_name
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _format_schema_error(path: Path, error: Any) -> str:
    location = ".".join(str(part) for part in error.absolute_path)
    prefix = f"{path}:"
    if location:
        prefix = f"{prefix}{location}:"
    return f"{prefix} {error.message}"


def validate_manifest(root: Path, path: Path) -> ValidationResult:
    result = ValidationResult()
    try:
        document = load_document(path)
    except Exception as exc:  # pragma: no cover - exact parser messages vary.
        result.errors.append(f"{path}: could not parse: {exc}")
        return result

    if not isinstance(document, dict):
        result.errors.append(f"{path}: expected a mapping/object document")
        return result

    kind = document.get("kind")
    schema_name = SCHEMA_BY_KIND.get(kind)
    if schema_name is None:
        result.warnings.append(f"{path}: no schema registered for kind {kind!r}")
        return result

    validator = Draft202012Validator(load_schema(root, schema_name))
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    result.files += 1
    result.errors.extend(_format_schema_error(path, error) for error in errors)
    return result


def iter_benchmark_manifests(root: Path) -> list[Path]:
    return sorted((root / "benchmarks").glob("*/*/benchmark.yaml"))


def iter_experiment_manifests(root: Path) -> list[Path]:
    return sorted((root / "experiments").glob("*/*/experiment.yaml"))


def iter_asset_manifests(root: Path) -> list[Path]:
    return sorted((root / "assets").glob("*/*/asset.yaml"))


def iter_metric_configs(root: Path) -> list[Path]:
    return sorted((root / "benchmarks").glob("*/*/metrics.yaml"))


def iter_run_records(root: Path) -> list[Path]:
    benchmark_records = sorted((root / "benchmarks").glob("*/*/baselines/*/result.json"))
    run_records = sorted((root / "runs").glob("*/result.json")) if (root / "runs").is_dir() else []
    return benchmark_records + run_records


def iter_benchmark_asset_manifests(root: Path) -> list[Path]:
    return sorted((root / "benchmarks").glob("*/*/assets.yaml"))


def iter_expected_failures(root: Path) -> list[Path]:
    return sorted((root / "benchmarks").glob("*/*/expected_failures.yaml"))


def iter_failure_cards(root: Path) -> list[Path]:
    cards: list[Path] = []
    if (root / "runs").is_dir():
        cards += sorted((root / "runs").glob("*/failure_cards/*.yaml"))
    cards += sorted((root / "benchmarks").glob("*/*/failure_cards/*.yaml"))
    return cards


def load_failure_taxonomy(root: Path) -> set[str]:
    taxonomy_path = root / "contracts" / "failure_taxonomy.yaml"
    if not taxonomy_path.is_file():
        return set()
    document = load_document(taxonomy_path) or {}
    tags = document.get("failure_tags") or {}
    if isinstance(tags, dict):
        return set(tags.keys())
    if isinstance(tags, list):
        return {item if isinstance(item, str) else item.get("tag") for item in tags if item}
    return set()


def _required_section_check(
    path: Path,
    required: tuple[str, ...],
    *,
    severity: str = "warning",
) -> ValidationResult:
    result = ValidationResult()
    if not path.is_file():
        return result
    text = path.read_text(encoding="utf-8")
    headings = {
        line.lstrip("#").strip().lower()
        for line in text.splitlines()
        if line.startswith("## ")
    }
    for section in required:
        if section.lower() not in headings:
            message = f"{path}: missing recommended README section '## {section}'"
            if severity == "error":
                result.errors.append(message)
            else:
                result.warnings.append(message)
    return result


def _root_relative(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _check_benchmark_bundle(root: Path, manifest_path: Path) -> ValidationResult:
    result = ValidationResult()
    bdir = manifest_path.parent
    required = [
        "README.md",
        "benchmark.yaml",
        "metrics.yaml",
        "assets.yaml",
        "expected_failures.yaml",
    ]
    for name in required:
        if not (bdir / name).is_file():
            result.errors.append(f"{bdir}: missing required benchmark file {name}")

    manifest = load_document(manifest_path)
    metrics_config = manifest.get("metrics", {}).get("config")
    if metrics_config and not (bdir / metrics_config).is_file():
        result.errors.append(f"{manifest_path}: metrics.config does not exist: {metrics_config}")

    for asset_name, asset_path in manifest.get("assets", {}).items():
        if asset_path is None:
            continue
        if isinstance(asset_path, str) and asset_path.startswith("$"):
            continue
        if not isinstance(asset_path, str):
            result.errors.append(f"{manifest_path}: assets.{asset_name} must be a path or null")
            continue
        resolved = _root_relative(root, asset_path)
        if not resolved.is_file():
            result.errors.append(f"{manifest_path}: assets.{asset_name} does not exist: {asset_path}")

    taxonomy = load_failure_taxonomy(root)
    if taxonomy:
        for tag in manifest.get("failure_taxonomy", []) or []:
            if tag not in taxonomy:
                result.errors.append(
                    f"{manifest_path}: failure_taxonomy contains unknown tag '{tag}'"
                    f" (allowed: {sorted(taxonomy)})"
                )
        expected_path = bdir / "expected_failures.yaml"
        if expected_path.is_file():
            expected_doc = load_document(expected_path) or {}
            for entry in expected_doc.get("expected_failures", []) or []:
                tag = entry.get("tag") if isinstance(entry, dict) else None
                if tag and tag not in taxonomy:
                    result.errors.append(
                        f"{expected_path}: unknown failure tag '{tag}'"
                        f" (allowed: {sorted(taxonomy)})"
                    )

    result.extend(_required_section_check(bdir / "README.md", BENCHMARK_README_SECTIONS))
    result.extend(_check_baseline_results(bdir))
    return result


def _check_baseline_results(benchmark_dir: Path) -> ValidationResult:
    result = ValidationResult()
    baselines_dir = benchmark_dir / "baselines"
    if not baselines_dir.is_dir():
        return result
    for baseline_result in sorted(baselines_dir.glob("*/result.json")):
        try:
            document = load_document(baseline_result)
        except Exception:
            continue
        execution = (document or {}).get("execution") or {}
        status = execution.get("baseline_status")
        if status is None:
            result.warnings.append(
                f"{baseline_result}: execution.baseline_status missing"
                " (set to 'dry_run', 'real', or 'unknown')"
            )
        elif status == "dry_run":
            result.warnings.append(
                f"{baseline_result}: baseline_status='dry_run' — replace with a real"
                " execution once the runner is connected"
            )
        elif status not in {"real", "unknown"}:
            result.errors.append(
                f"{baseline_result}: execution.baseline_status {status!r} is not"
                " one of dry_run / real / unknown"
            )
    return result


def _check_experiment_bundle(root: Path, manifest_path: Path) -> ValidationResult:
    result = ValidationResult()
    edir = manifest_path.parent
    if not (edir / "README.md").is_file():
        result.errors.append(f"{edir}: missing required experiment file README.md")

    manifest = load_document(manifest_path)
    launch = manifest.get("launch", {})
    if "reason_not_needed" not in launch:
        launch_file = launch.get("file")
        if not launch_file:
            result.errors.append(f"{manifest_path}: launch.file or launch.reason_not_needed is required")
        elif not (edir / launch_file).is_file():
            result.errors.append(f"{manifest_path}: launch.file does not exist: {launch_file}")
    for params_path in launch.get("params", []) or []:
        if not (edir / params_path).is_file():
            result.errors.append(f"{manifest_path}: launch.params entry does not exist: {params_path}")

    for group_name, benchmarks in manifest.get("benchmarks", {}).items():
        if not isinstance(benchmarks, list):
            continue
        for benchmark in benchmarks:
            if not isinstance(benchmark, str):
                result.errors.append(f"{manifest_path}: benchmarks.{group_name} contains a non-string entry")
                continue
            benchmark_dir = _root_relative(root, benchmark)
            benchmark_manifest_path = benchmark_dir / "benchmark.yaml"
            if not benchmark_manifest_path.is_file():
                result.errors.append(f"{manifest_path}: benchmarks.{group_name} target does not exist: {benchmark}")
                continue
            try:
                benchmark_doc = load_document(benchmark_manifest_path)
            except Exception as exc:
                result.errors.append(f"{benchmark_manifest_path}: could not parse: {exc}")
                continue
            if benchmark_doc.get("task") != manifest.get("task"):
                result.errors.append(
                    f"{manifest_path}: benchmarks.{group_name} target {benchmark!r}"
                    f" has task {benchmark_doc.get('task')!r} but experiment task is"
                    f" {manifest.get('task')!r}"
                )

    result.extend(_required_section_check(edir / "README.md", EXPERIMENT_README_SECTIONS))
    return result


def validate_repository(root: Path) -> ValidationResult:
    result = ValidationResult()
    for schema_path in sorted((root / "schemas").glob("*.json")):
        try:
            json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception as exc:
            result.errors.append(f"{schema_path}: could not parse schema: {exc}")

    manifest_paths = (
        iter_asset_manifests(root)
        + iter_benchmark_manifests(root)
        + iter_benchmark_asset_manifests(root)
        + iter_expected_failures(root)
        + iter_failure_cards(root)
        + iter_metric_configs(root)
        + iter_run_records(root)
        + iter_experiment_manifests(root)
    )
    for path in manifest_paths:
        result.extend(validate_manifest(root, path))

    for path in iter_benchmark_manifests(root):
        result.extend(_check_benchmark_bundle(root, path))
    for path in iter_experiment_manifests(root):
        result.extend(_check_experiment_bundle(root, path))
    return result


def validate_path(path: Path) -> ValidationResult:
    root = find_repo_root(path)
    path = path.resolve()
    if path.is_file():
        return validate_manifest(root, path)
    if (path / "benchmark.yaml").is_file():
        result = validate_manifest(root, path / "benchmark.yaml")
        for optional in ("metrics.yaml", "assets.yaml", "expected_failures.yaml"):
            if (path / optional).is_file():
                result.extend(validate_manifest(root, path / optional))
        result.extend(_check_benchmark_bundle(root, path / "benchmark.yaml"))
        return result
    if (path / "experiment.yaml").is_file():
        result = validate_manifest(root, path / "experiment.yaml")
        result.extend(_check_experiment_bundle(root, path / "experiment.yaml"))
        return result
    return validate_repository(root)
