import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as node from "tamil-toolkit";
import * as web from "tamil-toolkit/web";

await web.init({ module_or_path: readFileSync(new URL("../pkg-web/tamil_toolkit_bg.wasm", import.meta.resolve("tamil-toolkit/web"))) });
const cases = readFileSync(process.argv[2], "utf8").trim().split(/\r?\n/).map(JSON.parse);
assert.ok(cases.length);
for (const [name, api] of [["Node", node], ["browser-target", web]]) {
  for (const row of cases) {
    if (Object.hasOwn(row, "expected_error")) {
      assert.throws(() => api.execute(row), (error) => error.message === row.expected_error, row.id);
    } else {
      assert.deepEqual(api.execute(row), row.expected, row.id);
    }
  }
  assert.equal(api.format_fraction(2, 4), "1/2");
  console.log(`Installed ${name} WASM distribution: ${cases.length} golden rows passed.`);
}
