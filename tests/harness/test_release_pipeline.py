"""Tests for autonomous release pipeline and npm dist-tag utilities."""

import pytest
import subprocess
from tools.harness import ROOT
from tools.release_pipeline import (
    check_git_branch,
    check_git_clean,
    check_gh_authenticated,
)
from tools.release_policy import parse_version
from tools.release_npm_tags import get_current_dist_tags


def test_parse_version_valid_and_invalid():
    # Valid alpha version
    parsed = parse_version("0.1.0-alpha.6")
    assert parsed["version"] == "0.1.0-alpha.6"
    assert parsed["base"] == "0.1.0"
    assert parsed["stage"] == "alpha"
    assert parsed["number"] == "6"
    assert parsed["python_version"] == "0.1.0a6"
    assert parsed["npm_tag"] == "alpha"
    assert parsed["record_name"] == "alpha-6"

    # Valid stable version
    stable = parse_version("1.0.0")
    assert stable["channel"] == "stable"
    assert stable["python_version"] == "1.0.0"
    assert stable["npm_tag"] == "latest"

    # Invalid version
    with pytest.raises(ValueError, match="Unsupported release version"):
        parse_version("invalid-version")


def test_check_git_branch_validation(monkeypatch):
    monkeypatch.setattr(
        "tools.release_pipeline.run_command",
        lambda *args, **kwargs: "feature-branch\n",
    )
    with pytest.raises(RuntimeError, match="not release branch 'master'"):
        check_git_branch("master")


def test_check_git_clean_rejection(monkeypatch):
    monkeypatch.setattr(
        "tools.release_pipeline.run_command",
        lambda *args, **kwargs: " M some_file.py\n?? untracked.txt\n",
    )
    with pytest.raises(RuntimeError, match="Git working tree is dirty"):
        check_git_clean()


def test_get_current_dist_tags():
    tags = get_current_dist_tags()
    assert isinstance(tags, dict)
    assert "alpha" in tags
    assert "latest" in tags
