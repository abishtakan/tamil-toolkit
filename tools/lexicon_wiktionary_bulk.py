"""Track 2B: Official English Wiktionary Tamil bulk snapshot downloader, strict parser, and multi-pack dry-run.

Acquires pinned revisions exclusively from ``en.wiktionary.org`` (``CC-BY-SA-4.0`` /
``GFDL``), validates Unicode scalar integrity, parses each ``==Tamil==`` section
with full POS separation and fail-closed template/markup rejection, maps pluricentric
TN/SL dialect and register labels, and partitions clean candidates across ``core``,
``names_taxa``, and ``regional`` packs into ``target/lexicon/``.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import http.client
import json
from pathlib import Path
import re
import shutil
import sys
import threading
import time
from typing import Any
import unicodedata
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.lexicon import allocate_id, digest, json_text, native_inspect  # noqa: E402
from tools.lexicon_packs import (  # noqa: E402
    CANONICAL_CSV_TABLES,
    _render_vocabularies_toml,
    promote as promote_pack,
    validate_canonical_dir,
)
from tools.lexicon_review import claim_revision, evidence_hash  # noqa: E402
from tools.lexicon_tables import read_rows, write_rows  # noqa: E402
from tools.lexicon_wiktionary_candidate import PINNED_NOTICE_REQUIREMENTS  # noqa: E402

BULK_SNAPSHOT_DIR = ROOT / "data/sources/enwiktionary-tamil"
BULK_DRYRUN_DIR = ROOT / "target/lexicon/wiktionary-bulk-dryrun"
BULK_DRYRUN_REPORT = ROOT / "target/lexicon/wiktionary-bulk-dryrun-report.json"
CANONICAL_VOCAB_PATH = ROOT / "lexicon/dictionary/vocabularies.toml"
EXISTING_NOTICES_DIR = ROOT / "data/curation/wiktionary-candidate/notices"

API_HOST = "en.wiktionary.org"
API_PATH = "/w/api.php"
API_ENDPOINT = f"https://{API_HOST}{API_PATH}"
USER_AGENT = "tamil-toolkit-curation/1.0 (https://github.com/abishtakan/tamil-toolkit)"
BULK_NAMESPACE = "b8c4e712-3f9a-5d21-8c64-1e9f4a7b3d50"

DEFAULT_CATEGORIES: tuple[str, ...] = (
    "Category:Tamil lemmas",
    "Category:Tamil proper nouns",
    "Category:Tamil multiword terms",
    "Category:Tamil dialectal terms",
)

# Full UD-aligned POS mapping for Wiktionary Tamil headings (no collapsing).
POS_HEADING_MAP: dict[str, str] = {
    "Noun": "NOUN",
    "Proper noun": "PROPN",
    "Verb": "VERB",
    "Adjective": "ADJ",
    "Adverb": "ADV",
    "Interjection": "INTJ",
    "Pronoun": "PRON",
    "Postposition": "ADP",
    "Preposition": "ADP",
    "Particle": "PART",
    "Numeral": "NUM",
    "Conjunction": "CONJ",
    "Determiner": "DET",
}

NON_DEFINITION_SECTIONS: dict[str, str] = {
    "Pronunciation": "PRONUNCIATION_SECTION_EXCLUDED",
    "Etymology": "ETYMOLOGY_SECTION_EXCLUDED",
    "References": "REFERENCES_SECTION_EXCLUDED",
    "Further reading": "REFERENCES_SECTION_EXCLUDED",
    "See also": "SEE_ALSO_SECTION_EXCLUDED",
    "Alternative forms": "ALTERNATIVE_FORMS_SECTION_EXCLUDED",
    "Alternative spellings": "ALTERNATIVE_FORMS_SECTION_EXCLUDED",
    "Derived terms": "DERIVED_TERMS_SECTION_EXCLUDED",
    "Related terms": "RELATED_TERMS_SECTION_EXCLUDED",
    "Synonyms": "SYNONYMS_SECTION_EXCLUDED",
    "Antonyms": "ANTONYMS_SECTION_EXCLUDED",
    "Declension": "DECLENSION_SECTION_EXCLUDED",
    "Conjugation": "CONJUGATION_SECTION_EXCLUDED",
    "Inflection": "INFLECTION_SECTION_EXCLUDED",
    "Usage notes": "USAGE_NOTES_SECTION_EXCLUDED",
    "Translations": "TRANSLATIONS_SECTION_EXCLUDED",
    "Descendants": "DESCENDANTS_SECTION_EXCLUDED",
    "Coordinate terms": "COORDINATE_TERMS_SECTION_EXCLUDED",
    "Hyponyms": "HYPONYMS_SECTION_EXCLUDED",
    "Hypernyms": "HYPERNYMS_SECTION_EXCLUDED",
    "Meronyms": "MERONYMS_SECTION_EXCLUDED",
    "Holonyms": "HOLONYMS_SECTION_EXCLUDED",
    "Anagrams": "ANAGRAMS_SECTION_EXCLUDED",
    "Trivia": "TRIVIA_SECTION_EXCLUDED",
    "Quotations": "QUOTATION_SECTION_EXCLUDED",
}

# Build invisible/control sets without embedding literal joiners or BOM in Python source.
BOM_CHAR = chr(0xFEFF)
ZWNJ_CHAR = chr(0x200C)
ZWJ_CHAR = chr(0x200D)
JOINER_CHARS = frozenset({ZWNJ_CHAR, ZWJ_CHAR})
EXTRA_FORMAT_CONTROL_CPS = frozenset({0x00AD, 0x2028, 0x2029, 0x2060, 0xFEFF})

TAMIL_CHAR_RE = re.compile(r"[\u0B80-\u0BFF]")
SURROGATE_RE = re.compile("[" + chr(0xD800) + "-" + chr(0xDFFF) + "]")
LANG_HEADER_RE = re.compile(r"^==\s*([^=\n]+?)\s*==\s*$")
SUB_HEADER_RE = re.compile(r"^(={3,5})\s*([^=\n]+?)\s*\1\s*$")
WIKILINK_RE = re.compile(r"\[\[([^\[\]|]+?)(?:\|([^\[\]]+?))?\]\]")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_TAG_RE = re.compile(r"<\s*/?\s*[A-Za-z!][^>]*>")
BOLD_ITALIC_RE = re.compile(r"'{2,5}")

FORBIDDEN_SENSE_MARKERS: tuple[tuple[str, str], ...] = (
    ("(\u0b95\u0bb2\u0bc8\u0b9a\u0bcd\u0b9a\u0bca\u0bb2\u0bcd)", "KALAICHOL_PLACEHOLDER_REJECTED"),
    ("Module:ta-IPA", "FORBIDDEN_TA_IPA_MODULE_REJECTED"),
    ("{{ta-IPA", "FORBIDDEN_TA_IPA_TEMPLATE_REJECTED"),
    ("{{ta-decl", "FORBIDDEN_DECLENSION_TEMPLATE_REJECTED"),
    ("{{ta-conj", "FORBIDDEN_CONJUGATION_TEMPLATE_REJECTED"),
    ("verb_conjugations", "FORBIDDEN_VERB_CONJUGATION_CLAIM_REJECTED"),
    ("*PDr", "FORBIDDEN_SYNTHETIC_PDR_REJECTED"),
    ("DEDR", "FORBIDDEN_UNPINNED_DEDR_REJECTED"),
)

# Pluricentric TN/SL dialect and register/domain/temporal mappings for {{lb|ta|...}} and {{q|...}}.
REGION_LABEL_MAP: dict[str, dict[str, str | None]] = {
    "sri lanka": {"code": "SL", "parent": None, "display": "Sri Lanka"},
    "sri lankan": {"code": "SL", "parent": None, "display": "Sri Lanka"},
    "sri lankan tamil": {"code": "SL", "parent": None, "display": "Sri Lanka"},
    "sl": {"code": "SL", "parent": None, "display": "Sri Lanka"},
    "eelam": {"code": "SL", "parent": None, "display": "Sri Lanka"},
    "ceylon": {"code": "SL", "parent": None, "display": "Sri Lanka"},
    "jaffna": {"code": "JAFFNA", "parent": "SL", "display": "Jaffna"},
    "jaffna tamil": {"code": "JAFFNA", "parent": "SL", "display": "Jaffna"},
    "batticaloa": {"code": "BATTICALOA", "parent": "SL", "display": "Batticaloa"},
    "batticaloa tamil": {"code": "BATTICALOA", "parent": "SL", "display": "Batticaloa"},
    "vanni": {"code": "VANNI", "parent": "SL", "display": "Vanni"},
    "vanni tamil": {"code": "VANNI", "parent": "SL", "display": "Vanni"},
    "up-country": {"code": "UP_COUNTRY", "parent": "SL", "display": "Up-Country"},
    "upcountry": {"code": "UP_COUNTRY", "parent": "SL", "display": "Up-Country"},
    "up-country tamil": {"code": "UP_COUNTRY", "parent": "SL", "display": "Up-Country"},
    "malaiyaha": {"code": "UP_COUNTRY", "parent": "SL", "display": "Up-Country"},
    "malaiyaha tamil": {"code": "UP_COUNTRY", "parent": "SL", "display": "Up-Country"},
    "trincomalee": {"code": "TRINCOMALEE", "parent": "SL", "display": "Trincomalee"},
    "tamil nadu": {"code": "TN", "parent": None, "display": "Tamil Nadu"},
    "india": {"code": "TN", "parent": None, "display": "India / Tamil Nadu"},
    "indian": {"code": "TN", "parent": None, "display": "India / Tamil Nadu"},
    "indian tamil": {"code": "TN", "parent": None, "display": "India / Tamil Nadu"},
    "tn": {"code": "TN", "parent": None, "display": "Tamil Nadu"},
    "chennai": {"code": "CHENNAI", "parent": "TN", "display": "Chennai"},
    "madras": {"code": "CHENNAI", "parent": "TN", "display": "Chennai"},
    "madras bashai": {"code": "CHENNAI", "parent": "TN", "display": "Chennai"},
    "madras baashai": {"code": "CHENNAI", "parent": "TN", "display": "Chennai"},
    "kongu": {"code": "KONGU", "parent": "TN", "display": "Kongu"},
    "kongu tamil": {"code": "KONGU", "parent": "TN", "display": "Kongu"},
    "coimbatore": {"code": "KONGU", "parent": "TN", "display": "Kongu"},
    "madurai": {"code": "MADURAI", "parent": "TN", "display": "Madurai"},
    "madurai tamil": {"code": "MADURAI", "parent": "TN", "display": "Madurai"},
    "nellai": {"code": "NELLAI", "parent": "TN", "display": "Nellai"},
    "nellai tamil": {"code": "NELLAI", "parent": "TN", "display": "Nellai"},
    "tirunelveli": {"code": "NELLAI", "parent": "TN", "display": "Nellai"},
    "tirunelveli tamil": {"code": "NELLAI", "parent": "TN", "display": "Nellai"},
    "kanyakumari": {"code": "KANYAKUMARI", "parent": "TN", "display": "Kanyakumari"},
    "kanyakumari dialect": {"code": "KANYAKUMARI", "parent": "TN", "display": "Kanyakumari"},
    "kanyakumari tamil": {"code": "KANYAKUMARI", "parent": "TN", "display": "Kanyakumari"},
    "kumari": {"code": "KANYAKUMARI", "parent": "TN", "display": "Kanyakumari"},
    "nanjil": {"code": "KANYAKUMARI", "parent": "TN", "display": "Kanyakumari"},
    "pudukkottai": {"code": "PUDUKKOTTAI", "parent": "TN", "display": "Pudukkottai"},
    "pudukkottai tamil": {"code": "PUDUKKOTTAI", "parent": "TN", "display": "Pudukkottai"},
    "tanjore": {"code": "THANJAVUR", "parent": "TN", "display": "Thanjavur"},
    "tanjore tamil": {"code": "THANJAVUR", "parent": "TN", "display": "Thanjavur"},
    "thanjavur": {"code": "THANJAVUR", "parent": "TN", "display": "Thanjavur"},
    "thanjavur tamil": {"code": "THANJAVUR", "parent": "TN", "display": "Thanjavur"},
    "chennai tamil": {"code": "CHENNAI", "parent": "TN", "display": "Chennai"},
    "trincomalee tamil": {"code": "TRINCOMALEE", "parent": "SL", "display": "Trincomalee"},
    "south india": {"code": "TN", "parent": None, "display": "South India / Tamil Nadu"},
    "singapore": {"code": "SG", "parent": None, "display": "Singapore"},
    "singaporean": {"code": "SG", "parent": None, "display": "Singapore"},
    "singapore tamil": {"code": "SG", "parent": None, "display": "Singapore"},
    "malaysia": {"code": "MY", "parent": None, "display": "Malaysia"},
    "malaysian": {"code": "MY", "parent": None, "display": "Malaysia"},
    "malaysian tamil": {"code": "MY", "parent": None, "display": "Malaysia"},
}

NEGATING_REGION_PREFIXES = frozenset({"outside", "except", "except in", "not"})

TN_SL_REGIONAL_CODES = frozenset({
    "SL", "JAFFNA", "BATTICALOA", "VANNI", "UP_COUNTRY", "TRINCOMALEE",
    "TN", "CHENNAI", "KONGU", "MADURAI", "NELLAI", "KANYAKUMARI", "PUDUKKOTTAI", "THANJAVUR",
})

REGISTER_LABEL_MAP: dict[str, str] = {
    "colloquial": "colloquial",
    "spoken": "colloquial",
    "informal": "informal",
    "casual": "informal",
    "slang": "slang",
    "cant": "cant",
    "vulgar": "vulgar",
    "profanity": "profanity",
    "obscene": "obscene",
    "coarse": "coarse",
    "offensive": "offensive",
    "derogatory": "derogatory",
    "pejorative": "pejorative",
    "contempt": "derogatory",
    "demeaning": "derogatory",
    "dismissive": "dismissive",
    "rude": "rude",
    "impolite": "impolite",
    "literary": "literary",
    "literary tamil": "literary",
    "written": "written",
    "written tamil": "written",
    "formal": "formal",
    "formal tamil": "formal",
    "higher register": "elevated",
    "elevated": "elevated",
    "poetic": "poetic",
    "honorific": "honorific",
    "non-honorific": "non_honorific",
    "polite": "polite",
    "respectful": "honorific",
    "familiar": "familiar",
    "intimate": "familiar",
    "endearing": "endearing",
    "term of endearment": "endearing",
    "humorous": "humorous",
    "jocular": "humorous",
    "ironic": "ironic",
    "sarcastic": "sarcastic",
    "figurative": "figurative",
    "figuratively": "figurative",
    "metaphor": "figurative",
    "metaphoric": "figurative",
    "metaphorical": "figurative",
    "metonym": "figurative",
    "metonymic": "figurative",
    "hyperbole": "figurative",
    "figure of speech": "figurative",
    "literal": "literal",
    "idiom": "idiomatic",
    "idiomatic": "idiomatic",
    "euphemism": "euphemistic",
    "euphemistic": "euphemistic",
    "childish": "childish",
    "baby talk": "childish",
    "dialectal": "dialectal",
    "regional": "dialectal",
    "standard": "standard",
    "puristic": "puristic",
    "proscribed": "proscribed",
    "sentamil": "literary",
    "koduntamil": "colloquial",
    "spoken tamil": "colloquial",
}

GRAMMAR_SYSTEM_LABEL_MAP: dict[str, str] = {
    "transitive": "transitive",
    "intransitive": "intransitive",
    "ditransitive": "ditransitive",
    "ambitransitive": "ambitransitive",
    "auxiliary": "auxiliary",
    "reflexive": "reflexive",
    "reflexive pronoun": "reflexive",
    "causative": "causative",
    "impersonal": "impersonal",
    "passive": "passive",
    "imperative": "imperative",
    "interrogative": "interrogative",
    "exclamative": "exclamative",
    "conjunctive": "conjunctive",
    "countable": "countable",
    "uncountable": "uncountable",
    "plural": "plural",
    "in the plural": "plural",
    "plural only": "plural_only",
    "singular": "singular",
    "collective": "collective",
    "masculine": "masculine",
    "feminine": "feminine",
    "neuter": "neuter",
    "inanimate": "inanimate",
    "distal": "distal",
    "proximal": "proximal",
    "yonder": "distal",
    "exclusive": "exclusive",
    "clitic": "clitic",
    "indeclinable": "indeclinable",
    "defective": "defective",
    "tag question": "tag_question",
    "negative polarity": "negative_polarity",
    "absolute negation": "absolute_negation",
    "existential negation": "existential_negation",
    "compound": "in_compounds",
    "compounds": "in_compounds",
    "in compounds": "in_compounds",
    "often in compounds": "in_compounds",
    "mostly in compounds": "in_compounds",
    "especially in compounds": "in_compounds",
    "exclusively in compounds": "in_compounds",
}

TEMPORAL_LABEL_MAP: dict[str, str] = {
    "archaic": "archaic",
    "obsolete": "obsolete",
    "dated": "dated",
    "dated sense": "dated",
    "neologism": "neologism",
    "historical": "historical",
    "rare": "rare",
    "uncommon": "rare",
    "classical": "classical",
    "sangam": "classical",
    "old tamil": "old_tamil",
    "middle tamil": "middle_tamil",
}

SOCIAL_USAGE_LABEL_MAP: dict[str, str] = {
    "brahmin": "brahmin_sociolect",
    "brahmin tamil": "brahmin_sociolect",
    "iyer": "brahmin_sociolect",
    "iyengar": "brahmin_sociolect",
    "muslim": "muslim_sociolect",
    "muslim tamil": "muslim_sociolect",
    "muslim usage": "muslim_sociolect",
    "christian": "christian_usage",
}

# Explicit reviewed finite domain mapping for Wiktionary subject-matter labels.
# Unmapped tokens (prose fragments, colloquial modifiers, unattested localities)
# must never fall back to synthetic domain identifiers.
DOMAIN_LABEL_MAP: dict[str, str] = {
    "abrahamism": "abrahamism",
    "accounting": "accounting",
    "administration": "administration",
    "agriculture": "agriculture",
    "alchemy": "alchemy",
    "anatomy": "anatomy",
    "anthropology": "anthropology",
    "archaeology": "archaeology",
    "architectural element": "architecture",
    "architectural elements": "architecture",
    "architecture": "architecture",
    "arithmetic": "arithmetic",
    "arithmetics": "arithmetic",
    "art": "art",
    "artificial intelligence": "artificial_intelligence",
    "astrology": "astrology",
    "astronomy": "astronomy",
    "automotive": "automotive",
    "aviation": "aviation",
    "banking": "banking",
    "basketball": "basketball",
    "bharatanatyam": "dance",
    "bible": "biblical",
    "biblical": "biblical",
    "biblical character": "biblical",
    "biblical figure": "biblical",
    "biology": "biology",
    "board games": "board_games",
    "botany": "botany",
    "broadcasting": "broadcasting",
    "buddhism": "buddhism",
    "business": "business",
    "card games": "card_games",
    "carpentry": "carpentry",
    "catholicism": "catholicism",
    "chemistry": "chemistry",
    "chess": "chess",
    "christianity": "christianity",
    "cinema": "cinema",
    "clothes": "clothing",
    "clothing": "clothing",
    "communism": "communism",
    "computer": "computing",
    "computing": "computing",
    "construction": "construction",
    "cooking": "cooking",
    "cricket": "cricket",
    "cytology": "cytology",
    "dance": "dance",
    "dances": "dance",
    "dancing": "dance",
    "dermatology": "dermatology",
    "disease": "pathology",
    "diseases": "pathology",
    "drama": "drama",
    "dress": "clothing",
    "ecology": "ecology",
    "economics": "economics",
    "electricity": "electricity",
    "electronics": "electronics",
    "entomology": "entomology",
    "epidemiology": "epidemiology",
    "ethics": "ethics",
    "etymology": "etymology",
    "film": "film",
    "finance": "finance",
    "fireworks": "fireworks",
    "fishing": "fishing",
    "football": "football",
    "forestry": "forestry",
    "game": "games",
    "games": "games",
    "gaming": "gaming",
    "genealogy": "genealogy",
    "genetics": "genetics",
    "geography": "geography",
    "geology": "geology",
    "geometry": "geometry",
    "geomorphology": "geomorphology",
    "government": "government",
    "grammar": "grammar",
    "graph theory": "graph_theory",
    "health": "health",
    "heraldry": "heraldry",
    "hindu god": "hindu_deity",
    "hinduism": "hinduism",
    "history": "history",
    "horticulture": "horticulture",
    "hydrology": "hydrology",
    "ichthyology": "ichthyology",
    "indian politics": "politics",
    "inorganic compound": "chemistry",
    "internet": "internet",
    "islam": "islam",
    "jainism": "jainism",
    "japanese mythology": "japanese_mythology",
    "judaism": "judaism",
    "landforms": "geography",
    "law": "law",
    "law enforcement": "law_enforcement",
    "legal": "law",
    "letter writing": "letter_writing",
    "lexicography": "lexicography",
    "lgbtq": "lgbtq",
    "linguistic morphology": "morphology",
    "linguistics": "linguistics",
    "literature": "literature",
    "logic": "logic",
    "management": "management",
    "marxism": "marxism",
    "masonry": "masonry",
    "math": "mathematics",
    "mathematics": "mathematics",
    "media": "media",
    "medicine": "medicine",
    "metallurgy": "metallurgy",
    "meteorology": "meteorology",
    "military": "military",
    "mineralogy": "mineralogy",
    "money": "money",
    "music": "music",
    "musical instruments": "musical_instruments",
    "mythological creature": "mythology",
    "mythology": "mythology",
    "narratology": "narratology",
    "nautical": "nautical",
    "networking": "networking",
    "neurology": "neurology",
    "numismatics": "numismatics",
    "nutrition": "nutrition",
    "occult": "occult",
    "oncology": "oncology",
    "onomastics": "onomastics",
    "ophthalmology": "ophthalmology",
    "organic chemistry": "organic_chemistry",
    "orthography": "orthography",
    "parapsychology": "parapsychology",
    "pathology": "pathology",
    "percussion instrument": "musical_instruments",
    "pharmacology": "pharmacology",
    "philosophy": "philosophy",
    "phonetics": "phonetics",
    "phonology": "phonology",
    "photography": "photography",
    "physics": "physics",
    "physiology": "physiology",
    "play": "drama",
    "poetry": "poetry",
    "politics": "politics",
    "pragmatics": "pragmatics",
    "probability theory": "probability_theory",
    "programming": "programming",
    "property law": "property_law",
    "prosody": "prosody",
    "psychology": "psychology",
    "puranas": "hinduism",
    "religion": "religion",
    "rhetoric": "rhetoric",
    "roman catholic": "catholicism",
    "science": "science",
    "sciences": "science",
    "semantics": "semantics",
    "set theory": "set_theory",
    "shaivism": "shaivism",
    "shinto": "shinto",
    "smoking": "smoking",
    "social media": "social_media",
    "social sciences": "social_sciences",
    "sociology": "sociology",
    "spiritual": "religion",
    "spiritualism": "religion",
    "sports": "sports",
    "surgery": "surgery",
    "syntax": "syntax",
    "tamil religion": "tamil_religion",
    "taxonomy": "taxonomy",
    "telecommunication": "telecommunication",
    "television": "television",
    "theology": "theology",
    "time": "time",
    "trademark": "trademark",
    "tv": "television",
    "urology": "urology",
    "vaishnavism": "vaishnavism",
    "vedic religion": "vedic_religion",
    "vedicism": "vedic_religion",
    "vehicles": "vehicles",
    "virology": "virology",
    "volcanology": "volcanology",
    "watercraft": "nautical",
    "weapon": "military",
    "weapons": "military",
    "weaving": "weaving",
    "yoga": "yoga",
    "zodiac": "zodiac",
    "zoology": "zoology",
    "zootomy": "zootomy",
}

DOMAIN_LABEL_IGNORE = frozenset({
    "_", "&", "&!&", "and", "or", "sometimes", "especially", "chiefly", "usually",
    "often", "also", "now", "rarely", "mildly", "literally", "by extension",
    "specifically", "etc", "etc.", "in", "of", "with", "for", "as", "to",
    "from", "by", "on", "at", "the", "a", "an",
})

_THREAD_LOCAL = threading.local()


def _get_conn() -> http.client.HTTPSConnection:
    conn = getattr(_THREAD_LOCAL, "conn", None)
    if conn is None:
        conn = http.client.HTTPSConnection(API_HOST, timeout=20)
        _THREAD_LOCAL.conn = conn
    return conn


def _reset_conn() -> None:
    conn = getattr(_THREAD_LOCAL, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except OSError:
            pass
        _THREAD_LOCAL.conn = None


def _api_get_json(params: dict[str, str], retries: int = 4) -> dict[str, Any]:
    """Execute a polite MediaWiki API GET request with keep-alive and retry backoff."""
    query = urllib.parse.urlencode(params)
    url = f"{API_PATH}?{query}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    }
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            conn = _get_conn()
            conn.request("GET", url, headers=headers)
            resp = conn.getresponse()
            raw = resp.read()
            if resp.status == 200:
                if resp.getheader("Content-Encoding", "").lower() == "gzip":
                    raw = gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
            if resp.status in {429, 500, 502, 503, 504}:
                _reset_conn()
                time.sleep(0.5 * (2 ** attempt))
                continue
            raise RuntimeError(f"MediaWiki API HTTP {resp.status}: {raw[:300]!r}")
        except (OSError, http.client.HTTPException, json.JSONDecodeError) as exc:
            last_err = exc
            _reset_conn()
            time.sleep(0.4 * (2 ** attempt))
    raise RuntimeError(f"MediaWiki API request failed after {retries} retries: {last_err}")


def fetch_index(
    snapshot_dir: Path = BULK_SNAPSHOT_DIR,
    categories: tuple[str, ...] = DEFAULT_CATEGORIES,
) -> dict[str, Any]:
    """Fetch and deduplicate namespace-0 pageids/titles across Tamil Wiktionary categories."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    pages_by_id: dict[int, dict[str, Any]] = {}
    category_counts: dict[str, int] = {}

    for category in categories:
        count = 0
        cmcontinue: str | None = None
        while True:
            params: dict[str, str] = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": category,
                "cmnamespace": "0",
                "cmlimit": "500",
                "format": "json",
                "formatversion": "2",
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue
            payload = _api_get_json(params)
            members = payload.get("query", {}).get("categorymembers", [])
            for item in members:
                pid = int(item["pageid"])
                title = str(item["title"])
                count += 1
                entry = pages_by_id.get(pid)
                if entry is None:
                    pages_by_id[pid] = {"pageid": pid, "title": title, "categories": [category]}
                else:
                    if category not in entry["categories"]:
                        entry["categories"].append(category)
            cont = payload.get("continue", {})
            cmcontinue = cont.get("cmcontinue")
            if not cmcontinue:
                break
        category_counts[category] = count

    sorted_pages = [
        {"pageid": pid, "title": info["title"], "categories": sorted(info["categories"])}
        for pid, info in sorted(pages_by_id.items())
    ]
    index_obj = {
        "schema": "enwiktionary-tamil-index-v1",
        "api_endpoint": API_ENDPOINT,
        "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "categories": list(categories),
        "category_counts": category_counts,
        "unique_page_count": len(sorted_pages),
        "pages": sorted_pages,
    }
    index_path = snapshot_dir / "index.json"
    index_path.write_text(
        json.dumps(index_obj, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "index_path": str(index_path),
        "unique_page_count": len(sorted_pages),
        "category_counts": category_counts,
    }


def sync_notices(snapshot_dir: Path = BULK_SNAPSHOT_DIR) -> dict[str, dict[str, Any]]:
    """Verify and store pinned Wikimedia ToU, Wiktionary:Copyrights, and CC-BY-SA-4.0 notices."""
    notices_dir = snapshot_dir / "notices"
    notices_dir.mkdir(parents=True, exist_ok=True)
    verified: dict[str, dict[str, Any]] = {}

    fallback_urls = {
        "wikimedia_tou_api.json": (
            "https://foundation.wikimedia.org/w/api.php?"
            "action=query&prop=revisions&revids=598588&rvprop=ids|timestamp|content&rvslots=main&format=json&formatversion=2"
        ),
        "wiktionary_copyrights_api.json": (
            "https://en.wiktionary.org/w/api.php?"
            "action=query&prop=revisions&revids=87545419&rvprop=ids|timestamp|content&rvslots=main&format=json&formatversion=2"
        ),
        "cc_by_sa_4_0_legalcode.txt": "https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt",
    }

    for filename, req in PINNED_NOTICE_REQUIREMENTS.items():
        dest = notices_dir / filename
        if not dest.is_file():
            existing = EXISTING_NOTICES_DIR / filename
            if existing.is_file() and digest(existing) == req["sha256"]:
                shutil.copyfile(existing, dest)
            else:
                http_req = urllib.request.Request(fallback_urls[filename], headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(http_req, timeout=20) as resp:
                    dest.write_bytes(resp.read())

        actual_sha = digest(dest)
        if actual_sha != req["sha256"]:
            raise ValueError(f"Notice SHA-256 mismatch for {filename}: {actual_sha} != {req['sha256']}")

        if filename.endswith(".json"):
            payload = json.loads(dest.read_text(encoding="utf-8"))
            page = payload["query"]["pages"][0]
            rev = page["revisions"][0]
            if page.get("pageid") != req["pageid"] or rev.get("revid") != req["revid"]:
                raise ValueError(f"Notice revision mismatch in {filename}")
            if rev.get("timestamp") != req["timestamp"]:
                raise ValueError(f"Notice timestamp mismatch in {filename}")
        else:
            if req["required_text"] not in dest.read_text(encoding="utf-8"):
                raise ValueError(f"Notice text check failed in {filename}")

        verified[filename] = {"sha256": actual_sha, "bytes": dest.stat().st_size}

    attr_md = notices_dir / "ATTRIBUTION_AND_LICENSE.md"
    attr_md.write_text(
        "\n".join([
            "# Attribution & License Notices: English Wiktionary Tamil Bulk Snapshot",
            "",
            "> **Engineering Provenance Notice (Not Legal Advice):**",
            "> Upstream English Wiktionary entries are licensed under `CC-BY-SA-4.0` (and `GFDL` where applicable per Wikimedia Terms of Use Section 7).",
            "> License terms on Wiktionary data apply strictly to the data snapshot and derived data packs; they do **not** relicense the MIT-licensed Rust core crates or toolkit engine.",
            "",
            "## Source Provenance",
            "",
            f"- **API Endpoint:** `{API_ENDPOINT}`",
            "- **Categories Queried:** " + ", ".join(f"`{c}`" for c in DEFAULT_CATEGORIES),
            "- **Per-Revision Provenance Fields:** `pageid`, `title`, `revid`, `revision_timestamp`, `user`, `sha1`, `wikitext_sha256`, `permalink_url`, `history_url`.",
            "",
            "## Pinned Upstream License & Terms Files",
            "",
            f"- `cc_by_sa_4_0_legalcode.txt` (`sha256={verified['cc_by_sa_4_0_legalcode.txt']['sha256']}`)",
            f"- `wikimedia_tou_api.json` (`pageid=21261`, `revid=598588`, `sha256={verified['wikimedia_tou_api.json']['sha256']}`)",
            f"- `wiktionary_copyrights_api.json` (`pageid=1503`, `revid=87545419`, `sha256={verified['wiktionary_copyrights_api.json']['sha256']}`)",
            "",
        ]),
        encoding="utf-8",
        newline="\n",
    )
    verified["ATTRIBUTION_AND_LICENSE.md"] = {
        "sha256": digest(attr_md),
        "bytes": attr_md.stat().st_size,
    }
    return verified


def _fetch_batch_revisions(
    batch_idx: int,
    page_entries: list[dict[str, Any]],
) -> tuple[int, list[dict[str, Any]], list[int]]:
    cat_by_pid = {int(e["pageid"]): e["categories"] for e in page_entries}
    pids = "|".join(str(e["pageid"]) for e in page_entries)
    payload = _api_get_json({
        "action": "query",
        "prop": "revisions",
        "pageids": pids,
        "rvprop": "ids|timestamp|sha1|user|content",
        "rvslots": "main",
        "format": "json",
        "formatversion": "2",
    })
    pages = payload.get("query", {}).get("pages", [])
    records: list[dict[str, Any]] = []
    missing: list[int] = []
    for page in pages:
        pid = int(page["pageid"])
        if page.get("missing"):
            missing.append(pid)
            continue
        revs = page.get("revisions") or []
        if not revs:
            missing.append(pid)
            continue
        rev = revs[0]
        content = rev.get("slots", {}).get("main", {}).get("content")
        if not isinstance(content, str):
            missing.append(pid)
            continue
        title = str(page["title"])
        revid = int(rev["revid"])
        qtitle = urllib.parse.quote(title.replace(" ", "_"), safe="")
        records.append({
            "pageid": pid,
            "title": title,
            "categories": cat_by_pid.get(pid, []),
            "revid": revid,
            "parentid": rev.get("parentid"),
            "revision_timestamp": str(rev["timestamp"]),
            "user": str(rev.get("user") or ""),
            "sha1": str(rev.get("sha1") or ""),
            "wikitext_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "permalink_url": f"https://en.wiktionary.org/w/index.php?title={qtitle}&oldid={revid}",
            "history_url": f"https://en.wiktionary.org/w/index.php?title={qtitle}&action=history",
            "wikitext": content,
        })
    return batch_idx, records, missing


def fetch_pages_resumable(
    snapshot_dir: Path = BULK_SNAPSHOT_DIR,
    *,
    batch_size: int = 50,
    max_workers: int = 8,
    time_budget_s: float = 7.0,
) -> dict[str, Any]:
    """Fetch pinned page revisions in resumable <10s chunks into staging JSON files."""
    index_path = snapshot_dir / "index.json"
    if not index_path.is_file():
        raise FileNotFoundError(f"Missing index.json at {index_path}; run fetch-index first.")
    index_obj = json.loads(index_path.read_text(encoding="utf-8"))
    all_entries = index_obj["pages"]

    staging_dir = snapshot_dir / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    fetched_pids: set[int] = set()
    missing_pids: set[int] = set()
    existing_batches = sorted(staging_dir.glob("batch_*.json"))
    next_batch_idx = 0
    for bfile in existing_batches:
        data = json.loads(bfile.read_text(encoding="utf-8"))
        for rec in data.get("records", []):
            fetched_pids.add(int(rec["pageid"]))
        for mpid in data.get("missing_pageids", []):
            missing_pids.add(int(mpid))
        next_batch_idx = max(next_batch_idx, int(bfile.stem.split("_")[1]) + 1)

    remaining_entries = [e for e in all_entries if int(e["pageid"]) not in fetched_pids and int(e["pageid"]) not in missing_pids]
    if not remaining_entries:
        return {
            "fetched_now": 0,
            "total_fetched": len(fetched_pids),
            "missing_count": len(missing_pids),
            "remaining": 0,
            "done": True,
        }

    batches = [
        (next_batch_idx + i, remaining_entries[i * batch_size : (i + 1) * batch_size])
        for i in range((len(remaining_entries) + batch_size - 1) // batch_size)
    ]

    start = time.monotonic()
    fetched_now = 0
    cursor = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        while cursor < len(batches) and (time.monotonic() - start) < time_budget_s:
            window = batches[cursor : cursor + max_workers * 2]
            cursor += len(window)
            futures = {pool.submit(_fetch_batch_revisions, bidx, chunk): bidx for bidx, chunk in window}
            for fut in as_completed(futures):
                bidx, records, missing = fut.result()
                out_file = staging_dir / f"batch_{bidx:05d}.json"
                out_file.write_text(
                    json.dumps(
                        {"batch_idx": bidx, "records": records, "missing_pageids": missing},
                        ensure_ascii=True,
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
                for rec in records:
                    fetched_pids.add(int(rec["pageid"]))
                    fetched_now += 1
                for mpid in missing:
                    missing_pids.add(int(mpid))

    rem_after = len(all_entries) - len(fetched_pids) - len(missing_pids)
    return {
        "fetched_now": fetched_now,
        "total_fetched": len(fetched_pids),
        "missing_count": len(missing_pids),
        "remaining": max(0, rem_after),
        "done": rem_after <= 0,
    }


def finalize_snapshot(snapshot_dir: Path = BULK_SNAPSHOT_DIR, *, keep_staging: bool = False) -> dict[str, Any]:
    """Merge staged JSON batches into deterministic sorted pages.jsonl.gz and snapshots_manifest.json."""
    index_path = snapshot_dir / "index.json"
    index_obj = json.loads(index_path.read_text(encoding="utf-8"))
    staging_dir = snapshot_dir / "staging"
    batch_files = sorted(staging_dir.glob("batch_*.json"))
    if not batch_files:
        raise FileNotFoundError(f"No staged batch files found in {staging_dir}")

    records_by_pid: dict[int, dict[str, Any]] = {}
    missing_pids: set[int] = set()
    for bfile in batch_files:
        payload = json.loads(bfile.read_text(encoding="utf-8"))
        for rec in payload.get("records", []):
            records_by_pid[int(rec["pageid"])] = rec
        for mpid in payload.get("missing_pageids", []):
            missing_pids.add(int(mpid))

    expected_pids = {int(e["pageid"]) for e in index_obj["pages"]}
    accounted = set(records_by_pid) | missing_pids
    unaccounted = expected_pids - accounted
    if unaccounted:
        raise RuntimeError(f"{len(unaccounted)} indexed pageids not yet fetched; run fetch-pages until done=true.")

    pages_gz_path = snapshot_dir / "pages.jsonl.gz"
    uncompressed_hasher = hashlib.sha256()
    sorted_pids = sorted(records_by_pid)
    # Deterministic mtime=0 gzip header so pages.jsonl.gz SHA-256 is reproducible.
    with pages_gz_path.open("wb") as raw_out:
        with gzip.GzipFile(filename="pages.jsonl", mode="wb", fileobj=raw_out, mtime=0) as gz:
            for pid in sorted_pids:
                line = (json.dumps(records_by_pid[pid], ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")
                uncompressed_hasher.update(line)
                gz.write(line)

    notices = sync_notices(snapshot_dir)
    manifest = {
        "schema": "enwiktionary-tamil-bulk-snapshot-v1",
        "api_endpoint": API_ENDPOINT,
        "user_agent": USER_AGENT,
        "license": "CC-BY-SA-4.0 / GFDL (Wikimedia Terms of Use Section 7)",
        "categories": index_obj["categories"],
        "category_counts": index_obj["category_counts"],
        "fetch_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "index_file": "index.json",
        "index_sha256": digest(index_path),
        "pages_file": "pages.jsonl.gz",
        "pages_jsonl_gz_sha256": digest(pages_gz_path),
        "pages_jsonl_gz_bytes": pages_gz_path.stat().st_size,
        "pages_uncompressed_sha256": uncompressed_hasher.hexdigest(),
        "total_indexed_pages": len(expected_pids),
        "total_fetched_pages": len(sorted_pids),
        "missing_pageids": sorted(missing_pids),
        "notices": notices,
    }
    manifest_path = snapshot_dir / "snapshots_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if not keep_staging and staging_dir.exists():
        shutil.rmtree(staging_dir)
    return manifest


def check_unicode_scalar_integrity(text: str) -> tuple[bool, str | None, dict[str, Any]]:
    """Validate Unicode scalar safety: reject BOM, controls, lone surrogates, and unexpected joiners.

    Never silently strips ZWJ/ZWNJ. Normalizes NFC only after scalar safety checks pass.
    """
    if not text:
        return False, "EMPTY_TEXT_REJECTED", {}
    if SURROGATE_RE.search(text):
        return False, "LONE_SURROGATE_REJECTED", {}
    if BOM_CHAR in text:
        return False, "UNICODE_BOM_REJECTED", {"positions": [i for i, c in enumerate(text) if c == BOM_CHAR]}

    joiner_positions: list[dict[str, Any]] = []
    control_positions: list[dict[str, Any]] = []
    for idx, ch in enumerate(text):
        cp = ord(ch)
        if ch in JOINER_CHARS:
            joiner_positions.append({"pos": idx, "codepoint": f"U+{cp:04X}"})
        elif cp < 0x20 or (0x7F <= cp <= 0x9F) or cp in EXTRA_FORMAT_CONTROL_CPS:
            control_positions.append({"pos": idx, "codepoint": f"U+{cp:04X}"})

    if control_positions:
        return False, "UNICODE_CONTROL_OR_FORMAT_REJECTED", {"controls": control_positions}
    if joiner_positions:
        return False, "UNEXPECTED_JOINER_REJECTED", {"joiners": joiner_positions}

    was_nfc = unicodedata.is_normalized("NFC", text)
    normalized = text if was_nfc else unicodedata.normalize("NFC", text)
    return True, None, {"nfc_normalized": not was_nfc, "normalized_text": normalized}


def _extract_balanced_template(text: str, start: int) -> tuple[str, int] | None:
    """Return (inner_content, end_index_exclusive) for balanced ``{{...}}`` at ``start``."""
    if not text.startswith("{{", start):
        return None
    depth = 0
    i = start
    n = len(text)
    while i < n:
        if text.startswith("{{", i):
            depth += 1
            i += 2
        elif text.startswith("}}", i):
            depth -= 1
            i += 2
            if depth == 0:
                return text[start + 2 : i - 2], i
        else:
            i += 1
    return None


def _split_top_level_pipes(inner: str) -> list[str]:
    """Split template arguments on ``|`` outside nested ``{{...}}`` and ``[[...]]``."""
    parts: list[str] = []
    buf: list[str] = []
    brace_depth = 0
    bracket_depth = 0
    i = 0
    n = len(inner)
    while i < n:
        if inner.startswith("{{", i):
            brace_depth += 1
            buf.append("{{")
            i += 2
        elif inner.startswith("}}", i) and brace_depth > 0:
            brace_depth -= 1
            buf.append("}}")
            i += 2
        elif inner.startswith("[[", i):
            bracket_depth += 1
            buf.append("[[")
            i += 2
        elif inner.startswith("]]", i) and bracket_depth > 0:
            bracket_depth -= 1
            buf.append("]]")
            i += 2
        elif inner[i] == "|" and brace_depth == 0 and bracket_depth == 0:
            parts.append("".join(buf))
            buf.clear()
            i += 1
        else:
            buf.append(inner[i])
            i += 1
    parts.append("".join(buf))
    return parts


def _positional_and_named_args(parts: list[str]) -> tuple[str, list[str], dict[str, str]]:
    name = parts[0].strip()
    pos: list[str] = []
    named: dict[str, str] = {}
    for arg in parts[1:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            k_s = k.strip()
            if k_s.isidentifier() or k_s.isdigit():
                named[k_s] = v.strip()
                continue
        pos.append(arg.strip())
    return name, pos, named


def _map_label_token(token: str) -> dict[str, str | None] | None:
    """Map one raw {{lb}}/{{q}} token onto reviewed finite vocabulary dimensions only."""
    cleaned = token.strip()
    if "!" in cleaned:
        lbl_key, _, lbl_disp = cleaned.partition("!")
        cleaned = lbl_key.strip() or lbl_disp.strip()
    norm = re.sub(r"\s+", " ", cleaned.lower())
    if not norm or norm in DOMAIN_LABEL_IGNORE:
        return None
    if norm in REGION_LABEL_MAP:
        reg = REGION_LABEL_MAP[norm]
        return {
            "dimension": "region",
            "code": reg["code"],
            "parent_code": reg["parent"],
            "display_label": reg["display"],
            "raw_token": token.strip(),
        }
    if norm in REGISTER_LABEL_MAP:
        return {
            "dimension": "register",
            "code": REGISTER_LABEL_MAP[norm],
            "parent_code": None,
            "display_label": cleaned,
            "raw_token": token.strip(),
        }
    if norm in GRAMMAR_SYSTEM_LABEL_MAP:
        return {
            "dimension": "grammar_system",
            "code": GRAMMAR_SYSTEM_LABEL_MAP[norm],
            "parent_code": None,
            "display_label": cleaned,
            "raw_token": token.strip(),
        }
    if norm in TEMPORAL_LABEL_MAP:
        return {
            "dimension": "period",
            "code": TEMPORAL_LABEL_MAP[norm],
            "parent_code": None,
            "display_label": cleaned,
            "raw_token": token.strip(),
        }
    if norm in SOCIAL_USAGE_LABEL_MAP:
        return {
            "dimension": "social_usage",
            "code": SOCIAL_USAGE_LABEL_MAP[norm],
            "parent_code": None,
            "display_label": cleaned,
            "raw_token": token.strip(),
        }
    if norm in DOMAIN_LABEL_MAP:
        return {
            "dimension": "domain",
            "code": DOMAIN_LABEL_MAP[norm],
            "parent_code": None,
            "display_label": cleaned,
            "raw_token": token.strip(),
        }
    return None


def _unwrap_wikilinks(text: str) -> str:
    """Replace ``[[target|display]]`` -> ``display`` and ``[[target]]`` -> ``target``."""
    prev = None
    cur = text
    while prev != cur:
        prev = cur
        cur = WIKILINK_RE.sub(lambda m: (m.group(2) if m.group(2) is not None else m.group(1)), cur)
    return cur


def _classify_label_token(
    raw_tok: str,
    *,
    raw_template: str,
    allow_bang: bool,
    negated_region_context: bool,
) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
    """Resolve one cleaned qualifier token against finite registries without auto-inventing domains."""
    cleaned_tok = _unwrap_wikilinks(raw_tok).strip()
    if not cleaned_tok or cleaned_tok.lower() in DOMAIN_LABEL_IGNORE:
        return None, None, None
    lookup_tok = cleaned_tok
    visible_tok = cleaned_tok
    if allow_bang and "!" in cleaned_tok:
        lbl_key, _, lbl_disp = cleaned_tok.partition("!")
        lookup_tok = lbl_key.strip() or lbl_disp.strip()
        visible_tok = lbl_disp.strip() or lbl_key.strip()
    mapped = _map_label_token(lookup_tok)
    if mapped is not None:
        if negated_region_context and mapped["dimension"] == "region":
            return (
                visible_tok,
                None,
                {
                    "raw_token": cleaned_tok,
                    "display_token": visible_tok,
                    "raw_template": raw_template,
                    "status": "negated_or_conditional_region_skipped",
                },
            )
        return (
            visible_tok,
            {
                **mapped,
                "raw_token": cleaned_tok,
                "raw_template": raw_template,
            },
            None,
        )
    return (
        visible_tok,
        None,
        {
            "raw_token": cleaned_tok,
            "display_token": visible_tok,
            "raw_template": raw_template,
            "status": "unstructured_pending_review",
        },
    )


def _extract_headword_qualifiers(
    line: str,
    *,
    line_no: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract POS-scoped entry qualifiers from headword ``{{tlb|ta|...}}`` / ``{{lb|ta|...}}``."""
    mapped_entry: list[dict[str, Any]] = []
    unmapped_entry: list[dict[str, Any]] = []
    i = 0
    n = len(line)
    while i < n:
        if line.startswith("{{", i):
            extracted = _extract_balanced_template(line, i)
            if extracted is None:
                break
            inner, end_idx = extracted
            parts = _split_top_level_pipes(inner)
            tname, pos_args, _ = _positional_and_named_args(parts)
            tkey = tname.lower().replace("_", " ")
            if tkey in {"tlb", "lb", "label"} and len(pos_args) >= 2 and pos_args[0] == "ta":
                negated_region = False
                for raw_tok in pos_args[1:]:
                    if not raw_tok:
                        continue
                    if "{{" in raw_tok or "}}" in raw_tok:
                        unmapped_entry.append({
                            "raw_token": raw_tok.strip(),
                            "display_token": raw_tok.strip(),
                            "raw_template": f"{{{{{tname}|ta|{raw_tok}}}}}",
                            "status": "nested_template_pending_review",
                            "line_number": line_no,
                        })
                        continue
                    norm_tok = re.sub(r"\s+", " ", _unwrap_wikilinks(raw_tok).strip().lower())
                    if norm_tok in NEGATING_REGION_PREFIXES:
                        negated_region = True
                    _, mapped, unmapped = _classify_label_token(
                        raw_tok,
                        raw_template=f"{{{{{tname}|ta|{raw_tok}}}}}",
                        allow_bang=True,
                        negated_region_context=negated_region,
                    )
                    if mapped is not None:
                        mapped_entry.append({**mapped, "line_number": line_no})
                    if unmapped is not None:
                        unmapped_entry.append({**unmapped, "line_number": line_no})
            i = end_idx
        else:
            i += 1
    return mapped_entry, unmapped_entry


def _expand_safe_templates(text: str) -> tuple[bool, str, list[dict[str, Any]], list[dict[str, Any]], list[str], str, str | None]:
    """Conservatively unwrap allowlisted inline Wiktionary templates; fail closed on any unknown template."""
    out: list[str] = []
    qualifiers: list[dict[str, Any]] = []
    unmapped_qualifiers: list[dict[str, Any]] = []
    templates_used: list[str] = []
    component = "definition"
    i = 0
    n = len(text)

    while i < n:
        if text.startswith("{{", i):
            extracted = _extract_balanced_template(text, i)
            if extracted is None:
                return False, "", qualifiers, unmapped_qualifiers, templates_used, component, "UNBALANCED_TEMPLATE_REJECTED"
            inner, end_idx = extracted
            parts = _split_top_level_pipes(inner)
            tname, pos_args, named_args = _positional_and_named_args(parts)
            tkey = tname.lower().replace("_", " ")
            templates_used.append(tname)

            if tkey in {"ng", "non-gloss", "non-gloss definition", "n-g"}:
                if len(pos_args) != 1 or named_args:
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, f"UNSUPPORTED_TEMPLATE_ARGS:{tname}"
                ok, inner_exp, inner_quals, inner_unmapped, inner_tmpls, _, err = _expand_safe_templates(pos_args[0])
                if not ok:
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, err
                qualifiers.extend(inner_quals)
                unmapped_qualifiers.extend(inner_unmapped)
                templates_used.extend(inner_tmpls)
                component = "gloss"
                out.append(inner_exp)
            elif tkey in {"gloss", "gl"}:
                if not pos_args:
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, f"EMPTY_TEMPLATE_ARGS:{tname}"
                ok, inner_exp, inner_quals, inner_unmapped, inner_tmpls, _, err = _expand_safe_templates(", ".join(pos_args))
                if not ok:
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, err
                qualifiers.extend(inner_quals)
                unmapped_qualifiers.extend(inner_unmapped)
                templates_used.extend(inner_tmpls)
                out.append(f"({inner_exp})")
            elif tkey in {"q", "qualifier", "qual", "i"}:
                raw_tokens = [p for p in pos_args if p]
                if not raw_tokens:
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, f"EMPTY_QUALIFIER_TEMPLATE:{tname}"
                tok_labels: list[str] = []
                for raw_tok in raw_tokens:
                    if "{{" in raw_tok or "}}" in raw_tok:
                        return False, "", qualifiers, unmapped_qualifiers, templates_used, component, "NESTED_TEMPLATE_IN_QUALIFIER"
                    visible_tok, mapped, unmapped = _classify_label_token(
                        raw_tok,
                        raw_template=f"{{{{{tname}|{raw_tok}}}}}",
                        allow_bang=False,
                        negated_region_context=False,
                    )
                    if visible_tok is not None:
                        tok_labels.append(visible_tok)
                    if mapped is not None:
                        qualifiers.append(mapped)
                    if unmapped is not None:
                        unmapped_qualifiers.append(unmapped)
                if tok_labels:
                    out.append(f"({', '.join(tok_labels)})")
            elif tkey in {"lb", "label", "tlb"}:
                if len(pos_args) < 2 or pos_args[0] != "ta":
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, f"UNSUPPORTED_LB_LANG:{tname}"
                raw_tokens = [p for p in pos_args[1:] if p]
                visible_tokens: list[str] = []
                negated_region = False
                for raw_tok in raw_tokens:
                    if "{{" in raw_tok or "}}" in raw_tok:
                        return False, "", qualifiers, unmapped_qualifiers, templates_used, component, "NESTED_TEMPLATE_IN_LABEL"
                    norm_tok = re.sub(r"\s+", " ", _unwrap_wikilinks(raw_tok).strip().lower())
                    if norm_tok in NEGATING_REGION_PREFIXES:
                        negated_region = True
                    visible_tok, mapped, unmapped = _classify_label_token(
                        raw_tok,
                        raw_template=f"{{{{{tname}|ta|{raw_tok}}}}}",
                        allow_bang=True,
                        negated_region_context=negated_region,
                    )
                    if visible_tok is not None:
                        visible_tokens.append(visible_tok)
                    if mapped is not None:
                        qualifiers.append(mapped)
                    if unmapped is not None:
                        unmapped_qualifiers.append(unmapped)
                if visible_tokens:
                    out.append(f"({', '.join(visible_tokens)})")
            elif tkey == "tcl":
                if len(pos_args) < 2 or pos_args[0] != "ta" or not pos_args[1]:
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, "UNSUPPORTED_TCL_ARGS"
                gloss_arg = pos_args[1]
                if "{{" in gloss_arg or "}}" in gloss_arg:
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, "NESTED_TEMPLATE_IN_TCL"
                lb_param = named_args.get("lb", "")
                if lb_param:
                    lb_visible: list[str] = []
                    for raw_tok in lb_param.split(","):
                        visible_tok, mapped, unmapped = _classify_label_token(
                            raw_tok,
                            raw_template=f"{{{{tcl|...|lb={lb_param}}}}}",
                            allow_bang=True,
                            negated_region_context=False,
                        )
                        if visible_tok is not None:
                            lb_visible.append(visible_tok)
                        if mapped is not None:
                            qualifiers.append(mapped)
                        if unmapped is not None:
                            unmapped_qualifiers.append(unmapped)
                    if lb_visible:
                        out.append(f"({', '.join(lb_visible)}) ")
                out.append(gloss_arg)
            elif tkey == "defdate":
                if not pos_args:
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, "EMPTY_DEFDATE_TEMPLATE"
                if any("{{" in p or "}}" in p for p in pos_args):
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, "NESTED_TEMPLATE_IN_DEFDATE"
                out.append(f"[{pos_args[0]}]")
            elif tkey in {"vern", "w"}:
                # Safe English common name / Wikipedia article link display.
                disp = named_args.get("2") or (pos_args[1] if len(pos_args) > 1 and pos_args[1] else (pos_args[0] if pos_args else ""))
                if not disp or "{{" in disp or "}}" in disp:
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, f"UNSAFE_LINK_TEMPLATE:{tname}"
                out.append(disp)
            elif tkey in {"taxlink", "taxfmt"}:
                taxon = pos_args[0] if pos_args else ""
                if not taxon or "{{" in taxon or "}}" in taxon:
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, f"UNSAFE_TAXON_TEMPLATE:{tname}"
                out.append(taxon)
            elif tkey in {"l", "m"} and pos_args and pos_args[0] == "en":
                disp = named_args.get("t") or (pos_args[2] if len(pos_args) > 2 and pos_args[2] else (pos_args[1] if len(pos_args) > 1 else ""))
                if not disp or "{{" in disp or "}}" in disp:
                    return False, "", qualifiers, unmapped_qualifiers, templates_used, component, f"UNSAFE_EN_LINK_TEMPLATE:{tname}"
                out.append(disp)
            else:
                return False, "", qualifiers, unmapped_qualifiers, templates_used, component, f"UNEXPANDED_TEMPLATE_REJECTED:{tname}"
            i = end_idx
        else:
            out.append(text[i])
            i += 1

    return True, "".join(out), qualifiers, unmapped_qualifiers, templates_used, component, None


def clean_sense_line(raw_line: str) -> dict[str, Any]:
    """Parse and validate one ``# ...`` sense line fail-closed."""
    body = raw_line[2:].strip()
    if not body:
        return {"ok": False, "reason_code": "EMPTY_GLOSS_REJECTED", "raw_line": raw_line}

    for marker, reason in FORBIDDEN_SENSE_MARKERS:
        if marker in body:
            return {"ok": False, "reason_code": reason, "raw_line": raw_line}

    if HTML_COMMENT_RE.search(body) or HTML_TAG_RE.search(body) or "<!--" in body:
        return {"ok": False, "reason_code": "HTML_TAG_OR_COMMENT_REJECTED", "raw_line": raw_line}

    ok_tmpl, expanded, qualifiers, unmapped_qualifiers, templates_used, component, tmpl_err = _expand_safe_templates(body)
    if not ok_tmpl:
        return {"ok": False, "reason_code": tmpl_err or "UNEXPANDED_TEMPLATE_REJECTED", "raw_line": raw_line}

    # Unwrap wikilinks and strip wikitext bold/italic markers.
    unlinked = _unwrap_wikilinks(expanded)
    unlinked = BOLD_ITALIC_RE.sub("", unlinked)
    cleaned = re.sub(r"\s+", " ", unlinked).strip()

    if "{{" in cleaned or "}}" in cleaned:
        return {"ok": False, "reason_code": "RESIDUAL_TEMPLATE_BRACES_REJECTED", "raw_line": raw_line}
    if "[[" in cleaned or "]]" in cleaned:
        return {"ok": False, "reason_code": "RESIDUAL_WIKILINK_BRACKETS_REJECTED", "raw_line": raw_line}
    if HTML_TAG_RE.search(cleaned) or "<" in cleaned and ">" in cleaned:
        return {"ok": False, "reason_code": "RESIDUAL_HTML_REJECTED", "raw_line": raw_line}
    if not cleaned:
        return {"ok": False, "reason_code": "EMPTY_GLOSS_REJECTED", "raw_line": raw_line}
    if TAMIL_CHAR_RE.search(cleaned):
        return {"ok": False, "reason_code": "TAMIL_IN_ENGLISH_GLOSS_REJECTED", "raw_line": raw_line}

    u_ok, u_err, u_meta = check_unicode_scalar_integrity(cleaned)
    if not u_ok:
        return {"ok": False, "reason_code": f"SENSE_{u_err}", "raw_line": raw_line, "unicode_detail": u_meta}

    return {
        "ok": True,
        "component": component,
        "meaning_en": u_meta["normalized_text"],
        "nfc_normalized": u_meta["nfc_normalized"],
        "qualifiers": qualifiers,
        "unmapped_qualifiers": unmapped_qualifiers,
        "templates_used": templates_used,
    }


def _line_offsets(text: str) -> list[tuple[int, str, int, int, int, int]]:
    rows: list[tuple[int, str, int, int, int, int]] = []
    char_pos = 0
    byte_pos = 0
    for idx, line in enumerate(text.splitlines(keepends=False), start=1):
        char_end = char_pos + len(line)
        line_bytes = len(line.encode("utf-8"))
        byte_end = byte_pos + line_bytes
        rows.append((idx, line, char_pos, char_end, byte_pos, byte_end))
        nl = 1 if char_end < len(text) else 0
        char_pos = char_end + nl
        byte_pos = byte_end + nl
    return rows


def parse_wiktionary_page(page: dict[str, Any], *, check_native: bool = False) -> dict[str, Any]:
    """Parse a single en.wiktionary.org page independently with strict ==Tamil== and POS separation."""
    pageid = int(page["pageid"])
    revid = int(page["revid"])
    raw_title = str(page["title"])
    wikitext = str(page["wikitext"])
    categories = list(page.get("categories", []))

    exclusions: list[dict[str, Any]] = []
    extracted_entries: list[dict[str, Any]] = []
    pos_occurrence_counts: Counter[str] = Counter()

    u_ok, u_err, u_meta = check_unicode_scalar_integrity(raw_title)
    if not u_ok:
        exclusions.append({
            "pageid": pageid,
            "revid": revid,
            "title": raw_title,
            "reason_code": f"HEADWORD_{u_err}",
            "detail": u_meta,
        })
        return {"pageid": pageid, "revid": revid, "entries": [], "exclusions": exclusions}

    headword = u_meta["normalized_text"]
    if not TAMIL_CHAR_RE.search(headword):
        exclusions.append({
            "pageid": pageid,
            "revid": revid,
            "title": headword,
            "reason_code": "NON_TAMIL_HEADWORD_REJECTED",
        })
        return {"pageid": pageid, "revid": revid, "entries": [], "exclusions": exclusions}

    if check_native:
        inspected = native_inspect(headword)
        if not inspected.get("is_nfc"):
            exclusions.append({
                "pageid": pageid,
                "revid": revid,
                "title": headword,
                "reason_code": "HEADWORD_RUST_NON_NFC_REJECTED",
            })
            return {"pageid": pageid, "revid": revid, "entries": [], "exclusions": exclusions}

    in_tamil = False
    found_tamil_section = False
    current_pos: str | None = None
    in_pos = False
    current_entry: dict[str, Any] | None = None
    current_etymology_index = 0
    current_etymology_heading = ""

    for line_no, line, c_start, c_end, b_start, b_end in _line_offsets(wikitext):
        stripped = line.strip()
        if not stripped:
            continue

        lang_match = LANG_HEADER_RE.match(stripped)
        if lang_match:
            lang_name = lang_match.group(1).strip()
            in_tamil = lang_name == "Tamil"
            if in_tamil:
                found_tamil_section = True
            else:
                exclusions.append({
                    "pageid": pageid,
                    "revid": revid,
                    "line_number": line_no,
                    "reason_code": "NON_TAMIL_SECTION_EXCLUDED",
                    "heading": lang_name,
                })
            in_pos = False
            current_pos = None
            current_entry = None
            continue

        if not in_tamil:
            continue

        if stripped == "----":
            in_tamil = False
            in_pos = False
            current_pos = None
            current_entry = None
            continue

        sub_match = SUB_HEADER_RE.match(stripped)
        if sub_match:
            heading = sub_match.group(2).strip()
            # Normalize numbered Etymology headings like "Etymology 1".
            base_heading = re.sub(r"\s+\d+$", "", heading)
            if base_heading == "Etymology":
                current_etymology_index += 1
                current_etymology_heading = heading
            if heading in POS_HEADING_MAP:
                pos_code = POS_HEADING_MAP[heading]
                pos_occ_idx = pos_occurrence_counts[pos_code]
                pos_occurrence_counts[pos_code] += 1
                current_pos = pos_code
                in_pos = True
                current_entry = {
                    "pageid": pageid,
                    "revid": revid,
                    "revision_timestamp": page["revision_timestamp"],
                    "user": page.get("user", ""),
                    "sha1": page.get("sha1", ""),
                    "wikitext_sha256": page.get("wikitext_sha256", ""),
                    "permalink_url": page.get("permalink_url", ""),
                    "history_url": page.get("history_url", ""),
                    "categories": categories,
                    "headword": headword,
                    "headword_nfc_normalized": u_meta["nfc_normalized"],
                    "pos_code": pos_code,
                    "pos_heading": heading,
                    "pos_line": line_no,
                    "pos_lines": [line_no],
                    "etymology_index": current_etymology_index,
                    "etymology_heading": current_etymology_heading,
                    "pos_occurrence_index": pos_occ_idx,
                    "entry_qualifiers": [],
                    "unmapped_entry_qualifiers": [],
                    "senses": [],
                }
                extracted_entries.append(current_entry)
            else:
                in_pos = False
                current_pos = None
                current_entry = None
                reason = NON_DEFINITION_SECTIONS.get(base_heading, f"UNMAPPED_SUBSECTION_EXCLUDED:{base_heading}")
                exclusions.append({
                    "pageid": pageid,
                    "revid": revid,
                    "line_number": line_no,
                    "reason_code": reason,
                    "heading": heading,
                })
            continue

        if in_pos and current_entry is not None and line.startswith("# ") and not line.startswith("#:"):
            parsed_sense = clean_sense_line(line)
            if not parsed_sense["ok"]:
                exclusions.append({
                    "pageid": pageid,
                    "revid": revid,
                    "line_number": line_no,
                    "pos_code": current_pos,
                    "reason_code": parsed_sense["reason_code"],
                    "raw_line": line[:200],
                })
                continue
            ordinal = len(current_entry["senses"]) + 1
            current_entry["senses"].append({
                "ordinal": ordinal,
                "line_number": line_no,
                "char_range": [c_start, c_end],
                "byte_range": [b_start, b_end],
                "component": parsed_sense["component"],
                "meaning_en": parsed_sense["meaning_en"],
                "qualifiers": parsed_sense["qualifiers"],
                "unmapped_qualifiers": parsed_sense["unmapped_qualifiers"],
                "templates_used": parsed_sense["templates_used"],
            })
            continue

        # Capture POS-scoped headword qualifiers ({{tlb|ta|...}} / {{lb|ta|...}}) before exclusions.
        if (
            in_pos
            and current_entry is not None
            and not stripped.startswith(("#", "{{C|", "{{cln|", "[[Category:", "{{ta-IPA", "{{ta-decl", "{{ta-conj"))
            and "{{" in stripped
        ):
            mapped_eq, unmapped_eq = _extract_headword_qualifiers(stripped, line_no=line_no)
            if mapped_eq:
                current_entry["entry_qualifiers"].extend(mapped_eq)
            if unmapped_eq:
                current_entry["unmapped_entry_qualifiers"].extend(unmapped_eq)

        # Non-definition lines inside ==Tamil== (examples, quotations, headword templates, IPA, declensions).
        reason = "NON_DEFINITION_LINE_EXCLUDED"
        if "{{ta-IPA" in stripped or "Module:ta-IPA" in stripped:
            reason = "TEMPLATE_TA_IPA_EXCLUDED"
        elif stripped.startswith("#:"):
            reason = "USAGE_EXAMPLE_OR_SYNONYM_EXCLUDED"
        elif stripped.startswith("#*"):
            reason = "QUOTATION_LINE_EXCLUDED"
        elif stripped.startswith("##"):
            reason = "SUBSENSE_LINE_EXCLUDED"
        elif "{{ta-decl" in stripped:
            reason = "DECLENSION_TEMPLATE_EXCLUDED"
        elif "{{ta-conj" in stripped:
            reason = "CONJUGATION_TEMPLATE_EXCLUDED"
        elif stripped.startswith("{{C|") or stripped.startswith("{{cln|") or stripped.startswith("[[Category:"):
            reason = "CATEGORY_LINE_EXCLUDED"
        elif stripped.startswith("{{ta-"):
            reason = "HEADWORD_OR_TA_TEMPLATE_EXCLUDED"
        exclusions.append({
            "pageid": pageid,
            "revid": revid,
            "line_number": line_no,
            "reason_code": reason,
        })

    if not found_tamil_section:
        exclusions.append({
            "pageid": pageid,
            "revid": revid,
            "title": headword,
            "reason_code": "NO_TAMIL_SECTION_EXCLUDED",
        })
        return {"pageid": pageid, "revid": revid, "entries": [], "exclusions": exclusions}

    valid_entries: list[dict[str, Any]] = []
    for entry_obj in extracted_entries:
        pos_code = entry_obj["pos_code"]
        if not entry_obj["senses"]:
            exclusions.append({
                "pageid": pageid,
                "revid": revid,
                "title": headword,
                "pos_code": pos_code,
                "pos_occurrence_index": entry_obj["pos_occurrence_index"],
                "etymology_index": entry_obj["etymology_index"],
                "reason_code": "ENTRY_NO_VALID_SENSES_REMAINING",
            })
            continue
        # Deterministic entry identity scoped to (pageid, revid, pos_code, etymology_index, pos_occurrence_index).
        alloc_key = (
            f"enwiktionary:bulk:page:{pageid}:rev:{revid}:tam:{pos_code}"
            f":ety:{entry_obj['etymology_index']}:occ:{entry_obj['pos_occurrence_index']}"
        )
        entry_id = allocate_id("ent", BULK_NAMESPACE, alloc_key)
        pack_id, pack_reason = assign_pack(entry_obj)
        entry_obj["entry_id"] = entry_id
        entry_obj["pack_id"] = pack_id
        entry_obj["pack_reason"] = pack_reason
        valid_entries.append(entry_obj)

    return {"pageid": pageid, "revid": revid, "entries": valid_entries, "exclusions": exclusions}


def assign_pack(entry: dict[str, Any]) -> tuple[str, str]:
    """Deterministically partition a clean entry into ``names_taxa``, ``regional``, or ``core``.

    Routing relies exclusively on the entry's own POS, POS-scoped entry qualifiers, and its
    own sense qualifiers; page-wide categories (e.g. Category:Tamil dialectal terms) and
    other POS sections never re-route an unattested entry.
    """
    if entry["pos_code"] == "PROPN":
        return "names_taxa", "pos_propn"

    for qual in entry.get("entry_qualifiers", []):
        if qual.get("dimension") == "region" and qual.get("code") in TN_SL_REGIONAL_CODES:
            return "regional", f"entry_attested_region:{qual['code']}"

    for sense in entry["senses"]:
        for qual in sense.get("qualifiers", []):
            if qual.get("dimension") == "region" and qual.get("code") in TN_SL_REGIONAL_CODES:
                return "regional", f"attested_region:{qual['code']}"

    return "core", "standard_lemma_pos"


def run_bulk_dryrun(
    snapshot_dir: Path = BULK_SNAPSHOT_DIR,
    output_dir: Path = BULK_DRYRUN_DIR,
    report_path: Path = BULK_DRYRUN_REPORT,
    *,
    check_native: bool = False,
) -> dict[str, Any]:
    """Parse gzipped Wiktionary snapshot fail-closed and emit multi-pack dry-run candidates + report."""
    manifest_path = snapshot_dir / "snapshots_manifest.json"
    pages_gz_path = snapshot_dir / "pages.jsonl.gz"
    if not manifest_path.is_file() or not pages_gz_path.is_file():
        raise FileNotFoundError(f"Missing snapshot manifest or pages.jsonl.gz in {snapshot_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if digest(pages_gz_path) != manifest["pages_jsonl_gz_sha256"]:
        raise ValueError("Snapshot pages.jsonl.gz SHA-256 mismatch against snapshots_manifest.json")

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Load current canonical vocabularies.toml for compatibility reporting (read-only).
    canonical_vocab = {}
    if CANONICAL_VOCAB_PATH.is_file():
        import tomllib
        canonical_vocab = tomllib.loads(CANONICAL_VOCAB_PATH.read_text(encoding="utf-8"))
    canonical_pos_set = set(canonical_vocab.get("parts_of_speech", []))

    pack_entries: dict[str, list[dict[str, Any]]] = {"core": [], "names_taxa": [], "regional": []}
    exclusion_counts: Counter[str] = Counter()
    pos_counts: Counter[str] = Counter()
    region_counts: Counter[str] = Counter()
    register_counts: Counter[str] = Counter()
    temporal_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    social_usage_counts: Counter[str] = Counter()
    grammar_system_counts: Counter[str] = Counter()
    headword_to_pos: dict[str, set[str]] = defaultdict(set)
    nfc_normalized_headwords = 0

    pages_processed = 0
    pages_with_valid_entries = 0
    pages_with_zero_entries = 0

    with gzip.open(pages_gz_path, "rt", encoding="utf-8") as gz:
        for line in gz:
            if not line.strip():
                continue
            page = json.loads(line)
            pages_processed += 1
            parsed = parse_wiktionary_page(page, check_native=check_native)
            for exc in parsed["exclusions"]:
                exclusion_counts[exc["reason_code"]] += 1
            if parsed["entries"]:
                pages_with_valid_entries += 1
            else:
                pages_with_zero_entries += 1
            for entry in parsed["entries"]:
                if entry.get("headword_nfc_normalized"):
                    nfc_normalized_headwords += 1
                pack_entries[entry["pack_id"]].append(entry)
                pos_counts[entry["pos_code"]] += 1
                headword_to_pos[entry["headword"]].add(entry["pos_code"])
                for qual in entry.get("entry_qualifiers", []):
                    dim = qual["dimension"]
                    code = qual["code"]
                    if dim == "region":
                        region_counts[code] += 1
                    elif dim == "register":
                        register_counts[code] += 1
                    elif dim == "period":
                        temporal_counts[code] += 1
                    elif dim == "social_usage":
                        social_usage_counts[code] += 1
                    elif dim == "grammar_system":
                        grammar_system_counts[code] += 1
                    elif dim == "domain":
                        domain_counts[code] += 1
                for sense in entry["senses"]:
                    for qual in sense["qualifiers"]:
                        dim = qual["dimension"]
                        code = qual["code"]
                        if dim == "region":
                            region_counts[code] += 1
                        elif dim == "register":
                            register_counts[code] += 1
                        elif dim == "period":
                            temporal_counts[code] += 1
                        elif dim == "social_usage":
                            social_usage_counts[code] += 1
                        elif dim == "grammar_system":
                            grammar_system_counts[code] += 1
                        elif dim == "domain":
                            domain_counts[code] += 1

    pack_summaries: dict[str, dict[str, int]] = {}
    for pack_id, entries in pack_entries.items():
        entries.sort(
            key=lambda e: (
                e["headword"],
                e["pos_code"],
                e["pageid"],
                int(e.get("pos_occurrence_index") or 0),
                int(e.get("etymology_index") or 0),
                int(e.get("pos_line") or 0),
            )
        )
        sense_count = sum(len(e["senses"]) for e in entries)
        pack_summaries[pack_id] = {"entries": len(entries), "senses": sense_count}
        pack_file = output_dir / f"{pack_id}_candidates.jsonl.gz"
        with pack_file.open("wb") as raw_out:
            with gzip.GzipFile(filename=f"{pack_id}_candidates.jsonl", mode="wb", fileobj=raw_out, mtime=0) as gz:
                for entry in entries:
                    gz.write((json_text(entry) + "\n").encode("utf-8"))

    homograph_multi_pos = sum(1 for poses in headword_to_pos.values() if len(poses) > 1)
    total_entries = sum(v["entries"] for v in pack_summaries.values())
    total_senses = sum(v["senses"] for v in pack_summaries.values())
    unapproved_pos = sorted(pos for pos in pos_counts if pos not in canonical_pos_set)

    report = {
        "schema": "wiktionary-bulk-dryrun-report-v1",
        "snapshot_manifest_sha256": digest(manifest_path),
        "pages_jsonl_gz_sha256": manifest["pages_jsonl_gz_sha256"],
        "license": manifest["license"],
        "pages_processed": pages_processed,
        "pages_with_valid_entries": pages_with_valid_entries,
        "pages_with_zero_entries": pages_with_zero_entries,
        "total_clean_entries": total_entries,
        "total_clean_senses": total_senses,
        "multi_pos_homograph_headwords": homograph_multi_pos,
        "packs": pack_summaries,
        "pos_counts": dict(sorted(pos_counts.items())),
        "vocabularies_compatibility": {
            "canonical_parts_of_speech": sorted(canonical_pos_set),
            "bulk_pos_requiring_vocab_expansion_before_l3": unapproved_pos,
        },
        "scope_counts": {
            "region": dict(region_counts.most_common()),
            "register": dict(register_counts.most_common()),
            "period": dict(temporal_counts.most_common()),
            "social_usage": dict(social_usage_counts.most_common()),
            "grammar_system": dict(grammar_system_counts.most_common()),
            "top_domains": dict(domain_counts.most_common(25)),
        },
        "unicode_diagnostics": {
            "rust_native_checked": check_native,
            "nfc_normalized_headwords": nfc_normalized_headwords,
            "rejected_unexpected_joiners": sum(
                v for k, v in exclusion_counts.items() if "JOINER" in k
            ),
            "rejected_bom_controls": sum(
                v for k, v in exclusion_counts.items() if "BOM" in k or "CONTROL" in k
            ),
        },
        "top_exclusion_reasons": dict(exclusion_counts.most_common(30)),
        "total_exclusions_recorded": sum(exclusion_counts.values()),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


PACK_IDS_ORDERED: tuple[str, ...] = ("core", "names_taxa", "regional")
BULK_EXTRACTION_METHOD = "wiktionary-bulk-parser"
BULK_EXTRACTION_VERSION = "wiktionary-bulk-v1+utf8-v1"
BULK_METHOD_VERSION = "wiktionary-bulk-v1"
BULK_ALGORITHM_REF = "wiktionary-bulk-parser"
BULK_SNAPSHOT_DATE = "2026-11-15"
BULK_REUSE_BASIS = (
    "CC-BY-SA-4.0 (official en.wiktionary.org Tamil bulk snapshot 2026-11-15 rev; "
    "dual-licensed CC-BY-SA-4.0/GFDL upstream; attribution & ShareAlike required)"
)
_ISO_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def _validate_snapshot_date(snapshot_date: str) -> tuple[str, str]:
    """Validate an ISO YYYY-MM-DD snapshot date and return (iso_date, compact_yyyymmdd)."""
    if not isinstance(snapshot_date, str) or not _ISO_DATE_RE.fullmatch(snapshot_date):
        raise ValueError(f"Invalid snapshot_date {snapshot_date!r}: expected YYYY-MM-DD")
    try:
        datetime.strptime(snapshot_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid snapshot_date {snapshot_date!r}: {exc}") from exc
    return snapshot_date, snapshot_date.replace("-", "")


def _bulk_reuse_basis(snapshot_date: str) -> str:
    """Return the CC-BY-SA-4.0 / GFDL reuse basis string for a validated snapshot date."""
    return (
        f"CC-BY-SA-4.0 (official en.wiktionary.org Tamil bulk snapshot {snapshot_date} rev; "
        "dual-licensed CC-BY-SA-4.0/GFDL upstream; attribution & ShareAlike required)"
    )

SHARED_REGION_HIERARCHY: tuple[tuple[str, str | None, str], ...] = (
    ("TN", None, "Tamil Nadu"),
    ("CHENNAI", "TN", "Chennai Tamil"),
    ("KONGU", "TN", "Kongu Tamil"),
    ("MADURAI", "TN", "Madurai Tamil"),
    ("NELLAI", "TN", "Nellai Tamil"),
    ("KANYAKUMARI", "TN", "Kanyakumari Tamil"),
    ("PUDUKKOTTAI", "TN", "Pudukkottai Tamil"),
    ("THANJAVUR", "TN", "Thanjavur Tamil"),
    ("SL", None, "Sri Lanka"),
    ("JAFFNA", "SL", "Jaffna Tamil"),
    ("BATTICALOA", "SL", "Batticaloa Tamil"),
    ("VANNI", "SL", "Vanni Tamil"),
    ("UP_COUNTRY", "SL", "Up-Country Tamil"),
    ("TRINCOMALEE", "SL", "Trincomalee Tamil"),
    ("SG", None, "Singapore Tamil"),
    ("MY", None, "Malaysian Tamil"),
)

_SCOPE_PROP_BY_DIM: dict[str, str] = {
    "region": "region_scope",
    "register": "register_scope",
    "domain": "domain_scope",
    "period": "period_scope",
    "grammar_system": "grammar_system_scope",
    "social_usage": "social_usage_scope",
}


def _pack_namespace(pack_id: str) -> str:
    """Return deterministic UUIDv5 namespace string scoped to a pack."""
    return str(uuid.uuid5(uuid.UUID(BULK_NAMESPACE), f"pack:{pack_id}"))


def _sha256_json(payload: Any) -> str:
    return hashlib.sha256(json_text(payload).encode("ascii")).hexdigest()


def _extract_reviewed_poc_closure(reviewed_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], set[tuple[str, str]]]:
    """Load data/curation/wiktionary-core-reviewed/ read-only and compute (headword_nfc, pos) keys."""
    tables: dict[str, list[dict[str, Any]]] = {}
    for tbl in (
        "sources",
        "snapshots",
        "source_records",
        "identities",
        "entries",
        "forms",
        "senses",
        "texts",
        "relations",
        "assertions",
        "evidence",
        "decisions",
        "scopes",
        "labels",
        "unicode_exceptions",
        "pack_members",
        "findings",
    ):
        csv_path = reviewed_dir / f"{tbl}.csv"
        tables[tbl] = list(read_rows(csv_path, tbl)) if csv_path.is_file() else []

    ast_by_id = {row["assertion_id"]: row for row in tables["assertions"]}
    frm_by_id = {row["form_id"]: row for row in tables["forms"]}
    reviewed_keys: set[tuple[str, str]] = set()
    for ent in tables["entries"]:
        pos = ast_by_id[ent["pos_assertion_id"]]["value_json"]
        frm = frm_by_id[ent["canonical_form_id"]]
        hw = ast_by_id[frm["text_assertion_id"]]["value_json"]
        reviewed_keys.add((unicodedata.normalize("NFC", hw), pos))
    return tables, reviewed_keys


def _extract_markdown_attribution_table(notice_text: str) -> list[str]:
    """Extract Section 2 Markdown table lines from PoC notice verbatim without local paths/usernames."""
    lines = notice_text.replace("\r\n", "\n").splitlines()
    table_lines: list[str] = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("| Legacy `word_id`"):
            in_table = True
        if in_table:
            if stripped.startswith("|"):
                table_lines.append(line)
            elif table_lines:
                break
    return table_lines


def _build_pack_attribution_notice(
    pack_id: str,
    *,
    manifest: dict[str, Any],
    entry_count: int,
    sense_count: int,
    reviewed_notice_path: Path | None,
    snapshot_date: str = BULK_SNAPSHOT_DATE,
) -> str:
    """Build clean CC-BY-SA-4.0 notice markdown without local paths or usernames."""
    validated_date, _ = _validate_snapshot_date(snapshot_date)
    lines: list[str] = [
        f"# Attribution, License Notices, and Disclaimers (Wiktionary Bulk Pack: `{pack_id}`)",
        "",
        "> **Scope & Separation Notice:**",
        f"> `CC-BY-SA-4.0` applies **only to the Wiktionary source snapshots and lexical data** in this separate `{pack_id}` data pack.",
        "> It does **not** relicense the MIT-licensed Rust core crates or toolkit runtime engine.",
        "> This notice records engineering attribution and upstream license terms; it is not legal advice.",
        "",
        "## 1. Bulk Snapshot Provenance & Pack Closure",
        "",
        f"- **Pack ID:** `{pack_id}` (separate `CC-BY-SA-4.0` data pack)",
        f"- **Snapshot Date:** `{validated_date}` (`actor_type = automated`, method `{BULK_METHOD_VERSION}`)",
        f"- **Upstream Corpus:** English Wiktionary Tamil namespace (`{manifest.get('total_fetched_pages', manifest.get('total_indexed_pages', 0))}` pinned pages, compressed archive SHA-256 `{manifest.get('pages_jsonl_gz_sha256', '')}`)",
        f"- **Promoted Pack Coverage:** `{entry_count}` entries, `{sense_count}` senses",
        "- **Per-Page Provenance:** Exact upstream `pageid`, pinned `oldid` (`revid`), revision `timestamp`, page `title`, `wikitext_sha256`, `permalink`, and revision `history_url` are preserved in every `evidence.csv` `locator_json` row.",
        "- **Attribution & ShareAlike:** Upstream English Wiktionary pages remain under `CC-BY-SA-4.0` (with upstream historical GFDL notice per Wikimedia Terms of Use Section 7).",
        "",
    ]

    if pack_id == "core" and reviewed_notice_path is not None and reviewed_notice_path.is_file():
        poc_lines = _extract_markdown_attribution_table(
            reviewed_notice_path.read_text(encoding="utf-8")
        )
        lines.extend([
            "## 2. Preserved Human-Reviewed PoC Revisions & Contributor Attribution",
            "",
            "- Includes the 6 human-reviewed PoC entries (`actor_type = human`, `2026-11-14`, review packet SHA-256 `0b2168d07e9b45b5316994c1d97648ebf5de3ad666de050b10afbe5dfa58695b`) preserved verbatim alongside bulk entries.",
            "",
        ])
        if poc_lines:
            lines.extend(poc_lines)
            lines.append("")

    lines.extend([
        "## 3. Preserved Official Notice Files",
        "",
        "- `notices/CC-BY-SA-4.0.md`",
    ])
    return "\n".join(lines) + "\n"


def _build_bulk_pack_workspace(
    pack_id: str,
    candidates: list[tuple[str, dict[str, Any]]],
    *,
    manifest: dict[str, Any],
    workspace_dir: Path,
    legalcode_src: Path,
    reviewed_tables: dict[str, list[dict[str, Any]]] | None = None,
    reviewed_notice_path: Path | None = None,
    snapshot_date: str = BULK_SNAPSHOT_DATE,
) -> dict[str, Any]:
    """Deterministically materialize one curation workspace ready for `lexicon_packs.promote`."""
    validated_date, compact_date = _validate_snapshot_date(snapshot_date)
    if any(candidate.get("rendered_evidence") or candidate.get("source_kind") == "rendered_html" for _, candidate in candidates):
        raise ValueError("Rendered source proposals require a separately reviewed acceptance path")
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    notices_dir = workspace_dir / "notices"
    notices_dir.mkdir(parents=True, exist_ok=True)

    pack_ns = _pack_namespace(pack_id)
    gz_sha256 = manifest["pages_jsonl_gz_sha256"]
    snapshot_source_label = f"enwiktionary_ta_bulk_{compact_date}_{pack_id}"
    snapshot_source_id = allocate_id("src", pack_ns, snapshot_source_label)

    rows: dict[str, list[dict[str, Any]]] = {
        tbl: [] for tbl in (*CANONICAL_CSV_TABLES, "snapshots", "source_records", "findings")
    }
    used_pos: set[str] = set()
    used_langs: set[str] = {"tam", "eng"}
    used_dims: dict[str, set[str]] = {
        "register": set(),
        "domain": set(),
        "period": set(),
        "grammar_system": set(),
        "social_usage": set(),
        "region": set(),
    }

    reviewed_label_rows: dict[tuple[str, str], dict[str, Any]] = {}
    reviewed_entry_count = 0
    reviewed_sense_count = 0

    if reviewed_tables is not None:
        for tbl, tbl_rows in reviewed_tables.items():
            if tbl in rows:
                rows[tbl].extend(dict(r) for r in tbl_rows)
        reviewed_entry_count = len(reviewed_tables["entries"])
        reviewed_sense_count = len(reviewed_tables["senses"])
        ast_by_id = {r["assertion_id"]: r for r in reviewed_tables["assertions"]}
        for ent in reviewed_tables["entries"]:
            used_langs.add(ent["language_id"])
            used_pos.add(ast_by_id[ent["pos_assertion_id"]]["value_json"])
        for txt in reviewed_tables["texts"]:
            used_langs.add(txt["language_id"])
        for lbl in reviewed_tables["labels"]:
            reviewed_label_rows[(lbl["category"], lbl["code"])] = lbl

    snapshot_source_row = {
        "source_id": snapshot_source_id,
        "label_json": snapshot_source_label,
        "publication_json": "English Wiktionary (Wikimedia Foundation)",
        "url_json": "https://en.wiktionary.org/wiki/Category:Tamil_lemmas",
        "edition_json": f"bulk-snapshot-{validated_date};pack={pack_id};sha256={gz_sha256}",
        "locator_json": json_text({
            "snapshot_date": validated_date,
            "pack_id": pack_id,
            "pages_jsonl_gz_sha256": gz_sha256,
            "total_pages": manifest.get("total_fetched_pages", manifest.get("total_indexed_pages", 0)),
        }),
        "snapshot_id": None,
        "retrieval_date_state": "known",
        "retrieval_date_json": validated_date,
        "extraction_method": BULK_EXTRACTION_METHOD,
        "extraction_version": BULK_EXTRACTION_VERSION,
        "evidence_verification_state": "verified",
        "reuse_basis_json": _bulk_reuse_basis(validated_date),
        "reuse_state": "permitted",
        "attribution_text_json": (
            f"English Wiktionary contributors, official Tamil bulk snapshot ({validated_date}), "
            "CC BY-SA 4.0; exact pageid, pinned oldid, permalink, and revision history in per-claim evidence locators"
        ),
        "attribution_reference_json": "notices/ATTRIBUTION_AND_LICENSE.md",
    }
    rows["sources"].append(snapshot_source_row)

    label_registry: dict[tuple[str, str], dict[str, Any]] = {}
    region_meta = {code: (parent, display) for code, parent, display in SHARED_REGION_HIERARCHY}
    pos_occurrences: dict[tuple[str, str, str], int] = Counter()
    used_occ_indices: dict[tuple[str, str, str], set[int]] = defaultdict(set)

    def register_scope_label(dim: str, code: str, display_label: str, parent_code: str | None, scope_aid: str) -> None:
        if dim == "region" and code in region_meta:
            parent_code, display_label = region_meta[code]
        if (dim, code) not in label_registry:
            label_registry[(dim, code)] = {
                "registry_id": "enwiktionary-ta-qualifiers",
                "registry_version": "1",
                "code": code,
                "category": dim,
                "display_label_json": display_label,
                "definition_json": (
                    f"Official en.wiktionary Tamil {dim} qualifier '{code}' "
                    f"from pinned bulk snapshot ({validated_date})."
                ),
                "evidence_reference": scope_aid,
                "parent_code": parent_code,
            }
        if dim == "region" and parent_code and (dim, parent_code) not in label_registry:
            p_parent, p_disp = region_meta.get(parent_code, (None, parent_code))
            used_dims["region"].add(parent_code)
            label_registry[(dim, parent_code)] = {
                "registry_id": "enwiktionary-ta-qualifiers",
                "registry_version": "1",
                "code": parent_code,
                "category": "region",
                "display_label_json": p_disp,
                "definition_json": (
                    f"Region hierarchy node '{parent_code}' for Tamil lexical scopes "
                    f"({validated_date})."
                ),
                "evidence_reference": scope_aid,
                "parent_code": p_parent,
            }

    def add_verified_claim(
        key: str,
        *,
        subject_kind: str,
        subject_id: str,
        property_code: str,
        value_json: Any,
        locator_obj: dict[str, Any],
        extraction_sha256: str,
    ) -> tuple[str, str]:
        aid = allocate_id("ast", pack_ns, key)
        claim = {
            "assertion_id": aid,
            "subject_kind": subject_kind,
            "subject_id": subject_id,
            "property_code": property_code,
            "value_state": "known",
            "value_json": value_json,
            "origin": "verbatim_source",
            "source_fidelity_state": "verified",
            "ambiguity_state": "unambiguous",
            "algorithm_reference": BULK_ALGORITHM_REF,
            "convention_reference": None,
            "imported_status_json": None,
            "imported_confidence_json": None,
        }
        rev_sha = claim_revision(claim)
        claim["claim_revision_sha256"] = rev_sha
        rows["assertions"].append(claim)

        ev_row = {
            "assertion_id": aid,
            "source_id": snapshot_source_id,
            "source_record_id": None,
            "locator_json": json_text(locator_obj),
            "evidence_role": "supports",
            "extraction_version": BULK_EXTRACTION_VERSION,
            "extraction_sha256": extraction_sha256,
        }
        rows["evidence"].append(ev_row)

        ev_bundle_sha = evidence_hash([ev_row])
        did = allocate_id("dec", pack_ns, f"{key}:dec")
        rows["decisions"].append({
            "decision_id": did,
            "assertion_id": aid,
            "assertion_revision_sha256": rev_sha,
            "evidence_bundle_sha256": ev_bundle_sha,
            "outcome": "accepted_auto_source",
            "actor_type": "automated",
            "actor_id": None,
            "method_version": BULK_METHOD_VERSION,
            "decision_date": validated_date,
            "note_json": "",
            "predecessor_decision_id": None,
        })
        return aid, did

    bulk_entry_count = 0
    bulk_sense_count = 0

    for page_title, cand in candidates:
        pageid = int(cand["pageid"])
        revid = int(cand["revid"])
        pos_code = cand["pos_code"]
        hw = unicodedata.normalize("NFC", cand["headword"])
        used_pos.add(pos_code)

        occ_key = (str(pageid), str(revid), pos_code)
        source_occ_idx = cand.get("pos_occurrence_index")
        if (
            isinstance(source_occ_idx, int)
            and source_occ_idx >= 0
            and source_occ_idx not in used_occ_indices[occ_key]
        ):
            occ_idx = source_occ_idx
        else:
            occ_idx = pos_occurrences[occ_key]
            while occ_idx in used_occ_indices[occ_key]:
                occ_idx += 1
        used_occ_indices[occ_key].add(occ_idx)
        pos_occurrences[occ_key] = max(pos_occurrences[occ_key], occ_idx + 1)
        entry_alloc_key = f"enwiktionary:pack:{pack_id}:page:{pageid}:rev:{revid}:tam:{pos_code}:{occ_idx}"

        ent_id = allocate_id("ent", pack_ns, entry_alloc_key)
        frm_id = allocate_id("frm", pack_ns, f"{entry_alloc_key}:canonical-written")

        base_provenance = {
            "pageid": pageid,
            "revid": revid,
            "timestamp": cand["revision_timestamp"],
            "title": page_title,
            "wikitext_sha256": cand["wikitext_sha256"],
            "history_url": cand["history_url"],
            "permalink": cand["permalink_url"],
            "license": "CC-BY-SA-4.0",
        }
        hw_locator = dict(base_provenance, field="page.title")
        pos_locator = dict(
            base_provenance,
            field="pos_heading",
            raw_heading=cand["pos_heading"],
            mapped_pos=pos_code,
            pos_occurrence_index=occ_idx,
            pos_line=cand.get("pos_line") or (cand["pos_lines"][0] if cand.get("pos_lines") else None),
            etymology_index=cand.get("etymology_index"),
            etymology_heading=cand.get("etymology_heading"),
        )
        if cand.get("unmapped_entry_qualifiers"):
            pos_locator["unmapped_entry_qualifiers"] = cand["unmapped_entry_qualifiers"]

        pos_aid, _ = add_verified_claim(
            f"{entry_alloc_key}:pos",
            subject_kind="entry",
            subject_id=ent_id,
            property_code="part_of_speech",
            value_json=pos_code,
            locator_obj=pos_locator,
            extraction_sha256=_sha256_json([ent_id, "part_of_speech", pos_code, revid, occ_idx]),
        )

        # Emit entry-level attested scopes from POS-scoped headword {{tlb}}/{{lb}} templates.
        seen_entry_scopes: set[tuple[str, str]] = set()
        seen_entry_dims: set[str] = set()
        seen_entry_register = False
        for q in cand.get("entry_qualifiers", []):
            dim = q["dimension"]
            code = q["code"]
            if dim not in _SCOPE_PROP_BY_DIM:
                continue
            if dim == "register":
                if seen_entry_register:
                    continue
                seen_entry_register = True
            if (dim, code) in seen_entry_scopes:
                continue
            seen_entry_scopes.add((dim, code))
            seen_entry_dims.add(dim)
            used_dims[dim].add(code)

            parent_code = q.get("parent_code")
            display_label = q.get("display_label") or code
            if dim == "region" and code in region_meta:
                parent_code, display_label = region_meta[code]
            entry_scope_locator = dict(
                base_provenance,
                field="headword_line",
                line_number=q.get("line_number"),
                scope_dimension=dim,
                label_code=code,
                raw_template=q.get("raw_template", ""),
            )
            esc_aid, esc_did = add_verified_claim(
                f"{entry_alloc_key}:entry_scope:{dim}:{code}",
                subject_kind="entry",
                subject_id=ent_id,
                property_code=_SCOPE_PROP_BY_DIM[dim],
                value_json=code,
                locator_obj=entry_scope_locator,
                extraction_sha256=_sha256_json([ent_id, "entry", dim, code, revid]),
            )
            rows["scopes"].append({
                "subject_kind": "entry",
                "subject_id": ent_id,
                "dimension": dim,
                "state": "attested",
                "label_code": code,
                "supporting_assertion_id": esc_aid,
                "decision_id": esc_did,
            })
            register_scope_label(dim, code, display_label, parent_code, esc_aid)

        if cand.get("unmapped_entry_qualifiers"):
            if "domain" not in seen_entry_dims:
                rows["scopes"].append({
                    "subject_kind": "entry",
                    "subject_id": ent_id,
                    "dimension": "domain",
                    "state": "unknown",
                    "label_code": None,
                    "supporting_assertion_id": None,
                    "decision_id": None,
                })
            rows["findings"].append({
                "finding_id": allocate_id("fnd", pack_ns, f"{entry_alloc_key}:unmapped_entry_qual"),
                "record_id": None,
                "assertion_id": pos_aid,
                "issue_code": "UNMAPPED_ENTRY_QUALIFIER_REQUIRES_REVIEW",
                "severity": "warning",
                "scalar_positions": [],
                "status": "open",
                "resolution_reason_json": None,
            })
        hw_aid, _ = add_verified_claim(
            f"{entry_alloc_key}:hw",
            subject_kind="form",
            subject_id=frm_id,
            property_code="headword",
            value_json=hw,
            locator_obj=hw_locator,
            extraction_sha256=_sha256_json([frm_id, "headword", hw, revid]),
        )

        rows["identities"].append({
            "entity_id": ent_id,
            "kind": "entry",
            "allocation_key": entry_alloc_key,
            "lifecycle": "active",
            "identity_decision_id": None,
        })
        rows["identities"].append({
            "entity_id": frm_id,
            "kind": "form",
            "allocation_key": f"{entry_alloc_key}:canonical-written",
            "lifecycle": "active",
            "identity_decision_id": None,
        })
        rows["forms"].append({
            "form_id": frm_id,
            "entry_id": ent_id,
            "representation": "written",
            "role": "canonical",
            "text_assertion_id": hw_aid,
            "convention_assertion_id": None,
        })

        sense_claim_aids: list[str] = []
        for s_idx, sense in enumerate(cand["senses"], start=1):
            sense_alloc_key = f"{entry_alloc_key}:sense:{s_idx}"
            sen_id = allocate_id("sen", pack_ns, sense_alloc_key)
            txt_id = allocate_id("txt", pack_ns, f"{sense_alloc_key}:definition")
            comp = sense.get("component") or "definition"
            if comp not in ("definition", "gloss"):
                comp = "definition"
            meaning = unicodedata.normalize("NFC", sense["meaning_en"])

            sense_locator = dict(
                base_provenance,
                line_number=sense.get("line_number"),
                char_range=sense.get("char_range"),
                byte_range=sense.get("byte_range"),
                templates=sense.get("templates_used") or [],
            )
            if sense.get("unmapped_qualifiers"):
                sense_locator["unmapped_qualifiers"] = sense["unmapped_qualifiers"]
            def_aid, _ = add_verified_claim(
                f"{sense_alloc_key}:{comp}",
                subject_kind="text",
                subject_id=txt_id,
                property_code=comp,
                value_json=meaning,
                locator_obj=sense_locator,
                extraction_sha256=_sha256_json([txt_id, comp, meaning, revid, sense.get("line_number")]),
            )
            sense_claim_aids.append(def_aid)

            rows["identities"].append({
                "entity_id": sen_id,
                "kind": "sense",
                "allocation_key": sense_alloc_key,
                "lifecycle": "active",
                "identity_decision_id": None,
            })
            rows["identities"].append({
                "entity_id": txt_id,
                "kind": "text",
                "allocation_key": f"{sense_alloc_key}:definition",
                "lifecycle": "active",
                "identity_decision_id": None,
            })
            rows["senses"].append({
                "sense_id": sen_id,
                "entry_id": ent_id,
                "display_order": int(sense.get("ordinal") or s_idx),
                "parent_sense_id": None,
            })
            rows["texts"].append({
                "text_id": txt_id,
                "owner_kind": "sense",
                "owner_id": sen_id,
                "component": comp,
                "language_id": "eng",
                "text_assertion_id": def_aid,
                "paired_translation_id": None,
                "cited_source_locator_json": json_text(sense_locator),
            })

            seen_sense_scopes: set[tuple[str, str]] = set()
            seen_sense_dims: set[str] = set()
            seen_register = False
            for q in sense.get("qualifiers", []):
                dim = q["dimension"]
                code = q["code"]
                if dim not in _SCOPE_PROP_BY_DIM:
                    continue
                if dim == "register":
                    if seen_register:
                        continue
                    seen_register = True
                if (dim, code) in seen_sense_scopes:
                    continue
                seen_sense_scopes.add((dim, code))
                seen_sense_dims.add(dim)
                used_dims[dim].add(code)

                parent_code = q.get("parent_code")
                if dim == "region" and code in region_meta:
                    parent_code, display_label = region_meta[code]
                else:
                    display_label = q.get("display_label") or code

                scope_prop = _SCOPE_PROP_BY_DIM[dim]
                scope_locator = dict(
                    sense_locator,
                    scope_dimension=dim,
                    label_code=code,
                    raw_template=q.get("raw_template", ""),
                )
                scope_aid, scope_did = add_verified_claim(
                    f"{sense_alloc_key}:scope:{dim}:{code}",
                    subject_kind="sense",
                    subject_id=sen_id,
                    property_code=scope_prop,
                    value_json=code,
                    locator_obj=scope_locator,
                    extraction_sha256=_sha256_json([sen_id, dim, code, revid]),
                )
                rows["scopes"].append({
                    "subject_kind": "sense",
                    "subject_id": sen_id,
                    "dimension": dim,
                    "state": "attested",
                    "label_code": code,
                    "supporting_assertion_id": scope_aid,
                    "decision_id": scope_did,
                })
                register_scope_label(dim, code, display_label, parent_code, scope_aid)
            if sense.get("unmapped_qualifiers"):
                if "domain" not in seen_sense_dims:
                    rows["scopes"].append({
                        "subject_kind": "sense",
                        "subject_id": sen_id,
                        "dimension": "domain",
                        "state": "unknown",
                        "label_code": None,
                        "supporting_assertion_id": None,
                        "decision_id": None,
                    })
                rows["findings"].append({
                    "finding_id": allocate_id("fnd", pack_ns, f"{sense_alloc_key}:unmapped_qual"),
                    "record_id": None,
                    "assertion_id": def_aid,
                    "issue_code": "UNMAPPED_QUALIFIER_REQUIRES_REVIEW",
                    "severity": "warning",
                    "scalar_positions": [],
                    "status": "open",
                    "resolution_reason_json": None,
                })
            bulk_sense_count += 1

        entry_rev = _sha256_json([ent_id, frm_id, hw_aid, pos_aid, sense_claim_aids])
        rows["entries"].append({
            "entry_id": ent_id,
            "language_id": "tam",
            "variety_id": None,
            "canonical_form_id": frm_id,
            "pos_assertion_id": pos_aid,
            "structural_kind": "wiktionary_bulk",
            "revision": entry_rev,
        })
        rows["pack_members"].append({
            "pack_id": pack_id,
            "entry_id": ent_id,
            "included_revision": entry_rev,
            "relation_inclusion_policy": "omit_cross_pack",
        })
        bulk_entry_count += 1

    # Merge labels cleanly: bulk attested labels override reviewed unattested PoC labels on conflict.
    if reviewed_label_rows:
        kept_reviewed_labels = [
            lbl for key, lbl in reviewed_label_rows.items() if key not in label_registry
        ]
        rows["labels"] = kept_reviewed_labels + [label_registry[k] for k in sorted(label_registry)]
    else:
        rows["labels"] = [label_registry[k] for k in sorted(label_registry)]

    # Deterministic table ordering before writing CSVs.
    write_rows(workspace_dir / "sources.csv", "sources", sorted(rows["sources"], key=lambda r: r["source_id"]))
    write_rows(workspace_dir / "snapshots.csv", "snapshots", rows["snapshots"])
    write_rows(workspace_dir / "source_records.csv", "source_records", rows["source_records"])
    write_rows(workspace_dir / "identities.csv", "identities", sorted(rows["identities"], key=lambda r: r["entity_id"]))
    write_rows(workspace_dir / "entries.csv", "entries", sorted(rows["entries"], key=lambda r: r["entry_id"]))
    write_rows(workspace_dir / "forms.csv", "forms", sorted(rows["forms"], key=lambda r: r["form_id"]))
    write_rows(workspace_dir / "senses.csv", "senses", sorted(rows["senses"], key=lambda r: (r["entry_id"], r["display_order"], r["sense_id"])))
    write_rows(workspace_dir / "texts.csv", "texts", sorted(rows["texts"], key=lambda r: r["text_id"]))
    write_rows(workspace_dir / "relations.csv", "relations", rows["relations"])
    write_rows(workspace_dir / "assertions.csv", "assertions", sorted(rows["assertions"], key=lambda r: r["assertion_id"]))
    write_rows(workspace_dir / "evidence.csv", "evidence", sorted(rows["evidence"], key=lambda r: (r["assertion_id"], r["source_id"], r["locator_json"])))
    write_rows(workspace_dir / "decisions.csv", "decisions", sorted(rows["decisions"], key=lambda r: r["decision_id"]))
    write_rows(workspace_dir / "scopes.csv", "scopes", sorted(rows["scopes"], key=lambda r: (r["subject_kind"], r["subject_id"], r["dimension"], r["state"], r["label_code"] or "")))
    write_rows(workspace_dir / "labels.csv", "labels", sorted(rows["labels"], key=lambda r: (r["registry_id"], r["registry_version"], r["category"], r["code"])))
    write_rows(workspace_dir / "unicode_exceptions.csv", "unicode_exceptions", rows["unicode_exceptions"])
    write_rows(workspace_dir / "pack_members.csv", "pack_members", sorted(rows["pack_members"], key=lambda r: (r["pack_id"], r["entry_id"])))
    write_rows(workspace_dir / "findings.csv", "findings", rows["findings"])

    # Identical conflict-free region hierarchy across all 3 packs in vocabularies.toml.
    vocab = {
        "schema_version": 1,
        "vocabulary_version": "1",
        "language_ids": sorted(used_langs),
        "parts_of_speech": sorted(used_pos),
        "relation_codes": [],
        "annotation_properties": [],
        "registers": sorted(used_dims["register"]),
        "domains": sorted(used_dims["domain"]),
        "temporals": sorted(used_dims["period"]),
        "varieties": [],
        "regions": [
            ({"code": code, "parent_code": parent} if parent else {"code": code})
            for code, parent, _ in sorted(SHARED_REGION_HIERARCHY, key=lambda x: x[0])
        ],
    }
    (workspace_dir / "vocabularies.toml").write_text(
        _render_vocabularies_toml(vocab),
        encoding="utf-8",
        newline="\n",
    )

    shutil.copy2(legalcode_src, notices_dir / "cc_by_sa_4_0_legalcode.txt")
    notice_md = _build_pack_attribution_notice(
        pack_id,
        manifest=manifest,
        entry_count=reviewed_entry_count + bulk_entry_count,
        sense_count=reviewed_sense_count + bulk_sense_count,
        reviewed_notice_path=reviewed_notice_path,
        snapshot_date=validated_date,
    )
    (notices_dir / "ATTRIBUTION_AND_LICENSE.md").write_text(
        notice_md,
        encoding="utf-8",
        newline="\n",
    )
    return {
        "pack_id": pack_id,
        "workspace_dir": str(workspace_dir),
        "reviewed_entries": reviewed_entry_count,
        "bulk_entries": bulk_entry_count,
        "total_entries": reviewed_entry_count + bulk_entry_count,
        "reviewed_senses": reviewed_sense_count,
        "bulk_senses": bulk_sense_count,
        "total_senses": reviewed_sense_count + bulk_sense_count,
    }


def promote_bulk_packs(
    snapshot_dir: Path = BULK_SNAPSHOT_DIR,
    *,
    packs: tuple[str, ...] = PACK_IDS_ORDERED,
    curation_root: Path = ROOT / "data/curation",
    reviewed_dir: Path = ROOT / "data/curation/wiktionary-core-reviewed",
    output_dirs: dict[str, Path] | None = None,
    check_native: bool = False,
    snapshot_date: str = BULK_SNAPSHOT_DATE,
) -> dict[str, Any]:
    """Build deterministic auto-curation workspaces and promote/validate multi-pack Wiktionary data."""
    validated_date, _ = _validate_snapshot_date(snapshot_date)
    manifest_path = snapshot_dir / "snapshots_manifest.json"
    pages_gz = snapshot_dir / "pages.jsonl.gz"
    if not manifest_path.is_file() or not pages_gz.is_file():
        raise FileNotFoundError(
            f"Missing pinned bulk snapshot artifacts in {snapshot_dir}; expected snapshots_manifest.json and pages.jsonl.gz"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual_sha = digest(pages_gz)
    if actual_sha != manifest["pages_jsonl_gz_sha256"]:
        raise ValueError(
            f"Snapshot SHA-256 mismatch for {pages_gz}: expected {manifest['pages_jsonl_gz_sha256']}, got {actual_sha}"
        )

    legalcode_src = reviewed_dir / "notices/cc_by_sa_4_0_legalcode.txt"
    if not legalcode_src.is_file():
        raise FileNotFoundError(f"Canonical CC-BY-SA-4.0 legal text missing: {legalcode_src}")

    reviewed_tables, reviewed_keys = _extract_reviewed_poc_closure(reviewed_dir)
    reviewed_notice_path = reviewed_dir / "notices/ATTRIBUTION_AND_LICENSE.md"

    candidates_by_pack: dict[str, list[tuple[str, dict[str, Any]]]] = {p: [] for p in PACK_IDS_ORDERED}
    skipped_core_duplicates: list[tuple[str, str]] = []

    pages: list[dict[str, Any]] = []
    with gzip.open(pages_gz, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                pages.append(json.loads(line))
    pages.sort(key=lambda pg: (unicodedata.normalize("NFC", pg["title"]), int(pg["pageid"])))

    for page in pages:
        parsed = parse_wiktionary_page(page, check_native=check_native)
        title_nfc = unicodedata.normalize("NFC", page["title"])
        for ent in parsed["entries"]:
            pack_id = ent.get("pack_id") or "core"
            if pack_id == "core":
                hw_nfc = unicodedata.normalize("NFC", ent["headword"])
                if (hw_nfc, ent["pos_code"]) in reviewed_keys and int(ent.get("pos_occurrence_index") or 0) == 0:
                    skipped_core_duplicates.append((hw_nfc, ent["pos_code"]))
                    continue
            if pack_id in candidates_by_pack:
                candidates_by_pack[pack_id].append((title_nfc, ent))

    resolved_outputs = output_dirs or {
        "core": ROOT / "lexicon/dictionary",
        "names_taxa": ROOT / "lexicon/packs/names_taxa",
        "regional": ROOT / "lexicon/packs/regional",
    }

    pack_results: dict[str, Any] = {}
    for pack_id in packs:
        if pack_id not in PACK_IDS_ORDERED:
            raise ValueError(f"Unsupported pack id: {pack_id!r}")
        ws_dir = curation_root / f"wiktionary-{pack_id}-auto"
        ws_summary = _build_bulk_pack_workspace(
            pack_id,
            candidates_by_pack[pack_id],
            manifest=manifest,
            workspace_dir=ws_dir,
            legalcode_src=legalcode_src,
            reviewed_tables=reviewed_tables if pack_id == "core" else None,
            reviewed_notice_path=reviewed_notice_path if pack_id == "core" else None,
            snapshot_date=validated_date,
        )

        target_out = resolved_outputs[pack_id]
        target_out.parent.mkdir(parents=True, exist_ok=True)
        stage_out = target_out.parent / f".staging-{pack_id}"
        if stage_out.exists():
            shutil.rmtree(stage_out)
        try:
            promote_report = promote_pack(ws_dir, pack=pack_id, output=stage_out)
            if not promote_report.get("l3_pack_eligible"):
                raise RuntimeError(f"Promotion produced ineligible pack for {pack_id}: {promote_report}")
            if target_out.exists():
                shutil.rmtree(target_out)
            shutil.move(str(stage_out), str(target_out))
        finally:
            if stage_out.exists():
                shutil.rmtree(stage_out, ignore_errors=True)

        final_errors = validate_canonical_dir(target_out)
        if final_errors:
            raise RuntimeError(f"Final canonical validation failed for {pack_id}: {final_errors}")

        pack_results[pack_id] = {
            **ws_summary,
            "canonical_dir": str(target_out),
            "dataset_version": promote_report["dataset_version"],
            "manifest_sha256": promote_report["manifest_sha256"],
            "promoted_entries": promote_report["entry_count"],
            "promoted_senses": promote_report["sense_count"],
            "promoted_sources": sum(1 for _ in read_rows(target_out / "sources.csv")),
            "validation_errors": final_errors,
        }

    return {
        "schema_version": 1,
        "snapshot_date": validated_date,
        "pages_jsonl_gz_sha256": actual_sha,
        "reviewed_poc_keys_preserved": sorted(f"{hw}:{pos}" for hw, pos in reviewed_keys),
        "skipped_core_duplicates": sorted(f"{hw}:{pos}" for hw, pos in skipped_core_duplicates),
        "packs": pack_results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_idx = sub.add_parser("fetch-index")
    p_idx.add_argument("--snapshot-dir", type=Path, default=BULK_SNAPSHOT_DIR)

    p_pg = sub.add_parser("fetch-pages")
    p_pg.add_argument("--snapshot-dir", type=Path, default=BULK_SNAPSHOT_DIR)
    p_pg.add_argument("--batch-size", type=int, default=50)
    p_pg.add_argument("--workers", type=int, default=8)
    p_pg.add_argument("--time-budget", type=float, default=7.0)

    p_fin = sub.add_parser("finalize")
    p_fin.add_argument("--snapshot-dir", type=Path, default=BULK_SNAPSHOT_DIR)
    p_fin.add_argument("--keep-staging", action="store_true")

    p_dry = sub.add_parser("dryrun")
    p_dry.add_argument("--snapshot-dir", type=Path, default=BULK_SNAPSHOT_DIR)
    p_dry.add_argument("--output-dir", type=Path, default=BULK_DRYRUN_DIR)
    p_dry.add_argument("--report", type=Path, default=BULK_DRYRUN_REPORT)
    p_dry.add_argument("--check-native", action="store_true")

    p_prom = sub.add_parser("promote")
    p_prom.add_argument("--snapshot-dir", type=Path, default=BULK_SNAPSHOT_DIR)
    p_prom.add_argument("--curation-root", type=Path, default=ROOT / "data/curation")
    p_prom.add_argument("--reviewed-dir", type=Path, default=ROOT / "data/curation/wiktionary-core-reviewed")
    p_prom.add_argument("--core-output", type=Path, default=ROOT / "lexicon/dictionary")
    p_prom.add_argument("--packs-output-root", type=Path, default=ROOT / "lexicon/packs")
    p_prom.add_argument("--all", action="store_true")
    p_prom.add_argument("--pack", action="append", choices=list(PACK_IDS_ORDERED))
    p_prom.add_argument("--check-native", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "fetch-index":
        res = fetch_index(args.snapshot_dir)
    elif args.command == "fetch-pages":
        res = fetch_pages_resumable(
            args.snapshot_dir,
            batch_size=args.batch_size,
            max_workers=args.workers,
            time_budget_s=args.time_budget,
        )
    elif args.command == "finalize":
        res = finalize_snapshot(args.snapshot_dir, keep_staging=args.keep_staging)
    elif args.command == "dryrun":
        res = run_bulk_dryrun(
            args.snapshot_dir,
            args.output_dir,
            args.report,
            check_native=args.check_native,
        )
    elif args.command == "promote":
        selected_packs = PACK_IDS_ORDERED if (args.all or not args.pack) else tuple(dict.fromkeys(args.pack))
        outputs = {
            "core": args.core_output,
            "names_taxa": args.packs_output_root / "names_taxa",
            "regional": args.packs_output_root / "regional",
        }
        res = promote_bulk_packs(
            args.snapshot_dir,
            packs=selected_packs,
            curation_root=args.curation_root,
            reviewed_dir=args.reviewed_dir,
            output_dirs=outputs,
            check_native=args.check_native,
        )
    else:
        raise ValueError(f"Unknown command: {args.command}")
    print(json.dumps(res, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
