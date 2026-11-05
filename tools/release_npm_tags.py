"""Synchronizes npm dist-tags for tamil-toolkit so that 'latest' reflects the active release."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "tamil-toolkit"

sys.path.insert(0, str(ROOT / "tools"))
from release_policy import load


def get_current_dist_tags() -> dict:
    """Queries npm registry for existing dist-tags of the package."""
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("Missing npm executable in PATH.")
    cmd = [npm, "view", PACKAGE, "dist-tags", "--json"]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return json.loads(out)
    except Exception:
        # Fallback using urllib
        import urllib.request
        req = urllib.request.Request(f"https://registry.npmjs.org/-/package/{PACKAGE}/dist-tags")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))


def sync_dist_tags(target_version: str = None, tag: str = "latest", dry_run: bool = False):
    """Assigns the specified dist-tag (default 'latest') to the target version."""
    if not target_version:
        policy = load(ROOT)
        target_version = policy["version"]

    current_tags = get_current_dist_tags()
    print(f"Current npm dist-tags for {PACKAGE}: {json.dumps(current_tags)}", flush=True)

    if current_tags.get(tag) == target_version:
        print(f"Dist-tag '{tag}' is already set to {target_version}; nothing to do.", flush=True)
        return

    if dry_run:
        print(f"[dry-run] Would execute: npm dist-tag add {PACKAGE}@{target_version} {tag}", flush=True)
        return

    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("Missing npm executable in PATH.")

    print(f"Updating npm dist-tag: {PACKAGE}@{target_version} -> '{tag}'...", flush=True)
    cmd = [npm, "dist-tag", "add", f"{PACKAGE}@{target_version}", tag]
    try:
        subprocess.run(cmd, check=True, text=True)
        print(f"Successfully set dist-tag '{tag}' to {target_version} on npm!", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to update npm dist-tag locally (authentication required).", file=sys.stderr)
        print(f"Run manually: npm dist-tag add {PACKAGE}@{target_version} {tag}", file=sys.stderr)
        raise e


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?", help="Target version to tag (defaults to current Cargo.toml version)")
    parser.add_argument("--tag", default="latest", help="Dist-tag to assign (default: 'latest')")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing")
    parser.add_argument("--view", action="store_true", help="View current dist-tags only")
    args = parser.parse_args()

    if args.view:
        tags = get_current_dist_tags()
        print(json.dumps(tags, indent=2))
        return

    sync_dist_tags(args.version, tag=args.tag, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
