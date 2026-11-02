"""Check that every manifest operation has a manual workbench form."""

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTENTIONAL_UNKNOWN = {"unknown_core_operation"}


def main() -> None:
    manifest = json.loads((ROOT / "tests/golden/manifest.json").read_text(encoding="utf-8"))
    declared = {
        operation
        for suite in manifest["suites"]
        for operation in suite.get("operations", [])
    }
    source = (ROOT / "workbench/main.ts").read_text(encoding="utf-8")
    operations = re.findall(r'\bop:\s*"([a-z_]+)"\s*,\s*label:', source)
    duplicates = sorted(name for name, count in Counter(operations).items() if count > 1)
    manual = set(operations)
    missing = sorted(declared - manual - INTENTIONAL_UNKNOWN)
    extra = sorted(manual - declared)
    if duplicates or missing or extra:
        raise SystemExit(
            "workbench operation coverage mismatch: "
            f"duplicates={duplicates}, missing={missing}, unregistered={extra}"
        )
    print(f"Workbench operation coverage verified ({len(manual)} forms; intentional fixture excluded).")


if __name__ == "__main__":
    main()
