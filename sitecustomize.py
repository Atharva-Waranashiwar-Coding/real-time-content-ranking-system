"""Local source-tree package aliases for running services from the repository root."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def _load_local_package(module_name: str, relative_directory: str) -> None:
    """Load a local package under a stable import alias if it is not installed."""

    if module_name in sys.modules:
        return

    package_root = PROJECT_ROOT / relative_directory
    module_path = package_root / "__init__.py"
    if not module_path.exists():
        return

    spec = importlib.util.spec_from_file_location(
        module_name,
        module_path,
        submodule_search_locations=[str(package_root)],
    )
    if spec is None or spec.loader is None:
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


_load_local_package("shared_schemas", "packages/shared-schemas")
_load_local_package("shared_config", "packages/shared-config")
_load_local_package("shared_logging", "packages/shared-logging")
_load_local_package("shared_clients", "packages/shared-clients")
