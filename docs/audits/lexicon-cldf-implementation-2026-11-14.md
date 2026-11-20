# Feature 021 T042/T043 CLDF 1.3 Offline Interchange Notes

- **Scope**: Bounded offline CLDF 1.3 `Dictionary` interchange (`T042`, `T043`).
- **Pinned dev validator dependencies** (`pyproject.toml` `[dependency-groups].dev` & `uv.lock`):
  - `pycldf==2.2.0`
  - `csvw==4.2.0`
- **Pinned CLDF 1.3 local schemas & ontology** (`schemas/lexicon/cldf/cldf-1.3.sha256.json`):
  - Source tag: `https://github.com/cldf/cldf/tree/v1.3`
  - Ontology: `schemas/lexicon/cldf/v1.3/terms.rdf` (`sha256:763b9f2587af9cdbb452c997cbc10328a316eeecdcc235f1a615e2bd2466385e`)
  - Schemas: `modules/Dictionary-metadata.json`, `components/{EntryTable,SenseTable,ExampleTable,LanguageTable,FormTable}-metadata.json`
  - Report JSON Schema: `schemas/lexicon/cldf/cldf-export-report.schema.json`
- **Module API** (`tools/lexicon_cldf.py`):
  - `verify_cldf_schemas(schema_dir=None) -> dict`
  - `load_trusted_canonical(canonical, pack, *, canonical_validator=None) -> dict`
  - `verify_cldf_export(cldf_dir, trusted_canonical, *, schema_dir=None) -> dict`
  - `export_cldf(canonical, pack, output, *, check=True, report_output=None, canonical_validator=None) -> dict`
  - `main(argv=None) -> int`
- **Root CLI hook snippet for `tools/lexicon.py`**:
  ```python
  p_cldf = sub.add_parser("export-cldf", help="Export promoted canonical pack to offline CLDF 1.3")
  p_cldf.add_argument("--canonical", required=True)
  p_cldf.add_argument("--pack", required=True, choices=lexicon_cldf.SUPPORTED_PACKS)
  p_cldf.add_argument("--output", required=True)
  p_cldf.add_argument("--check", action="store_true")
  p_cldf.add_argument("--report-output")
  ```
  Dispatch handler returns `lexicon_cldf.main(raw_argv)` directly (exit `0` pass, `1` eligibility/validation failure, `2` usage/IO/hash/conflict error).
