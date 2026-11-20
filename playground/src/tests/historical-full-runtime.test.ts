import { readFile } from 'node:fs/promises';
import { webcrypto } from 'node:crypto';
import { beforeAll, describe, expect, it } from 'vitest';
import * as toolkit from 'tamil-toolkit/web';
import { ensureToolkitInitialized } from './setup';
import { createSourceRecordsClient } from '../lib/source-records';
import samples from '../../../tests/reference/lexicon/historical/source_samples.json';

describe('real historical data through browser WASM', () => {
  beforeAll(ensureToolkitInitialized);
  const fetchAssets: typeof fetch = async (input) => {
    const pathname = String(input).replace(/^.*historical-lexicon\//, '');
    if (!/^(manifest|[0-9a-f]{2})\.json$/.test(pathname)) throw new Error('Unsafe test asset path');
    const bytes = await readFile(new URL(`../../public/historical-lexicon/${pathname}`, import.meta.url));
    return new Response(bytes, { headers: { 'content-type': 'application/json' } });
  };
  const client = createSourceRecordsClient({
    execute: toolkit.execute,
    fetchImpl: fetchAssets,
    subtle: webcrypto.subtle as SubtleCrypto,
  });

  it.each(samples)('retrieves original cells from $source_file', async (sample) => {
    const result = await client.search({ query: sample.query, offset: 0, limit: 100 });
    expect(result.manifest.total_records).toBe(307243);
    expect(result.response.data_status).toBe('owner_supplied_unverified');
    expect(result.response.rights_status).toBe('unresolved');
    expect(result.response.records.find(row => row.source_file === sample.source_file
      && row.source_row === sample.source_row)?.fields).toEqual(sample.fields);
  });
});
