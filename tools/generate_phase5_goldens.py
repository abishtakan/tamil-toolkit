import json
import subprocess
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORACLE_EXE = os.path.join(ROOT, "target", "debug", "tamil-oracle.exe")


def run_oracle(requests):
    p = subprocess.Popen(
        [ORACLE_EXE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    input_data = "\n".join(json.dumps(r) for r in requests) + "\n"
    stdout, stderr = p.communicate(input=input_data)
    if p.returncode != 0:
        raise RuntimeError(f"oracle failed: {stderr}")
    return [json.loads(line) for line in stdout.strip().split("\n") if line.strip()]

def generate_folded_search_suite():
    raw_cases = [
        # Mayangoli lateral
        ("collate_folded_001", "folded_search_key", {"text": "பழம்", "profile": "mayangoli"}, ["collate", "folded", "mayangoli"], "Mayangoli zha to la folded search key"),
        ("collate_folded_002", "folded_search_key", {"text": "பலம்", "profile": "mayangoli"}, ["collate", "folded", "mayangoli"], "Mayangoli alveolar la folded search key"),
        ("collate_folded_003", "folded_search_key", {"text": "பளம்", "profile": "mayangoli"}, ["collate", "folded", "mayangoli"], "Mayangoli retroflex la folded search key"),
        # Mayangoli nasal
        ("collate_folded_004", "folded_search_key", {"text": "மணம்", "profile": "mayangoli"}, ["collate", "folded", "mayangoli"], "Mayangoli retroflex na folded search key"),
        ("collate_folded_005", "folded_search_key", {"text": "மனம்", "profile": "mayangoli"}, ["collate", "folded", "mayangoli"], "Mayangoli alveolar na folded search key"),
        # Mayangoli rhotic
        ("collate_folded_006", "folded_search_key", {"text": "கறி", "profile": "mayangoli"}, ["collate", "folded", "mayangoli"], "Mayangoli hard ra folded search key"),
        ("collate_folded_007", "folded_search_key", {"text": "கரி", "profile": "mayangoli"}, ["collate", "folded", "mayangoli"], "Mayangoli medial ra folded search key"),
        # Mayangoli geminate lateral
        ("collate_folded_008", "folded_search_key", {"text": "வெள்ளம்", "profile": "mayangoli"}, ["collate", "folded", "mayangoli"], "Mayangoli geminate retroflex la folded key"),
        ("collate_folded_009", "folded_search_key", {"text": "வெல்லம்", "profile": "mayangoli"}, ["collate", "folded", "mayangoli"], "Mayangoli geminate alveolar la folded key"),
        # Grantha
        ("collate_folded_010", "folded_search_key", {"text": "சந்தோஷம்", "profile": "grantha"}, ["collate", "folded", "grantha"], "Grantha sha to cha folded search key"),
        ("collate_folded_011", "folded_search_key", {"text": "சந்தோசம்", "profile": "grantha"}, ["collate", "folded", "grantha"], "Native cha folded search key"),
        ("collate_folded_012", "folded_search_key", {"text": "ஜனம்", "profile": "grantha"}, ["collate", "folded", "grantha"], "Grantha ja to cha folded search key"),
        ("collate_folded_013", "folded_search_key", {"text": "சனம்", "profile": "grantha"}, ["collate", "folded", "grantha"], "Native cha folded search key"),
        ("collate_folded_014", "folded_search_key", {"text": "ஹரி", "profile": "grantha"}, ["collate", "folded", "grantha"], "Grantha ha to ka folded search key"),
        ("collate_folded_015", "folded_search_key", {"text": "கரி", "profile": "grantha"}, ["collate", "folded", "grantha"], "Native ka folded search key"),
        ("collate_folded_016", "folded_search_key", {"text": "மோக்ஷம்", "profile": "grantha"}, ["collate", "folded", "grantha"], "Grantha ksha to cha folded search key"),
        ("collate_folded_017", "folded_search_key", {"text": "மோசம்", "profile": "grantha"}, ["collate", "folded", "grantha"], "Native cha folded search key"),
        # Comprehensive
        ("collate_folded_018", "folded_search_key", {"text": "ஸ்ரீலங்கா", "profile": "comprehensive"}, ["collate", "folded", "comprehensive"], "Comprehensive folded search key for srilanka"),
        ("collate_folded_019", "folded_search_key", {"text": "சீலங்கா", "profile": "comprehensive"}, ["collate", "folded", "comprehensive"], "Comprehensive folded search key for seelanka"),
    ]

    requests = [{"op": op, "input": inp} for _, op, inp, _, _ in raw_cases]
    outputs = run_oracle(requests)

    lines = []
    for (cid, op, inp, tags, src), out in zip(raw_cases, outputs):
        vector = {
            "id": cid,
            "op": op,
            "input": inp,
            "expected": out,
            "dialect": "COMMON",
            "tags": tags,
            "source": src
        }
        lines.append(json.dumps(vector, ensure_ascii=True))

    out_path = os.path.join(ROOT, "tests", "golden", "collate_folded_search.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {len(lines)} vectors to {out_path}")

def generate_uyirmei_first_suite():
    raw_cases = [
        # Syllable before Mei comparisons
        ("collate_uf_001", "compare", {"left": "கப்பல்", "right": "க்ளப்", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "consonant_k"], "Ka syllable before K consonant in uyirmei-first"),
        ("collate_uf_002", "compare", {"left": "க்ளப்", "right": "கப்பல்", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "consonant_k"], "K consonant after Ka syllable in uyirmei-first"),
        ("collate_uf_003", "compare", {"left": "சக்கரம்", "right": "ச்லோகம்", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "consonant_c"], "Ca syllable before C consonant in uyirmei-first"),
        ("collate_uf_004", "compare", {"left": "தட்டு", "right": "த்ராவிடம்", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "consonant_t"], "Ta syllable before T consonant in uyirmei-first"),
        ("collate_uf_005", "compare", {"left": "படம்", "right": "ப்ளூ", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "consonant_p"], "Pa syllable before P consonant in uyirmei-first"),
        ("collate_uf_006", "compare", {"left": "மரம்", "right": "ம்ரூக", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "consonant_m"], "Ma syllable before M consonant in uyirmei-first"),
        # Consonant row progression
        ("collate_uf_007", "compare", {"left": "க", "right": "கா", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "row_order"], "Ka before Kaa in uyirmei-first"),
        ("collate_uf_008", "compare", {"left": "கா", "right": "கி", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "row_order"], "Kaa before Ki in uyirmei-first"),
        ("collate_uf_009", "compare", {"left": "கௌ", "right": "க்", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "row_order"], "Kau before K-mei in uyirmei-first"),
        # Single element keys
        ("collate_uf_010", "sort_key", {"text": "அ", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "sort_key"], "Independent vowel A sort key in uyirmei-first"),
        ("collate_uf_011", "sort_key", {"text": "க", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "sort_key"], "Syllable Ka sort key in uyirmei-first (rank 14)"),
        ("collate_uf_012", "sort_key", {"text": "கா", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "sort_key"], "Syllable Kaa sort key in uyirmei-first (rank 15)"),
        ("collate_uf_013", "sort_key", {"text": "கௌ", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "sort_key"], "Syllable Kau sort key in uyirmei-first (rank 25)"),
        ("collate_uf_014", "sort_key", {"text": "க்", "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "sort_key"], "Muted consonant K sort key in uyirmei-first (rank 26)"),
        # Word sorting
        ("collate_uf_015", "sort_words", {"words": ["க்ளப்", "காகம்", "கப்பல்"], "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "sort_words"], "Stable sorting of K words in uyirmei-first"),
        ("collate_uf_016", "sort_words", {"words": ["ச்லோகம்", "சாவி", "சக்கரம்"], "profile": "uyirmei-first-v1"}, ["collate", "uyirmei_first", "sort_words"], "Stable sorting of C words in uyirmei-first"),
    ]

    requests = [{"op": op, "input": inp} for _, op, inp, _, _ in raw_cases]
    outputs = run_oracle(requests)

    lines = []
    for (cid, op, inp, tags, src), out in zip(raw_cases, outputs):
        vector = {
            "id": cid,
            "op": op,
            "input": inp,
            "expected": out,
            "dialect": "COMMON",
            "tags": tags,
            "source": src
        }
        lines.append(json.dumps(vector, ensure_ascii=True))

    out_path = os.path.join(ROOT, "tests", "golden", "collate_uyirmei_first.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {len(lines)} vectors to {out_path}")

def main():
    generate_folded_search_suite()
    generate_uyirmei_first_suite()

if __name__ == "__main__":
    main()
