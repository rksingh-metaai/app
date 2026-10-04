import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "base_small.txt"
COMBINED = ROOT / "output" / "en_IN.combined"

HEADER_RE = re.compile(
    r"^dictionary=main:en_in,locale=en_IN,description=[^,]+,date=\d+,version=\d+$"
)
WORD_RE = re.compile(r"^ word=[^,\s]+,f=(\d+)(,possibly_offensive=true)?$")
BIGRAM_RE = re.compile(r"^  bigram=[^,\s]+,f=(\d+)$")


@pytest.fixture(scope="module")
def small():
    return build.build(FIXTURE).entries


def f(entries, word):
    return entries[word].f


def test_pronoun_i_is_capitalised(small):
    assert "I" in small and "i" not in small


def test_contractions_replace_fragments(small):
    assert "don't" in small and "I'm" in small
    for junk in ("don", "dont", "s", "mm-hmm", "xyz123"):
        assert junk not in small


def test_british_spelling_preferred(small):
    assert f(small, "colour") > f(small, "color")


def test_proper_nouns_replace_lowercase(small):
    assert "India" in small and "india" not in small
    assert "Delhi" in small and "delhi" not in small


def test_ordinary_words_keep_lowercase_ahead(small):
    assert f(small, "west") > f(small, "West")
    assert f(small, "salt") > f(small, "Salt")
    assert f(small, "may") > f(small, "May")


def test_acronyms_rank_below_lowercase_word(small):
    assert f(small, "pin") > f(small, "PIN")


def test_curated_indian_words_present(small):
    for word in ("lakh", "crore", "prepone", "Aadhaar", "kya", "Rahul", "Bengaluru"):
        assert word in small


def test_hinglish_below_everyday_english(small):
    assert f(small, "hai") < f(small, "good")


def test_offensive_words_flagged(small):
    assert small["fuck"].offensive and f(small, "fuck") == 0


def test_bigrams_attached(small):
    assert "morning" in small["good"].bigrams
    assert "Delhi" in small["new"].bigrams


def test_combined_output_is_valid(tmp_path):
    d = build.build(FIXTURE)
    out = tmp_path / "x.combined"
    build.write_combined(d, out)
    check_combined(out.read_text(encoding="utf-8"))


@pytest.mark.skipif(not COMBINED.exists(), reason="output not built")
def test_committed_output_is_valid():
    text = COMBINED.read_text(encoding="utf-8")
    words = check_combined(text)
    assert len(words) > 40000


@pytest.mark.skipif(
    not (build.CACHE / "en_50k.txt").exists() or not COMBINED.exists(),
    reason="base list not cached",
)
def test_committed_output_is_up_to_date(tmp_path):
    d = build.build(build.fetch_base())
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
    return words
