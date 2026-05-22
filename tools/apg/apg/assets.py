from __future__ import annotations

from pathlib import Path

from .schema import iter_asset_manifests, load_document


def list_assets(root: Path) -> list[dict]:
    return [load_document(path) for path in iter_asset_manifests(root)]
