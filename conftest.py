"""Keep pytest's numbered, automatically retained temp runs in the workspace."""

import os
from pathlib import Path


def pytest_configure(config):
    if config.option.basetemp is None and "PYTEST_DEBUG_TEMPROOT" not in os.environ:
        directory = Path(__file__).resolve().parent / "target/pytest-temp"
        directory.mkdir(parents=True, exist_ok=True)
        os.environ["PYTEST_DEBUG_TEMPROOT"] = str(directory)
