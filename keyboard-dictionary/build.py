#!/usr/bin/env python3
"""Build an English (India) dictionary for AOSP-based Android keyboards.

Pipeline:
  1. Base English word frequencies (OpenSubtitles 2018 top-50k, CC-BY-SA 4.0).
  2. Clean-up: drop tokenizer fragments / junk, fix capitalisation.
  3. Indian spelling preferences (British forms preferred: colour, organise).
  4. Curated layers: Indian English terms, places, names, Hinglish, contractions.
  5. Flag offensive words, attach curated bigrams.
  6. Write AOSP combined wordlist (output/en_IN.combined) + a TSV.

Compile the .combined file to a binary .dict with AOSP dicttool (see README).

Usage:
  python3 build.py                 # downloads + caches base list, builds output/
  python3 build.py --base FILE     # use a local "word count" frequency file
"""

from __future__ import annotations

import argparse
import hashlib
import math
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CACHE = ROOT / ".cache"
OUTPUT = ROOT / "output"

BASE_URL = (
    "https://raw.githubusercontent.com/hermitdave/FrequencyWords/"
    "master/content/2018/en/en_50k.txt"
)
BASE_SHA256 = "5351ff405b1126ef555791dd4d9798a48e3e9a501a9fc481a9da957752cfb458"

# Dictionary header. Bump VERSION whenever the word list changes; DATE is kept
# fixed per version so builds are reproducible.
DICT_ID = "main:en_in"
LOCALE = "en_IN"
DESCRIPTION = "English (India)"
VERSION = 1
DATE = 1791072000  # 2026-10-04 00:00 UTC

# AOSP unigram frequencies are 0..255. Base words are log-scaled into this band.
F_MAX = 250
F_MIN = 15
# Offensive words stay in the dictionary (so they aren't "corrected" into
# something else) but are flagged and pushed down; keyboards hide them when
# "block offensive words" is on.
F_OFFENSIVE = 0
# British spelling is preferred; the US variant is kept but ranked below it.
US_VARIANT_PENALTY = 40
# A capitalised/acronym form kept next to an ordinary lowercase word ranks
# this much below it ("West" < "west", "PIN" < "pin").
CASED_VARIANT_GAP = 10

BASE_WORD_RE = re.compile(r"^[a-z]+$")
CURATED_WORD_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9'.\-]*$")


@dataclass
class Entry:
    word: str
    f: int
    offensive: bool = False
    curated: bool = False  # came from a hand-curated list, never auto-removed
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


# ---------------------------------------------------------------- base list


def fetch_base() -> Path:
    CACHE.mkdir(exist_ok=True)
    path = CACHE / "en_50k.txt"
    if not path.exists():
        print(f"Downloading {BASE_URL}", file=sys.stderr)
        with urllib.request.urlopen(BASE_URL, timeout=60) as resp:
            path.write_bytes(resp.read())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != BASE_SHA256:
        raise SystemExit(f"{path}: sha256 mismatch ({digest}); delete it and retry")
    return path


def load_counts(path: Path) -> dict[str, int]:
    """Raw `word count` lines, unfiltered."""
    counts: dict[str, int] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        parts = raw.split()
        if len(parts) == 2:
            counts[parts[0]] = counts.get(parts[0], 0) + int(parts[1])
    return counts


def filter_base(counts: dict[str, int], exclude: set[str]) -> dict[str, int]:
    return {
        word: count
        for word, count in counts.items()
        if BASE_WORD_RE.match(word)
        and word not in exclude
        and (len(word) > 1 or word in ("a", "i"))
    }


def scale(counts: dict[str, int]) -> dict[str, int]:
    hi = math.log(max(counts.values()))
    lo = math.log(min(counts.values()))
    span = (hi - lo) or 1.0
    return {
        w: round(F_MIN + (F_MAX - F_MIN) * (math.log(c) - lo) / span)
        for w, c in counts.items()
    }


# ---------------------------------------------------------------- build


class Dictionary:
    def __init__(self) -> None:
        self.entries: dict[str, Entry] = {}
        self.recased: list[tuple[str, str]] = []  # (removed lowercase, kept form)

    def get(self, word: str) -> Entry | None:
        return self.entries.get(word)

    def put(self, word: str, f: int, curated: bool = False) -> Entry:
        """Add `word`, keeping the higher frequency if it already exists."""
        entry = self.entries.get(word)
        if entry is None:
            entry = self.entries[word] = Entry(word, f)
        else:
            entry.f = max(entry.f, f)
        entry.curated |= curated
        return entry

    def recase(self, word: str, f: int, keep_lowercase: set[str]) -> int:
        """Add the properly cased `word`, merging it with a lowercase entry.

        Normally the lowercase base entry ("delhi") is replaced and its
        frequency inherited. It is kept instead when it is ordinary English
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
            f = max(0, min(f, entry.f - CASED_VARIANT_GAP))
            return self.put(word, f, curated=True).f
        del self.entries[lower]
        self.recased.append((lower, word))
        return self.put(word, max(f, entry.f), curated=True).f


def build(base_path: Path) -> Dictionary:
    exclude = read_wordset("exclude.txt")
    keep_lowercase = read_wordset("keep_lowercase.txt")
    offensive = {w.lower() for w in read_wordset("offensive.txt")}

    raw_counts = load_counts(base_path)
    d = Dictionary()
    for word, f in scale(filter_base(raw_counts, exclude)).items():
        d.put(word, f)

    # Proper-case common English proper nouns (I, Monday, January, English…).
    # Only words present in the base list are recased.
    for word in sorted(read_wordset("capitalize.txt")):
        base = d.get(word.lower())
        if base:
            d.recase(word, base.f, keep_lowercase)

    # Contractions: "@fragment" borrows the frequency of the split-off token
    # from the base list (subtitles tokenise "don't" as "don" + "'t").
    scaled_raw = scale(raw_counts)
    for row in read_lines(DATA / "contractions.txt"):
        word, spec = row[0], row[1]
        f = scaled_raw.get(spec[1:], 0) if spec.startswith("@") else int(spec)
        if f:
            d.put(word, f, curated=True)

    # Indian English follows British spelling: "colour" outranks "color".
    for us, gb in read_lines(DATA / "spelling_gb.tsv"):
        us_entry, gb_entry = d.get(us), d.get(gb)
        top = max(e.f for e in (us_entry, gb_entry) if e) if (us_entry or gb_entry) else 0
        if not top:
            continue
        d.put(gb, top)
        if us_entry:
            us_entry.f = max(F_MIN, min(us_entry.f, top - US_VARIANT_PENALTY))

    # Curated Indian layers. Default frequencies are the fallback when the
    # word isn't already more frequent in the base list.
    for name, default_f in (
        ("indian_english.txt", 140),
        ("places.txt", 130),
        ("names.txt", 115),
        ("hinglish.txt", 105),
    ):
        for word, f in read_curated(name, default_f):
            d.recase(word, f, keep_lowercase)

    for word, entry in d.entries.items():
        if word.lower() in offensive:
            entry.offensive = True
            entry.f = F_OFFENSIVE

    for row in read_lines(DATA / "bigrams.txt"):
        first, second, f = row[0], row[1], int(row[2])
        for w in (first, second):
            if w not in d.entries:
                raise ValueError(f"bigrams.txt: {w!r} is not in the dictionary")
        d.entries[first].bigrams[second] = f

    return d


# ---------------------------------------------------------------- output


def sorted_entries(d: Dictionary) -> list[Entry]:
    return sorted(d.entries.values(), key=lambda e: (-e.f, e.word.lower(), e.word))


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


def write_tsv(d: Dictionary, path: Path) -> None:
    rows = ["word\tfrequency\toffensive"]
    rows += [f"{e.word}\t{e.f}\t{int(e.offensive)}" for e in sorted_entries(d)]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", type=Path, help="local 'word count' frequency file")
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument(
        "--report-recased",
        action="store_true",
        help="list lowercase base words replaced by a capitalised form",
    )
    args = parser.parse_args()

    d = build(args.base or fetch_base())
    args.out.mkdir(parents=True, exist_ok=True)
    write_combined(d, args.out / "en_IN.combined")
    write_tsv(d, args.out / "en_IN.tsv")
    if args.report_recased:
        for lower, word in sorted(d.recased):
            print(f"{lower} -> {word}  (base f={d.entries[word].f})")
    bigrams = sum(len(e.bigrams) for e in d.entries.values())
    print(f"{len(d.entries)} words, {bigrams} bigrams -> {args.out}/en_IN.combined")


if __name__ == "__main__":
    main()
