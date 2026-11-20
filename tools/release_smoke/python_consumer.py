"""Run with an isolated interpreter against an installed distribution."""
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

import tamil_toolkit as tamil

package = Path(tamil.__file__).parent
assert version("tamil-toolkit") == sys.argv[2]
assert (package / "py.typed").is_file()
assert (package / "__init__.pyi").is_file()
count = 0

def vector_request(case):
    if case.get("op") not in {"lexicon_lookup", "lexicon_packs"}:
        return case
    metadata = {"id", "expected", "expected_error", "dialect", "tags", "source", "unicode_exceptions"}
    return {key: value for key, value in case.items() if key not in metadata}

for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    case = json.loads(line)
    try:
        result = tamil.execute(vector_request(case))
    except ValueError as error:
        assert "expected_error" in case, (case["id"], str(error))
        assert str(error) == case["expected_error"], case["id"]
    else:
        assert "expected" in case and result == case["expected"], case["id"]
    count += 1
assert count > 0
assert tamil.format_fraction(2, 4) == "1/2"
assert tamil.format_currency(102550, "LKR", "SL") == "LKR 1,025.50"

def _assert_lexicon_contracts(nanri, absent, unavailable_pack):
    assert tamil.lexicon_lookup(nanri)["status"] == "matched"
    missing = tamil.lexicon_lookup(absent)
    assert missing["status"] == "not_found" and missing["entries"] == []
    for args, kwargs, expected_msg in (
        ((nanri,), {"packs": [unavailable_pack]}, f"lexicon: pack unavailable '{unavailable_pack}'"),
        ((nanri,), {"packs": []}, "lexicon: packs must be a nonempty string array"),
        ((nanri,), {"packs": ["unknown"]}, "lexicon: unknown pack 'unknown'"),
        ((nanri,), {"region": "LK-JAFFNA"}, "lexicon: unknown region 'LK-JAFFNA'"),
        (("\u0b85\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc8",), {"register": "written"}, "lexicon: unknown register 'written'"),
    ):
        try:
            tamil.lexicon_lookup(*args, **kwargs)
        except ValueError as error:
            assert str(error) == expected_msg, str(error)
        else:
            raise AssertionError(f"Expected ValueError({expected_msg!r})")


profile = os.environ.get("TAMIL_LEXICON_PROFILE", "default")
packs = tamil.lexicon_packs()
nanri = "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf"
absent = "\u0b87\u0bb2\u0bcd\u0bb2\u0bbe\u0ba4\u0b9a\u0bca\u0bb2\u0bcd"
if profile == "default":
    assert packs == [], f"default profile must expose 0 lexicon packs, got {packs!r}"
    try:
        tamil.lexicon_lookup(nanri)
    except ValueError as error:
        assert str(error) == "lexicon: pack unavailable 'core'", str(error)
    else:
        raise AssertionError("default profile must reject core lookup")
elif profile == "core":
    assert len(packs) == 1 and packs[0]["id"] == "core", packs
    assert packs[0]["available"] is True and packs[0]["schema_version"] == 1
    expected_sha = os.environ.get("TAMIL_LEXICON_MANIFEST_SHA256")
    if expected_sha:
        assert packs[0]["manifest_sha256"] == expected_sha
    expected_ver = os.environ.get("TAMIL_LEXICON_DATASET_VERSION")
    if expected_ver:
        assert packs[0]["dataset_version"] == expected_ver
    _assert_lexicon_contracts(nanri, absent, "regional")
elif profile == "full":
    assert [pack["id"] for pack in packs] == ["core", "names_taxa", "regional"], packs
    raw_manifests = os.environ.get("TAMIL_LEXICON_PACK_MANIFESTS")
    env_manifests = json.loads(raw_manifests) if raw_manifests else None
    for pack in packs:
        assert pack["available"] is True and pack["schema_version"] == 1
        if env_manifests is not None:
            expected = env_manifests[pack["id"]]
            assert pack["manifest_sha256"] == expected["manifest_sha256"]
            assert pack["dataset_version"] == expected["dataset_version"]
    expected_sha = os.environ.get("TAMIL_LEXICON_MANIFEST_SHA256")
    if expected_sha:
        assert packs[0]["manifest_sha256"] == expected_sha
    expected_ver = os.environ.get("TAMIL_LEXICON_DATASET_VERSION")
    if expected_ver:
        assert packs[0]["dataset_version"] == expected_ver
    _assert_lexicon_contracts(nanri, absent, "terminology")
else:
    raise AssertionError(f"Unsupported TAMIL_LEXICON_PROFILE={profile!r}")

print(f"Installed native Python distribution ({profile}): {count} golden rows passed.")
