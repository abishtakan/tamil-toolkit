"""Prepare the playground's full browser WASM profile, pack catalog, and browse index."""
from __future__ import annotations
import argparse
import csv
import filecmp
import json
import os
from pathlib import Path
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PACKS = [('core', ROOT/'lexicon/dictionary'), ('names_taxa', ROOT/'lexicon/packs/names_taxa'), ('regional', ROOT/'lexicon/packs/regional')]

TAMIL_LETTER_ORDER = [
    '\u0b85', '\u0b86', '\u0b87', '\u0b88', '\u0b89', '\u0b8a',
    '\u0b8e', '\u0b8f', '\u0b90', '\u0b92', '\u0b93', '\u0b94', '\u0b83',
    '\u0b95', '\u0b99', '\u0b9a', '\u0b9e', '\u0b9f', '\u0ba3',
    '\u0ba4', '\u0ba8', '\u0baa', '\u0bae', '\u0baf', '\u0bb0',
    '\u0bb2', '\u0bb5', '\u0bb4', '\u0bb3', '\u0bb1', '\u0ba9',
    '\u0b9c', '\u0bb6', '\u0bb7', '\u0bb8', '\u0bb9',
]
TAMIL_LETTER_RANK = {ch: idx for idx, ch in enumerate(TAMIL_LETTER_ORDER)}


def initial_letter_bucket(word: str) -> str:
    for ch in word:
        if ch in TAMIL_LETTER_RANK:
            return ch
    return '#'


def _truncate_gloss(text: str, max_len: int = 84) -> str:
    clean = ' '.join(text.split())
    if len(clean) <= max_len:
        return clean
    return clean[: max_len - 1].rstrip(' ,;:') + '\u2026'


def build_artifacts():
    words: set[str] = set()
    packs = []
    by_word: dict[str, dict] = {}
    all_pos: set[str] = set()

    for ident, directory in PACKS:
        meta = tomllib.loads((directory/'packs.toml').read_text(encoding='utf-8'))
        with (directory/'assertions.csv').open(encoding='utf-8', newline='') as handle:
            claims = {r['assertion_id']: r['value_json'] for r in csv.DictReader(handle)}

        form_text: dict[str, str] = {}
        with (directory/'forms.csv').open(encoding='utf-8', newline='') as handle:
            for form in csv.DictReader(handle):
                if form['representation'] == 'written':
                    value = json.loads(claims[form['text_assertion_id']])
                    if isinstance(value, str):
                        words.add(value)
                        form_text[form['form_id']] = value

        entry_info: dict[str, tuple[str, str | None]] = {}
        with (directory/'entries.csv').open(encoding='utf-8', newline='') as handle:
            for row in csv.DictReader(handle):
                hw = form_text.get(row['canonical_form_id'])
                if not hw:
                    continue
                pos_val = None
                pos_aid = row.get('pos_assertion_id') or ''
                if pos_aid and pos_aid in claims:
                    parsed = json.loads(claims[pos_aid])
                    if isinstance(parsed, str) and parsed:
                        pos_val = parsed
                        all_pos.add(parsed)
                entry_info[row['entry_id']] = (hw, pos_val)

        sense_owner: dict[str, tuple[str, int]] = {}
        with (directory/'senses.csv').open(encoding='utf-8', newline='') as handle:
            for row in csv.DictReader(handle):
                order = int(row['display_order']) if row.get('display_order') else 999
                sense_owner[row['sense_id']] = (row['entry_id'], order)

        entry_gloss: dict[str, tuple[int, str]] = {}
        with (directory/'texts.csv').open(encoding='utf-8', newline='') as handle:
            for row in csv.DictReader(handle):
                if row['owner_kind'] != 'sense':
                    continue
                if row['component'] not in ('definition', 'gloss', 'translation'):
                    continue
                owner = sense_owner.get(row['owner_id'])
                if not owner:
                    continue
                eid, order = owner
                aid = row.get('text_assertion_id') or ''
                if aid not in claims:
                    continue
                val = json.loads(claims[aid])
                if not isinstance(val, str) or not val.strip():
                    continue
                prev = entry_gloss.get(eid)
                if prev is None or order < prev[0]:
                    entry_gloss[eid] = (order, val.strip())

        entry_regions: dict[str, set[str]] = {}
        with (directory/'scopes.csv').open(encoding='utf-8', newline='') as handle:
            for row in csv.DictReader(handle):
                if row['dimension'] != 'region' or row['state'] != 'attested':
                    continue
                code = (row.get('label_code') or '').strip()
                if not code:
                    continue
                eid = row['subject_id'] if row['subject_kind'] == 'entry' else (
                    sense_owner[row['subject_id']][0] if row['subject_id'] in sense_owner else None
                )
                if eid:
                    entry_regions.setdefault(eid, set()).add(code)

        for eid, (hw, pos_val) in entry_info.items():
            rec = by_word.setdefault(
                hw,
                {
                    'letter': initial_letter_bucket(hw),
                    'packs': set(),
                    'pos': set(),
                    'regions': set(),
                    'glosses': [],
                },
            )
            rec['packs'].add(ident)
            if pos_val:
                rec['pos'].add(pos_val)
            if eid in entry_regions:
                rec['regions'].update(entry_regions[eid])
            if eid in entry_gloss:
                g = ' '.join(entry_gloss[eid][1].split())
                if g and g not in rec['glosses'] and len(rec['glosses']) < 3:
                    rec['glosses'].append(g)

        packs.append({k:meta[k] for k in ('entry_count','sense_count','manifest_sha256','dataset_version','coverage')} | {'id':ident})

    vocab = tomllib.loads((PACKS[0][1]/'vocabularies.toml').read_text(encoding='utf-8'))
    catalog_data = dict(
        packs=packs,
        regions=vocab['regions'],
        registers=vocab['registers'],
        distinct_headwords=len(words),
        total_entries=sum(p['entry_count'] for p in packs),
        total_senses=sum(p['sense_count'] for p in packs),
    )

    sorted_words = sorted(
        by_word.items(),
        key=lambda kv: (TAMIL_LETTER_RANK.get(kv[1]['letter'], 999), kv[0]),
    )
    letter_counts: dict[str, int] = {}
    items = []
    for hw, rec in sorted_words:
        letter = rec['letter']
        letter_counts[letter] = letter_counts.get(letter, 0) + 1
        items.append([
            hw,
            letter,
            sorted(rec['packs']),
            sorted(rec['pos']),
            sorted(rec['regions']),
            _truncate_gloss('; '.join(rec['glosses']), max_len=96),
        ])

    letters = [
        {'id': ch, 'count': letter_counts[ch]}
        for ch in [*TAMIL_LETTER_ORDER, '#']
        if ch in letter_counts
    ]
    browse_data = {
        'version': 1,
        'count': len(items),
        'letters': letters,
        'pos': sorted(all_pos),
        'items': items,
    }
    return catalog_data, browse_data


def build_punarchi_review_data() -> dict:
    """Compile declarative Nannool Punarchi TOML rules, closed classes, and golden witnesses for Playground review."""
    rules_toml = tomllib.loads((ROOT / 'lexicon/punarchi-nannool.toml').read_text(encoding='utf-8'))
    golden_rows = []
    golden_path = ROOT / 'tests/golden/punarchi_nannool.jsonl'
    if golden_path.exists():
        for raw_line in golden_path.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line:
                continue
            golden_rows.append(json.loads(line))

    rules = [
        {
            'id': r['id'],
            'sutra': int(r['sutra']),
            'chapter': r['chapter'],
            'stage': int(r['stage']),
            'substage': str(r.get('substage', '')),
            'priority': int(r.get('priority', 50)),
            'transform': r['transform'],
            'relation': r.get('relation', 'unspecified'),
            'left_match': r.get('left_match', ''),
            'right_match': r.get('right_match', ''),
            'action': r.get('action', ''),
            'optional': bool(r.get('optional', False)),
            'poetic': bool(r.get('poetic', False)),
            'reversible': bool(r.get('reversible', True)),
            'evidence_layer': r.get('evidence_layer', 'root_sutra'),
        }
        for r in rules_toml.get('rule', [])
    ]

    closed_classes = [
        {
            'id': cc['class_id'],
            'sutra': int(cc['sutra']),
            'stems': list(cc.get('stems', [])),
            'oblique_map': dict(cc.get('oblique_map', {})),
            'notes': cc.get('notes', ''),
        }
        for cc in rules_toml.get('closed_class', [])
    ]

    chariyais = [
        {
            'id': c['id'],
            'form': c['form'],
            'sutra': int(c.get('sutra', 244)),
            'attach_classes': list(c.get('attach_classes', [])),
            'post_um': bool(c.get('post_um', False)),
            'suppress_205': bool(c.get('suppress_205', False)),
        }
        for c in rules_toml.get('chariyai', [])
    ]

    case_suffixes = [
        {
            'case_number': int(c['case_number']),
            'form': c['form'],
            'sutra': int(c.get('sutra', 242)),
            'force_165': bool(c.get('force_165', False)),
        }
        for c in rules_toml.get('case_suffix', [])
    ]

    crosswalk_path = ROOT / 'tests/reference/punarchi-nannool/vellaivaranar-crosswalk.json'
    crosswalk = json.loads(crosswalk_path.read_text(encoding='utf-8')) if crosswalk_path.exists() else {}

    return {
        'profile': 'nannool-v1',
        'rule_count': len(rules),
        'closed_class_count': len(closed_classes),
        'golden_count': len(golden_rows),
        'wikisource_page_base': crosswalk.get('wikisource_page_base', ''),
        'sutra_notes': crosswalk.get('sutras', {}),
        'rules': rules,
        'closed_classes': closed_classes,
        'chariyais': chariyais,
        'case_suffixes': case_suffixes,
        'golden_vectors': golden_rows,
    }


def catalog():
    return build_artifacts()[0]


def resolve_lexicon_channel(cli_channel: str | None = None) -> str:
    """Resolve the playground `.tlpack` channel (`full` default, or `open`)."""
    raw = (
        cli_channel
        if cli_channel is not None
        else os.environ.get('TAMIL_LEXICON_CHANNEL') or os.environ.get('VITE_LEXICON_CHANNEL') or 'full'
    )
    normalized = raw.strip().lower() or 'full'
    if normalized not in ('full', 'open'):
        raise ValueError(f"Unsupported lexicon channel: {raw!r} (expected 'full' or 'open')")
    return normalized


def sync_lexicon_packs(
    public_beta: bool = False,
    lexicon_channel: str | None = None,
) -> dict | None:
    """Copy compiled `.tlpack` v2 packs and a MANIFEST.json into `playground/public/lexicon-packs/`.

    When `lexicon_channel == 'open'`, `local/` packs are excluded (and any stale `local/`
    directory in `playground/public/lexicon-packs/` is removed) so open-only deployments
    ship strictly `verified_open` (`CC-BY-SA-4.0`) packs. When `lexicon_channel == 'full'`
    (the default), all 12 packs are synced with each pack's exact `pack_tier`, `rights_status`,
    `license`, and `source_ids` preserved verbatim. `--public-beta` alone does not strip `local/`.
    """
    channel = resolve_lexicon_channel(lexicon_channel)
    strip_local = channel == 'open'
    src_dir = ROOT / 'dist/lexicon-packs'
    src_manifest = src_dir / 'MANIFEST.json'
    if not src_manifest.is_file():
        return None

    manifest = json.loads(src_manifest.read_text(encoding='utf-8'))
    dest_dir = ROOT / 'playground/public/lexicon-packs'
    dest_dir.mkdir(parents=True, exist_ok=True)

    if strip_local:
        local_dest = dest_dir / 'local'
        if local_dest.exists():
            shutil.rmtree(local_dest)

    kept_packs = []
    expected_rel_paths: set[str] = set()
    for entry in manifest.get('packs', []):
        rel_file = str(entry.get('file', '')).replace('\\', '/').lstrip('/')
        if not rel_file:
            continue
        summary = entry.get('summary', {})
        is_local = rel_file.startswith('local/') or '/local/' in rel_file or summary.get('pack_tier') == 'local_historical'
        if strip_local and is_local:
            continue
        src_file = src_dir / rel_file
        if not src_file.is_file():
            continue
        dst_file = dest_dir / rel_file
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        if not dst_file.exists() or dst_file.stat().st_size != src_file.stat().st_size or not filecmp.cmp(src_file, dst_file, shallow=False):
            shutil.copy2(src_file, dst_file)
        kept_packs.append({**entry, 'file': rel_file})
        expected_rel_paths.add(rel_file)

    for existing_pack in dest_dir.rglob('*.tlpack'):
        rel = existing_pack.relative_to(dest_dir).as_posix()
        if rel not in expected_rel_paths:
            existing_pack.unlink()

    filtered_manifest = {
        **({'schema_version': manifest['schema_version']} if 'schema_version' in manifest else {}),
        'pack_count': len(kept_packs),
        'packs': kept_packs,
    }
    manifest_content = json.dumps(filtered_manifest, ensure_ascii=True, indent=2) + '\n'
    dest_manifest = dest_dir / 'MANIFEST.json'
    if not dest_manifest.exists() or dest_manifest.read_text(encoding='utf-8') != manifest_content:
        dest_manifest.write_text(manifest_content, encoding='utf-8', newline='\n')

    return {
        'public_beta': public_beta,
        'lexicon_channel': channel,
        'pack_count': len(kept_packs),
        'pack_ids': [p.get('summary', {}).get('pack_id') for p in kept_packs],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog-only', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--public-beta', action='store_true')
    parser.add_argument(
        '--lexicon-channel',
        choices=('full', 'open'),
        default=None,
        help="Select '.tlpack' channel: 'full' (all 12 packs, default) or 'open' (verified_open only).",
    )
    parser.add_argument(
        '--wasm-profile',
        choices=('default', 'core', 'full'),
        default=None,
        help="WASM Cargo profile ('default' = slim ~4 MiB Apache-2.0 with .tlpack v2 streaming; 'full' = includes legacy v1 embedded packs).",
    )
    args = parser.parse_args()
    public_beta = args.public_beta or os.environ.get('TAMIL_PLAYGROUND_PUBLIC_BETA', '').strip().lower() in ('1', 'true', 'yes')
    lexicon_channel = resolve_lexicon_channel(args.lexicon_channel)
    wasm_profile = (
        args.wasm_profile
        or os.environ.get('TAMIL_PLAYGROUND_WASM_PROFILE', '').strip().lower()
        or 'full'
    )
    if wasm_profile not in ('default', 'core', 'full'):
        wasm_profile = 'full'
    catalog_data, browse_data = build_artifacts()
    punarchi_data = build_punarchi_review_data()
    path = ROOT/'playground/src/generated/lexicon-catalog.json'
    punarchi_path = ROOT/'playground/src/generated/punarchi-review-data.json'
    browse_path = ROOT/'playground/public/lexicon-browse-index.json'
    content = json.dumps(catalog_data, ensure_ascii=True, indent=2)+'\n'
    punarchi_content = json.dumps(punarchi_data, ensure_ascii=True, separators=(',', ':'))+'\n'
    browse_content = json.dumps(browse_data, ensure_ascii=True, separators=(',', ':'))+'\n'
    if args.check:
        if not path.exists() or path.read_text(encoding='utf-8') != content:
            raise SystemExit('Playground catalog is stale; run tools/prepare_playground.py --catalog-only')
        if not punarchi_path.exists() or punarchi_path.read_text(encoding='utf-8') != punarchi_content:
            raise SystemExit('Playground punarchi review data is stale; run tools/prepare_playground.py --catalog-only')
        if not browse_path.exists() or browse_path.read_text(encoding='utf-8') != browse_content:
            raise SystemExit('Playground browse index is stale; run tools/prepare_playground.py --catalog-only')
        print('Playground catalog, punarchi review data, and browse index verified.')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding='utf-8') != content:
        path.write_text(content, encoding='utf-8', newline='\n')
    if not punarchi_path.exists() or punarchi_path.read_text(encoding='utf-8') != punarchi_content:
        punarchi_path.write_text(punarchi_content, encoding='utf-8', newline='\n')
    browse_path.parent.mkdir(parents=True, exist_ok=True)
    if not browse_path.exists() or browse_path.read_text(encoding='utf-8') != browse_content:
        browse_path.write_text(browse_content, encoding='utf-8', newline='\n')
    for ident, directory in PACKS:
        public = ROOT/'playground/public/lexicon-notices'/ident
        for source in [directory/'ATTRIBUTION_AND_TERMS.md', *sorted((directory/'notices').glob('*.md'))]:
            relative = source.relative_to(directory)
            destination = public/relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists() or destination.read_bytes() != source.read_bytes():
                destination.write_bytes(source.read_bytes())
    if not args.catalog_only:
        env = dict(os.environ)
        env['PATH'] = str(Path.home()/'.cargo/bin')+os.pathsep+env['PATH']
        os.environ['PATH'] = env['PATH']
        sys.path.insert(0, str(ROOT))
        from tools.prepare_extended_lexicon import prepare_extended
        print(json.dumps(prepare_extended(), sort_keys=True))
        tlpack_sync = sync_lexicon_packs(public_beta=public_beta, lexicon_channel=lexicon_channel)
        if tlpack_sync is not None:
            print(json.dumps(tlpack_sync, sort_keys=True))
        if not public_beta:
            from tools.prepare_historical_lexicon import prepare
            print(json.dumps(prepare(), sort_keys=True))
        from tools.tasks import sync_bindings
        sync_bindings(profile=wasm_profile, targets=('wasm-web',), release=True)

if __name__ == '__main__': main()
