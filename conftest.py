"""Keep pytest's numbered, automatically retained temp runs in the workspace and configure xdist safely."""

import os
from pathlib import Path


def pytest_configure(config):
    if config.option.basetemp is None and "PYTEST_DEBUG_TEMPROOT" not in os.environ:
        directory = Path(__file__).resolve().parent / "target/pytest-temp"
        directory.mkdir(parents=True, exist_ok=True)
        os.environ["PYTEST_DEBUG_TEMPROOT"] = str(directory)

    # Register xdist_group so tests remain warning-free both with and without pytest-xdist.
    config.addinivalue_line(
        "markers",
        "xdist_group(name): assign tests to a shared pytest-xdist scheduling group.",
    )

    # Default parallel runs (-n ...) to --dist=loadgroup unless explicitly overridden so
    # @pytest.mark.xdist_group(...) keeps read-only full-pack fixtures on one worker.
    if getattr(config.option, "numprocesses", None) and hasattr(config.option, "dist"):
        raw_args = getattr(getattr(config, "invocation_params", None), "args", ())
        has_explicit_dist = any(
            arg == "--dist" or arg.startswith("--dist=") for arg in raw_args
        )
        if not has_explicit_dist and config.option.dist == "load":
            config.option.dist = "loadgroup"
