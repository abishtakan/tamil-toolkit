// Development-only evidence: extract pinned upstream data and run its encoder.
// No public binding or production tool imports this file.
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const directory = process.argv[2];
const primary = fs.readFileSync(path.join(directory, "ag-main.js"), "utf8");
const boundary = primary.indexOf("function convertFontUnicode");
if (boundary < 0) throw new Error("Unexpected primary source layout");
const dataScope = Object.create(null);
vm.runInNewContext(primary.slice(0, boundary) + "\nresult = fontRespectiveUnicode.bamini;",
  dataScope, { timeout: 1000 });
fs.writeFileSync(process.argv[3], JSON.stringify(dataScope.result));

const encoderScope = { module: { exports: {} } };
vm.runInNewContext(fs.readFileSync(path.join(directory, "pakeetharan-convert.js"), "utf8"),
  encoderScope, { timeout: 1000 });
const samples = JSON.parse(fs.readFileSync(process.argv[4], "utf8"));
const results = samples.map((sample) => ({ ...sample, encoded: encoderScope.module.exports(sample.text) }));
fs.writeFileSync(process.argv[5], JSON.stringify(results));
