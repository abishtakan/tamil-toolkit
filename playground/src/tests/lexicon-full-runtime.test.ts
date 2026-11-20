import { beforeAll, describe, expect, it } from 'vitest';
import * as toolkit from 'tamil-toolkit/web';
import { ensureToolkitInitialized } from './setup';
import catalog from '../generated/lexicon-catalog.json';

describe('real full-profile lexicon browser WASM', () => {
  beforeAll(ensureToolkitInitialized);
  it('loads all canonical packs with matching provenance manifests', () => {
    const packs = toolkit.lexicon_packs();
    expect(packs.map(p => p.id)).toEqual(['core', 'names_taxa', 'regional']);
    for (const expected of catalog.packs) {
      expect(packs.find(p => p.id === expected.id)).toMatchObject({
        manifest_sha256: expected.manifest_sha256, dataset_version: expected.dataset_version,
      });
    }
  });
  it('returns both reviewed homographs and every sense', () => {
    const result = toolkit.lexicon_lookup('\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf', { packs: ['core'] });
    expect(result.status).toBe('matched');
    expect(result.entries).toHaveLength(2);
    expect(result.entries.reduce((n, e) => n + e.senses.length, 0)).toBe(3);
    expect(result.entries.map(e => e.part_of_speech.value).sort()).toEqual(['INTJ', 'NOUN']);
    expect(result.entries.every(e => e.provenance.length > 0)).toBe(true);
  });
  it.each([
    ['names_taxa', '\u0b95\u0bb0\u0bc1\u0ba8\u0bbe\u0b9f\u0b95\u0bae\u0bcd'],
    ['regional', '\u0ba8\u0bc6\u0bb0\u0bc1\u0b99\u0bcd\u0b95\u0bc1'],
  ])('queries the real %s pack', (pack, word) => {
    expect(toolkit.lexicon_lookup(word, { packs: [pack] }).status).toBe('matched');
  });
  it('preserves spaces and invisible scalars, and only normalizes NFC', () => {
    const input = ' ' + String.fromCodePoint(0x0b95, 0x0bc6, 0x0bbe, 0x200d) + ' ';
    const result = toolkit.lexicon_lookup(input);
    expect(result.canonical_query).toBe(' ' + String.fromCodePoint(0x0b95, 0x0bca, 0x200d) + ' ');
  });
  it('validates finite filters and pack errors without swallowing engine messages', () => {
    expect(() => toolkit.lexicon_lookup('', { packs: [] })).toThrow('lexicon: packs must be a nonempty string array');
    expect(() => toolkit.lexicon_lookup('', { packs: ['terminology'] })).toThrow("lexicon: pack unavailable 'terminology'");
    expect(() => toolkit.lexicon_lookup('', { packs: ['bogus'] })).toThrow("lexicon: unknown pack 'bogus'");
    expect(() => toolkit.lexicon_lookup('', { region: 'bogus' })).toThrow("lexicon: unknown region 'bogus'");
    expect(() => toolkit.lexicon_lookup('', { register: 'bogus' })).toThrow("lexicon: unknown register 'bogus'");
    expect(toolkit.lexicon_lookup('', { region: 'JAFFNA', register: 'formal' }).status).toBe('not_found');
  });
  it('honors the 65536-byte boundary without truncation', () => {
    expect(toolkit.lexicon_lookup('a'.repeat(65536)).canonical_query).toHaveLength(65536);
    expect(() => toolkit.lexicon_lookup('a'.repeat(65537))).toThrow('lexicon: input exceeds 65536 UTF-8 bytes');
  });
});
