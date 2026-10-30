"""Repository Unicode gate: inspect raw source and decoded literal escapes."""

import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.harness import JOINERS, ROOT, load_vectors  # noqa: E402

SKIP = {".git", ".venv", "target", "node_modules", "__pycache__", ".dart_tool", ".pytest_cache", "pkg-node", "pkg-web", "dist", "build"}
EXTENSIONS = {".rs", ".jsonl", ".py", ".ts", ".dart", ".toml"}
ESCAPES = re.compile(r"(?:\\u\{[0-9a-fA-F]{1,6}\}|\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}|[^\\])+")
HEX = re.compile(r"\\(?:u\{([0-9a-fA-F]{1,6})\}|u([0-9a-fA-F]{4})|U([0-9a-fA-F]{8}))")


def inspect_source(path):
    failures = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not unicodedata.is_normalized("NFC", line) or JOINERS.intersection(line):
            failures.append(f"{path}:{number}: raw non-NFC text or invisible joiner")
        # JSONL has pointer-scoped exceptions checked on decoded values by the schema gate.
        if path.suffix == ".jsonl":
            continue
        for match in ESCAPES.finditer(line):
            decoded = HEX.sub(lambda m: chr(int(next(g for g in m.groups() if g), 16)), match.group())
            if JOINERS.intersection(decoded):
                failures.append(f"{path}:{number}: escaped invisible joiner; place intentional cases in golden JSONL")
            tamil = any("\u0b80" <= char <= "\u0bff" for char in decoded)
            if tamil and not unicodedata.is_normalized("NFC", decoded):
                failures.append(f"{path}:{number}: escaped non-NFC Tamil; place intentional cases in golden JSONL")
    return failures


def main():
    try:
        active = load_vectors()
    except (ValueError, KeyError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    failures = []
    # Prune generated/dependency trees before recursion.
    import os
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = [name for name in dirs if name not in SKIP]
        for name in files:
            path = Path(directory) / name
            if path.suffix in EXTENSIONS:
                failures.extend(inspect_source(path))
            if path.is_relative_to(ROOT / "lexicon") and path.suffix not in {".toml", ".csv", ".md"}:
                failures.append(f"{path}: executable or unsupported file in lexicon")
    for failure in failures:
        print(failure, file=sys.stderr)
    if not failures:
        print(f"Unicode/schema gate passed; {len(active)} active vectors; planned suites validated separately.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
