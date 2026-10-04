#!/usr/bin/env python3
"""Derive next-word predictions and contraction frequencies from Google Books
Ngram (English Fiction) 2-gram counts.

Inputs:
  bi_fiction.tsv        "w1 w2<TAB>count" from tools/ngramcount (1990-2019)
  uni_fiction.tsv       fiction unigram counts (for the corpus size)
  data/generated/unigrams.tsv, data/contractions.txt, data/offensive.txt

Outputs:
  data/generated/bigrams.tsv       "w1<TAB>w2<TAB>count<TAB>f"
                                   count: pair occurrences 1990-2019 (used to
                                   rank pairs globally); f: 0-255 AOSP scale of
                                   P(w2 | w1) (used to rank predictions)
  data/generated/contractions.tsv  "word<TAB>per_billion" (whole number)

Contractions are mostly split in the source ("I 'm", "do not"), so their
frequencies are rebuilt from those pairs. Their predictions come from the
pairs that kept the contraction intact ("don't know"); when there are too few
of those, they are borrowed from the expanded word ("it's" -> after "is").
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GENERATED = DATA / "generated"

CLITICS = {"'s", "'m", "'re", "'ll", "'ve", "'d", "not"}
# Word whose followers stand in for a contraction's (it's -> is, I'll -> will).
EXPANSION = {"'s": "is", "'m": "am", "'re": "are", "'ll": "will", "'ve": "have",
             "'d": "would", "not": "not"}
# Contractions with fewer direct predictions than this borrow them.
MIN_DIRECT = 15
# Predictions kept per word here; build.py picks the global best from these.
K_PER_WORD = 12
# Followers of "not" come from every "X not" pair; after do/modal
# contractions ("don't", "can't") a bare verb follows, never these.
NOT_AFTER_MODAL = {
    "to", "a", "an", "the", "only", "that", "in", "of", "for", "as", "with",
    "at", "by", "from", "on", "yet", "and", "or", "but", "been", "being", "I",
    "he", "she", "it", "we", "they", "this", "his", "her", "my", "one",
}
MODAL_FIRSTS = {"do", "does", "did", "can", "will", "could", "would", "should",
                "must", "need"}
P_MIN = 0.002  # minimum P(w2 | w1)
COUNT_MIN = 200  # minimum pair count (1990-2019)


def read_rows(path: Path) -> list[list[str]]:
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            rows.append(line.split())
    return rows


def load_unigrams() -> list[str]:
    words = []
    for line in (GENERATED / "unigrams.tsv").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            words.append(line.split("\t")[0])
    return words


def bigram_f(p: float) -> int:
    return max(1, min(255, round(255 + 32 * math.log10(p))))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--bigrams", type=Path, required=True)
    parser.add_argument("--fiction-unigrams", type=Path, required=True)
    args = parser.parse_args()

    words = load_unigrams()
    rank = {w: i for i, w in enumerate(words)}
    vocab = set(words)
    by_lower: dict[str, str] = {}
    for w in words:  # most frequent first; a lowercase word always wins
        lw = w.lower()
        if lw not in by_lower or w == lw:
            by_lower[lw] = w

    offensive = {
        tok.lower()
        for row in read_rows(DATA / "offensive.txt")
        for tok in row
    }

    def canon(token: str) -> str | None:
        if token in vocab:
            return token
        return by_lower.get(token.lower())

    pair: dict[tuple[str, str], int] = defaultdict(int)
    clitic_pair: dict[tuple[str, str], int] = defaultdict(int)  # ("do", "not")
    with args.bigrams.open(encoding="utf-8") as fh:
        for line in fh:
            ngram, _, count = line.rstrip("\n").rpartition("\t")
            t1, _, t2 = ngram.partition(" ")
            c = int(count)
            if t2 in CLITICS:
                clitic_pair[(t1.lower() if t1 != "I" else "I", t2)] += c
            c1, c2 = canon(t1), canon(t2)
            if c1 and c2 and not t2.startswith("'"):
                pair[(c1, c2)] += c

    # Contractions.
    corpus_size = 0
    with args.fiction_unigrams.open(encoding="utf-8") as fh:
        for line in fh:
            corpus_size += int(line.rpartition("\t")[2])
    contraction_count: dict[str, float] = {}
    for row in read_rows(DATA / "contractions.txt"):
        word, first, second = row[0], row[1], row[2]
        share = float(row[3]) if len(row) > 3 else 1.0
        key = (first if first == "I" else first.lower(), second)
        n = clitic_pair.get(key, 0) * share
        if n:
            contraction_count[word] = n
    with (GENERATED / "contractions.tsv").open("w", encoding="utf-8") as out:
        out.write("# word\tper_billion  (Google Books Ngram 2020, fiction 2-grams)\n")
        for word, n in sorted(contraction_count.items(), key=lambda kv: -kv[1]):
            out.write(f"{word}\t{round(n * 1e9 / corpus_size)}\n")

    followers: dict[str, dict[str, int]] = defaultdict(dict)
    for (w1, w2), n in pair.items():
        followers[w1][w2] = n

    # Predictions after contractions: direct pairs, else borrowed.
    borrowed = 0
    for row in read_rows(DATA / "contractions.txt"):
        word, first, second = row[0], row[1], row[2]
        if word not in vocab and word not in contraction_count:
            continue
        direct = [n for n in followers.get(word, {}).values() if n >= COUNT_MIN]
        if len(direct) >= MIN_DIRECT:
            continue
        if word not in contraction_count:
            continue
        modal = second == "not" and first in MODAL_FIRSTS
        source = followers.get(EXPANSION[second], {})
        # Scale the borrowed counts down to the contraction's own frequency
        # so they compete fairly with real pairs in the global ranking.
        scale = min(1.0, contraction_count[word] / max(1, sum(source.values())))
        for nxt, n in source.items():
            if modal and nxt in NOT_AFTER_MODAL:
                continue
            pair[(word, nxt)] = max(pair.get((word, nxt), 0), round(n * scale))
        borrowed += 1

    first_total: dict[str, int] = defaultdict(int)
    for (w1, _), n in pair.items():
        first_total[w1] += n

    candidates: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for (w1, w2), n in pair.items():
        if n >= COUNT_MIN and w2.lower() not in offensive and w1.lower() not in offensive:
            candidates[w1].append((n, w2))

    kept = 0
    with (GENERATED / "bigrams.tsv").open("w", encoding="utf-8") as out:
        out.write("# w1\tw2\tcount\tf  (Google Books Ngram 2020, fiction 2-grams)\n")
        for w1 in sorted(candidates, key=lambda w: rank.get(w, -1)):
            for n, w2 in sorted(candidates[w1], reverse=True)[:K_PER_WORD]:
                p = n / first_total[w1]
                if p < P_MIN:
                    break
                out.write(f"{w1}\t{w2}\t{n}\t{bigram_f(p)}\n")
                kept += 1
    print(f"{len(contraction_count)} contractions ({borrowed} with borrowed "
          f"predictions), {kept} bigrams")


if __name__ == "__main__":
    main()
