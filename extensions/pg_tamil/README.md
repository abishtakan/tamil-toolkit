# pg_tamil (PostgreSQL Lexicon Extension)

`pg_tamil` exposes thin `pgrx` SQL functions backed by `tamil_lexicon::PackRegistry`
inside each PostgreSQL backend (`OnceLock<RwLock<PackRegistry>>`) with lazy
auto-discovery via `tamil_lexicon::auto_discover_pack_dir()`.

It is excluded from the portable Cargo workspace so building the core
Rust/Python/WASM/Dart SDKs does not require a PostgreSQL toolchain.

## Prerequisites & Setup

1. **Install `pgrx` (matching `0.19.3`) on Linux/macOS** with PostgreSQL 17 or 18:

   ```bash
   cargo install --locked cargo-pgrx --version 0.19.3
   cargo pgrx init
   ```

2. **Download `.tlpack` v2 packs** using the `tamil-toolkit` CLI (or copy `.tlpack`
   files into a directory and export `TAMIL_LEXICON_DIR`):

   ```bash
   # Lightweight verified open bundle (~2.9 MB)
   tamil-toolkit lexicon pull --profile open-lite

   # Or full verified open bundle (~15.3 MB, 90k+ words)
   tamil-toolkit lexicon pull --profile open

   # Optional: point PostgreSQL's environment to a custom pack directory
   export TAMIL_LEXICON_DIR="$HOME/.tamil-toolkit/lexicon-packs"
   ```

   `auto_discover_pack_dir()` checks `TAMIL_LEXICON_DIR`, `./dist/lexicon-packs`,
   `./lexicon-packs` (up to 3 parent directories), and `~/.tamil-toolkit/lexicon-packs`.

3. **Build and run / install from `extensions/pg_tamil/`**:

   ```bash
   cd extensions/pg_tamil
   cargo pgrx run pg18
   # Or install into the configured Postgres instance:
   # cargo pgrx install --release
   ```

   Inside PostgreSQL:

   ```sql
   CREATE EXTENSION pg_tamil;
   ```

## Exported SQL Functions

- `tamil_lexicon_init(dir TEXT DEFAULT NULL, profile TEXT DEFAULT NULL) -> TEXT`
  Initializes or reloads the backend-local pack registry (`profile`: `'open-lite'`,
  `'open'`, `'local'`, or `'full'`). Returns a JSON summary.
- `tamil_lexicon_stats() -> TEXT`
  Returns JSON `LexiconStoreStats` across all mounted packs.
- `tamil_define(word TEXT, folded BOOLEAN DEFAULT FALSE) -> TEXT`
  Returns unified JSON `WordDefinition` (meanings, POS, domains, regions, IPA,
  pure-Tamil equivalents, relations, and source provenance).
- `tamil_lexicon_search(prefix TEXT, limit INT DEFAULT 25, folded BOOLEAN DEFAULT FALSE) -> TEXT`
  Runs FST prefix search and returns JSON `LexiconPrefixSearchResult`.
- `tamil_lexicon_search_english(query TEXT, limit INT DEFAULT 25) -> TEXT`
  Runs reverse English-to-Tamil gloss/definition search and returns JSON `LexiconPrefixSearchResult`.

## SQL Query Examples

```sql
-- 1. Optional explicit initialization (otherwise auto-discovers lazily on first query)
SELECT tamil_lexicon_init(NULL, 'open')::jsonb;

-- 2. Inspect mounted packs and entry counts
SELECT (tamil_lexicon_stats()::jsonb) - 'packs';

-- 3. Define a Tamil word (exact NFC) and extract English meanings + pure-Tamil equivalents
SELECT
  def->>'headword' AS headword,
  def->'pos' AS pos,
  def->'pure_tamil_equivalents' AS pure_tamil,
  jsonb_path_query_array(def, '$.meanings_en[*].text') AS english_meanings
FROM (SELECT tamil_define('தமிழ்', false)::jsonb AS def) q;

-- 4. Mayangoli-folded definition lookup (e.g. மலை vs மழை)
SELECT tamil_define('மலை', true)::jsonb->'matched_headwords';

-- 5. FST Tamil prefix autocomplete
SELECT hit->>'headword' AS word, hit->>'preview_gloss' AS gloss
FROM jsonb_array_elements(
  tamil_lexicon_search('அறி', 10, true)::jsonb->'hits'
) AS hit;

-- 6. Reverse English-to-Tamil gloss search
SELECT hit->>'headword' AS tamil_word, hit->>'preview_gloss' AS english_gloss
FROM jsonb_array_elements(
  tamil_lexicon_search_english('water', 10)::jsonb->'hits'
) AS hit;
```
