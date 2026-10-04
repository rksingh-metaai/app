"""Export the three keyboard database files (words, bigrams, trigrams).

Format (what the keyboard importer expects):
  * all entries lowercase; case variants ("I"/"i", "Bill"/"bill") are merged
    by adding their frequencies;
  * a "#" comment as the first line, then tab-separated rows;
  * words:    word, frequency on the keyboard's 1-150 log scale:
              f = 150 + 30 * log10(per_billion / per_billion("the")),
              clamped to 1..150 ("the" = 150, +30 = 10x more common);
  * bigrams:  word1, word2, estimated occurrences per billion words;
  * trigrams: word1, word2, word3, estimated occurrences per billion words.
All frequencies are whole numbers.

Entries are chosen best-first up to the limits in build.py: hand-curated
entries always, then by frequency. Curated words and phrases carry a
frequency floor on the AOSP 0-255 scale; it is converted to occurrences per
billion with the same formula used for the corpus data.
"""

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

import build

# Tokens in the English Fiction 1-gram export (1990-2019) that the bigram and
# trigram counts are relative to.
FICTION_TOKENS = 116_539_799_483

WORD_TOP = 150      # frequency of "the"
WORD_PER_DECADE = 30
WORD_MIN = 1


def f_to_per_billion(f: float) -> float:
    """Inverse of build.per_billion_to_f (AOSP 0-255 scale)."""
    return 10 ** ((f - build.F_OFFSET) / build.F_SLOPE)


def p_from_f(f: float) -> float:
    """Conditional probability from the 0-255 prediction scale used by the
    curated bigrams/trigrams: f = 255 + 32 * log10(p)."""
    return 10 ** ((f - 255) / 32)


def effective_per_billion(e: build.Entry) -> float:
    """Corpus frequency adjusted by every boost or penalty applied to the
    word's 0-255 frequency (curated floors, British spelling, casing)."""
    if e.per_billion > 0:
        return e.per_billion * 10 ** ((e.f - build.per_billion_to_f(e.per_billion)) / build.F_SLOPE)
    return f_to_per_billion(e.f)


def export(d: build.Dictionary, out: Path) -> dict[str, int]:
    # ---- words: merge case variants, choose the best UNIGRAM_LIMIT.
    per_billion: dict[str, float] = defaultdict(float)
    forced: set[str] = set()
    offensive: set[str] = set()
    for e in d.entries.values():
        lw = e.word.lower()
        if e.offensive:
            offensive.add(lw)
        else:
            per_billion[lw] += effective_per_billion(e)
        if e.curated or e.offensive:
            forced.add(lw)
    for lw in offensive:
        per_billion.setdefault(lw, 0.0)

    ranked = sorted(per_billion, key=lambda w: (-per_billion[w], w))
    must = [w for w in ranked if w in forced]
    rest = [w for w in ranked if w not in forced]
    words = set(must + rest[: build.UNIGRAM_LIMIT - len(must)])
    top = per_billion["the"]

    def word_f(w: str) -> int:
        if w in offensive or per_billion[w] <= 0:
            return WORD_MIN
        f = WORD_TOP + WORD_PER_DECADE * math.log10(per_billion[w] / top)
        return max(WORD_MIN, min(WORD_TOP, round(f)))

    def ok(*ws: str) -> bool:
        return all(w in words and w not in offensive for w in ws)

    # ---- bigrams: corpus pairs + curated pairs, merged by lowercase.
    # Pairs around split contractions are rebuilt from 3-grams ("I do not"
    # -> "i don't"; "I 'm going" -> "i'm going"); they replace the sparse
    # direct counts of contracted tokens and correct the split pairs.
    rebuilt: dict[tuple[str, str], float] = defaultdict(float)
    for w1, w2, count in build.read_generated("contraction_bigrams.tsv"):
        rebuilt[(w1.lower(), w2.lower())] += int(count) * 1e9 / FICTION_TOKENS
    rebuilt_firsts = {a for (a, _), v in rebuilt.items() if v > 0 and "'" in a}

    bigram: dict[tuple[str, str], float] = defaultdict(float)
    for w1, w2, count, _ in build.read_generated("bigrams.tsv"):
        key = (w1.lower(), w2.lower())
        if ok(*key) and key[0] not in rebuilt_firsts:
            bigram[key] += int(count) * 1e9 / FICTION_TOKENS
    for key, v in rebuilt.items():
        if ok(*key):
            bigram[key] += v
    for key in [k for k, v in bigram.items() if v < 0.5]:
        del bigram[key]
    curated_bi: set[tuple[str, str]] = set()
    for row in (build.read_lines(build.DATA / "bigrams.txt")
                + build.read_lines(build.DATA / "hinglish_bigrams.txt")):
        key = (row[0].lower(), row[1].lower())
        if not ok(*key):
            raise ValueError(f"curated bigram {row[0]} {row[1]}: word not exported")
        estimate = p_from_f(int(row[2])) * per_billion[key[0]]
        bigram[key] = max(bigram[key], estimate)
        curated_bi.add(key)
    chosen_bi = pick(bigram, curated_bi, build.BIGRAM_LIMIT)

    # ---- trigrams: same, curated phrases estimated from their pair.
    trigram: dict[tuple[str, str, str], float] = defaultdict(float)
    for w1, w2, w3, count, _ in build.read_generated("trigrams.tsv.gz"):
        key = (w1.lower(), w2.lower(), w3.lower())
        if ok(*key):
            trigram[key] += int(count) * 1e9 / FICTION_TOKENS
    curated_tri: set[tuple[str, str, str]] = set()
    for row in (build.read_lines(build.DATA / "trigrams.txt")
                + build.read_lines(build.DATA / "hinglish_trigrams.txt")):
        key = (row[0].lower(), row[1].lower(), row[2].lower())
        if not ok(*key):
            raise ValueError(f"curated trigram {' '.join(row[:3])}: word not exported")
        context = bigram.get(key[:2]) or per_billion[key[0]] * 0.01
        trigram[key] = max(trigram[key], p_from_f(int(row[3])) * context)
        curated_tri.add(key)
    chosen_tri = pick(trigram, curated_tri, build.TRIGRAM_LIMIT)

    # ---- write.
    out.mkdir(parents=True, exist_ok=True)
    word_rows = sorted(words, key=lambda w: (-word_f(w), -per_billion[w], w))
    write(out / "en_IN_words.tsv",
          "# word\tfrequency (1-150, +30 = 10x more common)",
          (f"{w}\t{word_f(w)}" for w in word_rows))
    write(out / "en_IN_bigrams.tsv",
          "# word1\tword2\tfrequency (estimated occurrences per billion words)",
          (f"{a}\t{b}\t{v}" for (a, b), v in chosen_bi))
    write(out / "en_IN_trigrams.tsv",
          "# word1\tword2\tword3\tfrequency (estimated occurrences per billion words)",
          (f"{a}\t{b}\t{c}\t{v}" for (a, b, c), v in chosen_tri))
    return {"words": len(word_rows), "bigrams": len(chosen_bi), "trigrams": len(chosen_tri)}


def pick(scores: dict, forced: set, limit: int) -> list[tuple[tuple, int]]:
    """Forced entries plus the highest-scoring rest, up to `limit`, as whole
    numbers (at least 1), sorted by frequency."""
    rest = sorted((k for k in scores if k not in forced), key=lambda k: (-scores[k], k))
    keys = list(forced) + rest[: max(0, limit - len(forced))]
    rows = [(k, max(1, round(scores[k]))) for k in keys]
    rows.sort(key=lambda kv: (-kv[1], kv[0]))
    return rows


def write(path: Path, header: str, rows) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(header + "\n")
        for row in rows:
            fh.write(row + "\n")
