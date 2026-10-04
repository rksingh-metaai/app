#!/usr/bin/env python3
"""Build an English (India) dictionary for AOSP-based Android keyboards.

Pipeline (all inputs are in data/, nothing is downloaded):
  1. Base vocabulary and frequencies: data/generated/unigrams.tsv
     (Google Books Ngram 2020, CC BY 3.0, validated against SCOWL).
  2. Contractions: data/generated/contractions.tsv.
  3. Indian spelling preferences (British forms preferred: colour, organise).
  4. Curated Indian layers: Indian English terms, places, names, Hinglish.
  5. Offensive words are flagged; next-word predictions are attached from
     data/generated/bigrams.tsv plus the curated data/bigrams.txt.
  6. Write the AOSP combined word list (output/en_IN.combined) and a TSV.

Regenerate data/generated/ with tools/fetch_ngrams.sh (needs ~250 GB of
streaming download, no disk). Compile the .combined file to a binary .dict
with AOSP dicttool (see README).

Usage:
  python3 build.py [--report-recased]
"""

from __future__ import annotations

import argparse
import gzip
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
GENERATED = DATA / "generated"
OUTPUT = ROOT / "output"

# Dictionary header. Bump VERSION whenever the word list changes; DATE is kept
# fixed per version so builds are reproducible.
DICT_ID = "main:en_in"
LOCALE = "en_IN"
DESCRIPTION = "English (India)"
VERSION = 3
DATE = 1791072000  # 2026-10-04 00:00 UTC

# Per-billion frequencies are mapped to the AOSP 0..255 unigram scale with
# f = F_SLOPE * log10(per_billion) + F_OFFSET, clamped to [F_MIN, F_MAX].
# "the" (~57M per billion) lands at ~250, a 6-per-billion word at ~20.
F_SLOPE = 33.0
F_OFFSET = -5.7
F_MAX = 250
F_MIN = 15
# Offensive words stay in the dictionary (so they aren't "corrected" into
# something else) but are flagged and pushed down; keyboards hide them when
# "block offensive words" is on.
F_OFFENSIVE = 0
# British spelling is preferred; the US variant is kept but ranked below it.
US_VARIANT_PENALTY = 25
# A capitalised/acronym form kept next to an ordinary lowercase word ranks
# this much below it ("West" < "west", "PIN" < "pin").
CASED_VARIANT_GAP = 10

# Output sizes. Entries are chosen best-first:
#  * words: every curated word, then the most frequent ones;
#  * pairs / 3-word phrases: hand-written ones, then those occurring most
#    often in the corpus (a common sequence like "thank you" beats a rare one
#    that merely has a high conditional probability).
UNIGRAM_LIMIT = 150_000
BIGRAM_LIMIT = 400_000
TRIGRAM_LIMIT = 500_000

CURATED_WORD_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9'.\-]*$")


@dataclass
class Entry:
    word: str
    f: int
    offensive: bool = False
    curated: bool = False  # came from a hand-curated list, never auto-removed
    per_billion: float = 0.0  # corpus frequency; breaks ties between equal f
    bigrams: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------- data files


def read_lines(path: Path) -> list[list[str]]:
    """Non-empty, non-comment lines split on whitespace / tabs."""
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            rows.append(line.split())
    return rows


def read_wordset(name: str) -> set[str]:
    """Every whitespace-separated token in the file."""
    return {word for row in read_lines(DATA / name) for word in row}


def read_curated(name: str, default_f: int) -> list[tuple[str, int]]:
    """Whitespace-separated words, optionally `word=f`.

    A line `@@ f` sets the default frequency for the lines that follow.
    """
    out = []
    current = default_f
    for row in read_lines(DATA / name):
        if row[0] == "@@":
            current = int(row[1])
            continue
        for token in row:
            word, _, freq = token.partition("=")
            if not CURATED_WORD_RE.match(word):
                raise ValueError(f"{name}: invalid word {word!r}")
            f = int(freq) if freq else current
            if not 0 <= f <= 255:
                raise ValueError(f"{name}: frequency out of range for {word!r}")
            out.append((word, f))
    return out


def per_billion_to_f(per_billion: float) -> int:
    f = F_SLOPE * math.log10(max(per_billion, 1e-9)) + F_OFFSET
    return max(F_MIN, min(F_MAX, round(f)))


def read_generated(name: str) -> list[list[str]]:
    path = GENERATED / name
    if name.endswith(".gz"):
        text = gzip.decompress(path.read_bytes()).decode("utf-8")
    else:
        text = path.read_text(encoding="utf-8")
    return [
        line.split("\t")
        for line in text.splitlines()
        if line and not line.startswith("#")
    ]


# ---------------------------------------------------------------- build


class Dictionary:
    def __init__(self) -> None:
        self.entries: dict[str, Entry] = {}
        self.recased: list[tuple[str, str]] = []  # (removed lowercase, kept form)

    def get(self, word: str) -> Entry | None:
        return self.entries.get(word)

    def put(self, word: str, f: int, curated: bool = False,
            per_billion: float = 0.0) -> Entry:
        """Add `word`, keeping the higher frequency if it already exists."""
        entry = self.entries.get(word)
        if entry is None:
            entry = self.entries[word] = Entry(word, f)
        else:
            entry.f = max(entry.f, f)
        entry.curated |= curated
        entry.per_billion = max(entry.per_billion, per_billion)
        return entry

    def recase(self, word: str, f: int, keep_lowercase: set[str]) -> int:
        """Add the properly cased `word`, merging it with a lowercase entry.

        Normally the lowercase entry ("delhi") is replaced and its frequency
        inherited. It is kept instead when it is ordinary English
        (keep_lowercase.txt: "will", "west"), was itself curated, or `word` is
        an acronym ("PIN" vs "pin"); the cased form is then ranked just below
        the lowercase one so it never hijacks everyday typing.
        Returns the final frequency of `word`.
        """
        lower = word.lower()
        entry = self.entries.get(lower)
        if lower == word or entry is None:
            return self.put(word, f, curated=True).f
        acronym = len(word) > 1 and word.isupper()
        if acronym or lower in keep_lowercase or entry.curated:
            # The curated floor never lifts the cased form above the
            # lowercase word (data-derived frequencies are kept as they are).
            f = max(0, min(f, entry.f - CASED_VARIANT_GAP))
            return self.put(word, f, curated=True).f
        del self.entries[lower]
        self.recased.append((lower, word))
        return self.put(word, max(f, entry.f), curated=True,
                        per_billion=entry.per_billion).f


def build(select: bool = True) -> Dictionary:
    """The full dictionary. With `select`, trimmed to UNIGRAM_LIMIT words and
    BIGRAM_LIMIT predictions for the AOSP word list; the keyboard export
    (export_keyboard.py) does its own selection on the full dictionary."""
    exclude = read_wordset("exclude.txt")
    keep_lowercase = read_wordset("keep_lowercase.txt")
    offensive = {w.lower() for w in read_wordset("offensive.txt")}

    d = Dictionary()
    for word, per_billion in read_generated("unigrams.tsv"):
        if word not in exclude:
            pb = float(per_billion)
            d.put(word, per_billion_to_f(pb), per_billion=pb)
    for word, per_billion in read_generated("contractions.tsv"):
        pb = float(per_billion)
        d.put(word, per_billion_to_f(pb), curated=True, per_billion=pb)

    # Indian English follows British spelling: "colour" outranks "color".
    for us, gb in read_lines(DATA / "spelling_gb.tsv"):
        us_entry, gb_entry = d.get(us), d.get(gb)
        top = max(e.f for e in (us_entry, gb_entry) if e) if (us_entry or gb_entry) else 0
        if not top:
            continue
        d.put(gb, top)
        if us_entry:
            us_entry.f = max(F_MIN, min(us_entry.f, top - US_VARIANT_PENALTY))

    # Curated Indian layers. A curated frequency is a floor: Indian users type
    # these far more often than British/fiction books suggest.
    for name, default_f in (
        ("modern.txt", 160),
        ("indian_english.txt", 140),
        ("places.txt", 130),
        ("names.txt", 115),
        ("hinglish.txt", 105),
        ("hinglish_vocab.txt", 115),
    ):
        for word, f in read_curated(name, default_f):
            d.recase(word, f, keep_lowercase)

    for word, entry in d.entries.items():
        if word.lower() in offensive:
            entry.offensive = True
            entry.f = F_OFFENSIVE

    if select:
        select_words(d, UNIGRAM_LIMIT)
        select_bigrams(d, BIGRAM_LIMIT)
    return d


def select_words(d: Dictionary, limit: int) -> None:
    """Keep `limit` words: curated and flagged-offensive ones first (the latter
    so they are never "corrected" into something else), then by frequency."""
    def rank(e: Entry):
        return (-e.f, -e.per_billion, e.word.lower(), e.word)

    must = sorted((e for e in d.entries.values() if e.curated or e.offensive), key=rank)
    rest = sorted((e for e in d.entries.values() if not (e.curated or e.offensive)), key=rank)
    if len(must) > limit:
        raise ValueError(f"{len(must)} curated words exceed the {limit} word limit")
    keep = must + rest[: limit - len(must)]
    d.entries = {e.word: e for e in keep}


def usable(d: Dictionary, *words: str) -> bool:
    return all((e := d.get(w)) is not None and not e.offensive for w in words)


def select_bigrams(d: Dictionary, limit: int) -> None:
    """Hand-written pairs first, then the pairs that occur most often."""
    chosen: dict[tuple[str, str], int] = {}
    curated_rows = read_lines(DATA / "bigrams.txt") + read_lines(DATA / "hinglish_bigrams.txt")
    for row in curated_rows:
        first, second, f = row[0], row[1], int(row[2])
        if not usable(d, first, second):
            raise ValueError(f"bigrams.txt: {first} {second}: word not in the dictionary")
        chosen[(first, second)] = max(chosen.get((first, second), 0), f)

    candidates = [
        (int(count), first, second, int(f))
        for first, second, count, f in read_generated("bigrams.tsv")
        if usable(d, first, second)
    ]
    candidates.sort(key=lambda c: (-c[0], c[1], c[2]))
    for _, first, second, f in candidates:
        if len(chosen) >= limit:
            break
        chosen.setdefault((first, second), f)

    for (first, second), f in chosen.items():
        d.entries[first].bigrams[second] = f


# ---------------------------------------------------------------- output


def sorted_entries(d: Dictionary) -> list[Entry]:
    return sorted(d.entries.values(),
                  key=lambda e: (-e.f, -e.per_billion, e.word.lower(), e.word))


def write_combined(d: Dictionary, path: Path) -> None:
    lines = [
        f"dictionary={DICT_ID},locale={LOCALE},description={DESCRIPTION},"
        f"date={DATE},version={VERSION}"
    ]
    for e in sorted_entries(d):
        line = f" word={e.word},f={e.f}"
        if e.offensive:
            line += ",possibly_offensive=true"
        lines.append(line)
        for target, bf in sorted(e.bigrams.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"  bigram={target},f={bf}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument(
        "--report-recased",
        action="store_true",
        help="list lowercase words replaced by a capitalised curated form",
    )
    args = parser.parse_args()

    import export_keyboard

    counts = export_keyboard.export(build(select=False), args.out)
    d = build()
    write_combined(d, args.out / "en_IN.combined")
    if args.report_recased:
        for lower, word in sorted(d.recased):
            print(f"{lower} -> {word}  (f={d.entries[word].f})")
    print(f"keyboard export: {counts['words']} words, {counts['bigrams']} bigrams, "
          f"{counts['trigrams']} trigrams; AOSP word list: {len(d.entries)} words "
          f"-> {args.out}/")


if __name__ == "__main__":
    main()
