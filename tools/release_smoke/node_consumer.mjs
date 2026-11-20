import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as node from "tamil-toolkit";
import * as web from "tamil-toolkit/web";

await web.init({ module_or_path: readFileSync(new URL("../pkg-web/tamil_toolkit_bg.wasm", import.meta.resolve("tamil-toolkit/web"))) });
const cases = readFileSync(process.argv[2], "utf8").trim().split(/\r?\n/).map(JSON.parse);
assert.ok(cases.length);
const profile = process.env.TAMIL_LEXICON_PROFILE ?? "default";
const expectedSha = process.env.TAMIL_LEXICON_MANIFEST_SHA256;
const expectedVer = process.env.TAMIL_LEXICON_DATASET_VERSION;
const rawPackManifests = process.env.TAMIL_LEXICON_PACK_MANIFESTS;
const packManifests = rawPackManifests ? JSON.parse(rawPackManifests) : undefined;
const nanri = "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf";
const absent = "\u0b87\u0bb2\u0bcd\u0bb2\u0bbe\u0ba4\u0b9a\u0bca\u0bb2\u0bcd";

function assertLexiconContracts(api, unavailablePack) {
  assert.equal(api.lexicon_lookup(nanri).status, "matched");
  const missing = api.lexicon_lookup(absent);
  assert.equal(missing.status, "not_found");
  assert.deepEqual(missing.entries, []);
  assert.throws(() => api.lexicon_lookup(nanri, { packs: [unavailablePack] }), (e) => e.message === `lexicon: pack unavailable '${unavailablePack}'`);
  assert.throws(() => api.lexicon_lookup(nanri, { packs: [] }), (e) => e.message === "lexicon: packs must be a nonempty string array");
  assert.throws(() => api.lexicon_lookup(nanri, { packs: ["unknown"] }), (e) => e.message === "lexicon: unknown pack 'unknown'");
  assert.throws(() => api.lexicon_lookup(nanri, { region: "LK-JAFFNA" }), (e) => e.message === "lexicon: unknown region 'LK-JAFFNA'");
  assert.throws(() => api.lexicon_lookup("\u0b85\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc8", { register: "written" }), (e) => e.message === "lexicon: unknown register 'written'");
}

for (const [name, api] of [["Node", node], ["browser-target", web]]) {
  for (const row of cases) {
    if (Object.hasOwn(row, "expected_error")) {
      assert.throws(() => api.execute(vectorRequest(row)), (error) => error.message === row.expected_error, row.id);
    } else {
      assert.deepEqual(api.execute(vectorRequest(row)), row.expected, row.id);
    }
  }
  assert.equal(api.format_fraction(2, 4), "1/2");
  const packs = api.lexicon_packs();
  if (profile === "default") {
    assert.deepEqual(packs, []);
    assert.throws(
      () => api.lexicon_lookup(nanri),
      (error) => error.message === "lexicon: pack unavailable 'core'",
    );
  } else if (profile === "core") {
    assert.equal(packs.length, 1);
    assert.equal(packs[0].id, "core");
    assert.equal(packs[0].available, true);
    assert.equal(packs[0].schema_version, 1);
    if (expectedSha) assert.equal(packs[0].manifest_sha256, expectedSha);
    if (expectedVer) assert.equal(packs[0].dataset_version, expectedVer);
    assertLexiconContracts(api, "regional");
  } else if (profile === "full") {
    assert.deepEqual(packs.map((pack) => pack.id), ["core", "names_taxa", "regional"]);
    for (const pack of packs) {
      assert.equal(pack.available, true);
      assert.equal(pack.schema_version, 1);
      if (packManifests) {
        assert.equal(pack.manifest_sha256, packManifests[pack.id]?.manifest_sha256);
        assert.equal(pack.dataset_version, packManifests[pack.id]?.dataset_version);
      }
    }
    if (expectedSha) assert.equal(packs[0].manifest_sha256, expectedSha);
    if (expectedVer) assert.equal(packs[0].dataset_version, expectedVer);
    assertLexiconContracts(api, "terminology");
  } else {
    throw new Error(`Unsupported TAMIL_LEXICON_PROFILE=${profile}`);
  }
  console.log(`Installed ${name} WASM distribution (${profile}): ${cases.length} golden rows passed.`);
}

function vectorRequest(row) {
  if (!["lexicon_lookup", "lexicon_packs"].includes(row.op)) return row;
  const request = { ...row };
  for (const key of ["id", "expected", "expected_error", "dialect", "tags", "source", "unicode_exceptions"]) delete request[key];
  return request;
}
