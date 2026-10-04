#!/usr/bin/env python3
"""Derive 3-word predictions (trigrams) from Google Books Ngram English
Fiction 3-gram counts.

Inputs:
  tri_fiction.tsv   "w1 w2 w3<TAB>count" from tools/ngramcount (1990-2019)
  data/generated/unigrams.tsv, data/generated/contractions.tsv,
  data/contractions.txt, data/offensive.txt

Output:
  data/generated/trigrams.tsv.gz  "w1<TAB>w2<TAB>w3<TAB>count<TAB>f"
  count: occurrences 1990-2019 (ranks phrases globally); f: 0-255, same scale
  as the bigram predictions: 255 + 32*log10(P(w3 | w1 w2))

Contractions are split in the source. A 3-gram starting with a clitic
("'m going to") is credited to the contractions ending in it (I'm going ->
to), in proportion to how often each occurs; "'s" is skipped because it is
mostly possessive. Do/modal negations borrow their contexts from "not"
("don't know" -> what, as after "not know"). 3-grams with a clitic in
second or third place are dropped: they are 2-word phrases in disguise.
"""

from __future__ import annotations

import argparse
import gzip
import io
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GENERATED = DATA / "generated"

K_PER_CONTEXT = 5      # predictions kept per two-word context
P_MIN = 0.01           # minimum P(w3 | w1 w2)
COUNT_MIN = 200        # minimum 3-gram count (1990-2019)
CONTEXT_MIN = 1000     # minimum total count of a two-word context
MODAL_FIRSTS = {"do", "does", "did", "can", "will", "could", "would", "should",
                "must", "need"}


def read_rows(path: Path) -> list[list[str]]:
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            rows.append(line.split())
    return rows


def read_generated(name: str) -> list[list[str]]:
    return [
        line.split("\t")
        for line in (GENERATED / name).read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]


def trigram_f(p: float) -> int:
    return max(1, min(255, round(255 + 32 * math.log10(p))))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--trigrams", type=Path, required=True)
    args = parser.parse_args()

    words = [row[0] for row in read_generated("unigrams.tsv")]
    vocab = set(words)
    by_lower: dict[str, str] = {}
    for w in words:  # most frequent first; a lowercase word always wins
        lw = w.lower()
        if lw not in by_lower or w == lw:
            by_lower[lw] = w
    offensive = {tok.lower() for row in read_rows(DATA / "offensive.txt") for tok in row}

    def canon(token: str) -> str | None:
        if token in vocab:
            return token
        return by_lower.get(token.lower())

    # Contractions sharing a clitic, weighted by frequency ("'re" -> you're,
    # we're, they're). "'s" is excluded: mostly possessive ("John's car").
    freq = {row[0]: float(row[1]) for row in read_generated("contractions.tsv")}
    by_clitic: dict[str, list[tuple[str, float]]] = defaultdict(list)
    negations: list[str] = []
    for row in read_rows(DATA / "contractions.txt"):
        word, first, second = row[0], row[1], row[2]
        if word not in freq:
            continue
        if second.startswith("'") and second != "'s":
            by_clitic[second].append((word, freq[word]))
        elif second == "not" and first in MODAL_FIRSTS:
            negations.append(word)
    clitic_share = {
        clitic: [(w, f / sum(x for _, x in items)) for w, f in items]
        for clitic, items in by_clitic.items()
    }

    # Split contractions: ("do", "not") -> ("don't", 0.7), ("I", "'m") -> ("I'm", 1).
    contraction: dict[tuple[str, str], tuple[str, float]] = {}
    for row in read_rows(DATA / "contractions.txt"):
        if row[0] in freq:
            contraction[(row[1], row[2])] = (row[0], float(row[3]) if len(row) > 3 else 1.0)

    def split(a: str, b: str) -> tuple[str, float] | None:
        return contraction.get((a if a == "I" else a.lower(), b))

    counts: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    # Pairs involving a contraction, rebuilt from 3-grams: "and I 'm" ->
    # (and, I'm); "do not know" -> (don't, know). Negative counts remove the
    # share that moved out of the split pair ("I do" loses "I do n't").
    pairs: dict[tuple[str, str], float] = defaultdict(float)
    with args.trigrams.open(encoding="utf-8") as fh:
        for line in fh:
            ngram, _, count = line.rstrip("\n").rpartition("\t")
            t1, t2, t3 = ngram.split(" ")
            n = int(count)
            tail = split(t2, t3)   # "<t1> do not", "<t1> I 'm"
            head = split(t1, t2)   # "do not <t3>", "I 'm <t3>"
            if tail and not t1.startswith("'"):
                c1, c2 = canon(t1), canon(t2)
                if c1 and c2:
                    word, share = tail
                    pairs[(c1, word)] += n * share
                    pairs[(c1, c2)] -= n * share
            if head and not t3.startswith("'"):
                c3 = canon(t3)
                if c3:
                    word, share = head
                    pairs[(word, c3)] += n * share
            if t2.startswith("'") or t3.startswith("'"):
                continue
            c2, c3 = canon(t2), canon(t3)
            if not (c2 and c3):
                continue
            # The contracted share of "do not X" / "I do not" is not a 3-word
            # phrase once typed as "don't X" / "I don't".
            keep = 1.0 - max(tail[1] if tail else 0.0, head[1] if head else 0.0)
            if keep <= 0:
                continue
            if t1.startswith("'"):
                for word, share in clitic_share.get(t1, ()):
                    counts[(word, c2)][c3] += n * share
                continue
            c1 = canon(t1)
            if c1:
                counts[(c1, c2)][c3] += n * keep

    with (GENERATED / "contraction_bigrams.tsv").open("w", encoding="utf-8") as out:
        out.write("# w1\tw2\tcount  pairs rebuilt around split contractions "
                  "(negative: share moved out of the split pair)\n")
        for (a, b), n in sorted(pairs.items()):
            if abs(n) >= COUNT_MIN:
                out.write(f"{a}\t{b}\t{round(n)}\n")

    # "don't know" -> what: borrow from "not know" unless direct data exists,
    # scaled by how much of "not" each contraction accounts for.
    not_freq = next(float(r[1]) for r in read_generated("unigrams.tsv") if r[0] == "not")
    for (w1, w2), followers in list(counts.items()):
        if w1 != "not":
            continue
        for neg in negations:
            if (neg, w2) not in counts:
                scale = min(1.0, freq[neg] / not_freq)
                counts[(neg, w2)] = {w: n * scale for w, n in followers.items()}

    kept = contexts = 0
    # gzip with mtime=0 so identical data gives an identical file.
    with gzip.GzipFile(GENERATED / "trigrams.tsv.gz", "wb", mtime=0) as raw, \
            io.TextIOWrapper(raw, encoding="utf-8", newline="\n") as out:
        out.write("# w1\tw2\tw3\tcount\tf  (Google Books Ngram 2020, fiction 3-grams)\n")
        for (w1, w2) in sorted(counts):
            followers = counts[(w1, w2)]
            total = sum(followers.values())
            if total < CONTEXT_MIN or w1.lower() in offensive or w2.lower() in offensive:
                continue
            ranked = sorted(followers.items(), key=lambda kv: (-kv[1], kv[0]))
            wrote = False
            for w3, n in ranked[:K_PER_CONTEXT]:
                p = n / total
                if n < COUNT_MIN or p < P_MIN:
                    break
                if w3.lower() in offensive:
                    continue
                out.write(f"{w1}\t{w2}\t{w3}\t{round(n)}\t{trigram_f(p)}\n")
                kept += 1
                wrote = True
            contexts += wrote
    print(f"{contexts} contexts, {kept} trigrams")


if __name__ == "__main__":
    main()
