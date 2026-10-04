import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402

COMBINED = ROOT / "output" / "en_IN.combined"

HEADER_RE = re.compile(
    r"^dictionary=main:en_in,locale=en_IN,description=[^,]+,date=\d+,version=\d+$"
)
WORD_RE = re.compile(r"^ word=[^,\s]+,f=(\d+)(,possibly_offensive=true)?$")
BIGRAM_RE = re.compile(r"^  bigram=[^,\s]+,f=(\d+)$")


@pytest.fixture(scope="module")
def d():
    return build.build()


@pytest.fixture(scope="module")
def e(d):
    return d.entries


def f(entries, word):
    return entries[word].f


def test_exact_sizes(d, e):
    assert len(e) == build.UNIGRAM_LIMIT == 150_000
    assert sum(len(x.bigrams) for x in e.values()) == build.BIGRAM_LIMIT == 400_000


def test_whole_number_frequencies():
    for name, cols in (("unigrams.tsv", [1]), ("contractions.tsv", [1]),
                       ("bigrams.tsv", [2, 3]), ("trigrams.tsv.gz", [3, 4])):
        for i, row in enumerate(build.read_generated(name)):
            for c in cols:
                assert row[c].isdigit(), (name, row)
            if i > 50_000:
                break


def test_no_corpus_noise(e):
    for junk in ("ofthe", "litde", "vous", "und", "th", "ve", "Elsevier", "i"):
        assert junk not in e, junk


def test_core_words_rank_high(e):
    for word in ("the", "you", "and", "I", "is", "what", "okay", "thanks"):
        assert f(e, word) >= 180, word


def test_pronoun_i_is_capitalised(e):
    assert "I" in e and "i" not in e


def test_contractions(e):
    for word in ("don't", "I'm", "can't", "it's", "you're", "won't", "let's"):
        assert f(e, word) >= 140, word
    assert "don" not in e or f(e, "don") < f(e, "don't")


def test_british_spelling_preferred(e):
    for us, gb in (("color", "colour"), ("organize", "organise"), ("center", "centre")):
        assert f(e, gb) > f(e, us), gb


def test_data_driven_casing(e):
    assert "India" in e and "india" not in e
    assert "London" in e and "london" not in e
    assert "bill" in e and "Bill" in e


def test_ordinary_words_keep_lowercase_ahead(e):
    assert f(e, "pin") > f(e, "PIN")
    assert f(e, "erode") and "Erode" in e  # city kept, verb not displaced
    assert "shiny" in e and "vile" in e


def test_curated_indian_words(e):
    for word in ("lakh", "crore", "prepone", "Aadhaar", "UPI", "Bengaluru",
                 "Thiruvananthapuram", "Rahul", "Priyanka", "Diwali", "biryani"):
        assert word in e, word
    assert f(e, "lakh") >= 170 and f(e, "crore") >= 170


def test_hinglish_below_everyday_english(e):
    assert "kya" in e and "nahi" in e
    assert f(e, "hai") < f(e, "have")
    assert f(e, "kya") < f(e, "what")


def test_offensive_words_flagged(e):
    assert e["fuck"].offensive and f(e, "fuck") == 0
    for entry in e.values():
        for target in entry.bigrams:
            assert not e[target].offensive, (entry.word, target)


def test_predictions(e):
    assert "you" in e["thank"].bigrams
    assert "know" in e["don't"].bigrams
    assert "going" in e["I'm"].bigrams
    assert "Diwali" in e["happy"].bigrams
    assert "go" in e["let's"].bigrams
    assert "know" not in e["can't"].bigrams or "help" in e["can't"].bigrams


def test_combined_output_is_valid(d, tmp_path):
    out = tmp_path / "x.combined"
    build.write_combined(d, out)
    check_combined(out.read_text(encoding="utf-8"))


def test_committed_output_is_up_to_date(d, tmp_path):
    out = tmp_path / "en_IN.combined"
    build.write_combined(d, out)
    assert out.read_text(encoding="utf-8") == COMBINED.read_text(encoding="utf-8"), (
        "output/ is stale: run `python3 build.py`"
    )


def check_combined(text):
    lines = text.splitlines()
    assert HEADER_RE.match(lines[0]), lines[0]
    words = []
    for line in lines[1:]:
        m = WORD_RE.match(line) or BIGRAM_RE.match(line)
        assert m, f"bad line: {line!r}"
        assert 0 <= int(m.group(1)) <= 255
        if line.startswith(" word="):
            words.append(line[len(" word="):].split(",")[0])
        else:
            assert words, "bigram before any word"
    assert len(words) == len(set(words)), "duplicate words"
    known = set(words)
    for line in lines[1:]:
        if line.startswith("  bigram="):
            assert line[len("  bigram="):].split(",")[0] in known, line
    return words


def test_hinglish_coverage(e):
    for word in ("kya", "hai", "nahi", "theek", "yaar", "karunga", "jaunga", "milte"):
        assert word in e, word
    assert f(e, "kya") >= 160 and f(e, "yaar") >= 160
    assert f(e, "kya") < f(e, "what")
    assert "raha" in e["kar"].bigrams and "liye" in e["mere"].bigrams
    assert "nahi" in e["koi"].bigrams or "baat" in e["koi"].bigrams


# ---------------------------------------------------------- keyboard export

OUT = ROOT / "output"


def load(name, n_keys):
    lines = (OUT / name).read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("#"), "first line must be a # comment"
    rows = {}
    for line in lines[1:]:
        parts = line.split("\t")
        assert len(parts) == n_keys + 1, line
        assert parts[-1].isdigit() and int(parts[-1]) >= 1, line
        for w in parts[:-1]:
            assert w == w.lower(), line
        key = tuple(parts[:-1])
        assert key not in rows, f"duplicate {line}"
        rows[key] = int(parts[-1])
    return rows


@pytest.fixture(scope="module")
def kb():
    return {
        "words": {k[0]: v for k, v in load("en_IN_words.tsv", 1).items()},
        "bigrams": load("en_IN_bigrams.tsv", 2),
        "trigrams": load("en_IN_trigrams.tsv", 3),
    }


def test_keyboard_sizes(kb):
    assert len(kb["words"]) == 150_000
    assert len(kb["bigrams"]) == 400_000
    assert len(kb["trigrams"]) == 500_000


def test_keyboard_word_scale(kb):
    w = kb["words"]
    assert all(1 <= v <= 150 for v in w.values())
    assert w["the"] == 150
    assert 60 <= w["time"] <= 110
    assert w["kya"] > 50 and w["lakh"] > 50
    assert w["colour"] > w["color"]
    assert w["fuck"] == 1


def test_keyboard_phrases_use_known_words(kb):
    words = kb["words"]
    for key in list(kb["bigrams"]) + list(kb["trigrams"]):
        for x in key:
            assert x in words, key


def test_keyboard_predictions(kb):
    b, t = kb["bigrams"], kb["trigrams"]
    assert b[("of", "the")] > 1_000_000
    assert b[("i'm", "going")] > 10_000      # rebuilt from "I 'm going"
    assert b[("i", "don't")] > 10_000        # rebuilt from "I do not"
    assert b[("don't", "know")] > 10_000
    assert b[("kya", "hai")] > 100 and b[("kar", "raha")] > 100
    assert t[("i'm", "going", "to")] > 10_000
    assert t[("how", "are", "you")] > 1_000
    assert t[("kya", "kar", "rahe")] > 100
