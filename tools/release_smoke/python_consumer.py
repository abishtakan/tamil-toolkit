"""Run with an isolated interpreter against an installed distribution."""
import json
import sys
from importlib.metadata import version
from pathlib import Path

import tamil_toolkit as tamil

package = Path(tamil.__file__).parent
assert version("tamil-toolkit") == sys.argv[2]
assert (package / "py.typed").is_file()
assert (package / "__init__.pyi").is_file()
count = 0
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    case = json.loads(line)
    try:
        result = tamil.execute(case)
    except ValueError as error:
        assert "expected_error" in case, (case["id"], str(error))
        assert str(error) == case["expected_error"], case["id"]
    else:
        assert "expected" in case and result == case["expected"], case["id"]
    count += 1
assert count > 0
assert tamil.format_fraction(2, 4) == "1/2"
assert tamil.format_currency(102550, "LKR", "SL") == "LKR 1,025.50"
print(f"Installed native Python distribution: {count} golden rows passed.")
