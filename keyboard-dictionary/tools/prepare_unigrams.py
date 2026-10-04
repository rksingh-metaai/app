#!/usr/bin/env python3
"""Select the base vocabulary from Google Books Ngram unigram counts.

Inputs (produced by tools/fetch_ngrams.sh):
  uni_fiction.tsv, uni_gb.tsv   "token<TAB>count" (case-sensitive, 1990-2019)
  SCOWL word lists              british-english-huge, american-english-huge

Output: data/generated/unigrams.tsv  "word<TAB>per_billion" (whole number,
        occurrences per billion words; sorted, descending)
and     tools/.vocab_forms.txt  every surface form (all casings) that maps to
        a selected word; used to filter the bigram pass (not committed).

Selection rules
  * Tokens are words: letters with optional inner apostrophes or hyphens.
  * Frequencies are a weighted mix of English Fiction (closest to chat
    style) and British English (Indian English follows British spelling).
  * Words in SCOWL are accepted above a low frequency floor; words not in
    SCOWL (slang, new coinages, brand names) need a much higher frequency.
  * Casing comes from usage: "india" is almost always written "India", so
    only "India" is kept; "bill" is mostly lowercase, so "bill" is kept and
    "Bill" only if SCOWL lists it as a name and it is common in its own right.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "data" / "generated"

WORD_RE = re.compile(r"^[A-Za-z]+(?:['\-][A-Za-z]+)*$")

WEIGHTS = {"fiction": 0.9, "gb": 0.1}
# Per-billion floors. SCOWL words are trusted; the rest must be common.
FLOOR_SCOWL = 6.0
FLOOR_OTHER = 150.0
# A capitalised form must carry this share of its group to be kept when the
# lowercase word is also valid ("Will" the name vs "will").
CASED_SHARE_WITH_LOWER = 0.6
# Without a valid lowercase word, the dominant cased form must have this
# share (filters sentence-initial noise such as "Unto").
CASED_SHARE_ALONE = 0.5
# A lowercase word next to a kept cased form needs at least this share.
MIN_LOWER_SHARE = 0.05
MAX_WORDS = 220_000


def load_counts(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            token, _, count = line.rstrip("\n").rpartition("\t")
            if token and WORD_RE.match(token):
                counts[token] = counts.get(token, 0) + int(count)
    return counts


def load_scowl(paths: list[Path]) -> set[str]:
    words: set[str] = set()
    for path in paths:
        for line in path.read_text(encoding="latin-1").splitlines():
            line = line.strip()
            if line and WORD_RE.match(line):
                words.add(line)
    return words


def mix(corpora: dict[str, dict[str, int]]) -> dict[str, float]:
    """Weighted per-billion frequency across corpora."""
    mixed: dict[str, float] = defaultdict(float)
    for name, counts in corpora.items():
        total = sum(counts.values())
        for token, c in counts.items():
            mixed[token] += WEIGHTS[name] * c * 1e9 / total
    return mixed


def select(mixed: dict[str, float], scowl: set[str], allow: set[str]) -> dict[str, float]:
    scowl_lower_entries = {w for w in scowl if w.islower()}
    groups: dict[str, dict[str, float]] = defaultdict(dict)
    for token, f in mixed.items():
        groups[token.lower()][token] = f

    chosen: dict[str, float] = {}
    for lower, forms in groups.items():
        total = sum(forms.values())
        lower_f = forms.get(lower, 0.0)
        # SCOWL already covers modern slang (gonna, selfie, googled); other
        # lowercase tokens are OCR noise ("litde", "ofthe"), dialect spellings
        # ("goin") or foreign words ("vous"), so only the allowlist gets in.
        lower_valid = lower in scowl_lower_entries or lower in allow
        floor = FLOOR_SCOWL if (lower in scowl_lower_entries or lower in allow or
                                any(f in scowl for f in forms)) else FLOOR_OTHER
        if total < floor:
            continue

        kept_cased: dict[str, float] = {}
        for form, f in forms.items():
            if form == lower:
                continue
            share = f / total
            if lower_valid:
                ok = form in scowl and share >= CASED_SHARE_WITH_LOWER
            else:
                # Names outside SCOWL (Maddie, Rhys) are fine; unknown
                # acronyms (ISSN, HMSO) are mostly bibliography noise.
                ok = share >= CASED_SHARE_ALONE and (
                    form in scowl
                    or (len(form) >= 3 and not form.isupper() and total >= FLOOR_OTHER)
                )
            if ok:
                kept_cased[form] = f

        if lower_valid:
            # Sentence-initial capitals of a lowercase word belong to it.
            rest = total - sum(kept_cased.values())
            if kept_cased and (lower_f / total < MIN_LOWER_SHARE or rest < floor):
                lower_valid = False  # e.g. "i": nearly always written "I"
            else:
                chosen[lower] = rest
        if kept_cased:
            best = max(kept_cased, key=kept_cased.get)
            if lower_valid:
                chosen.update(kept_cased)
            else:
                # Only one cased spelling; it inherits the group's weight.
                chosen[best] = total
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--fiction", type=Path, required=True)
    parser.add_argument("--gb", type=Path, required=True)
    parser.add_argument("--scowl", type=Path, nargs="+", required=True)
    args = parser.parse_args()

    corpora = {"fiction": load_counts(args.fiction), "gb": load_counts(args.gb)}
    mixed = mix(corpora)
    allow = {
        w
        for line in (ROOT / "data" / "extra_words.txt").read_text(encoding="utf-8").splitlines()
        for w in line.split("#", 1)[0].split()
    }
    chosen = select(mixed, load_scowl(args.scowl), allow)
    ranked = sorted(chosen.items(), key=lambda kv: (-kv[1], kv[0]))[:MAX_WORDS]

    GENERATED.mkdir(parents=True, exist_ok=True)
    with (GENERATED / "unigrams.tsv").open("w", encoding="utf-8") as out:
        out.write("# word\tper_billion  (Google Books Ngram 2020, fiction+GB, 1990-2019)\n")
        for word, f in ranked:
            out.write(f"{word}\t{round(f)}\n")

    selected = {w.lower() for w, _ in ranked}
    forms = sorted(t for t in mixed if t.lower() in selected)
    (GENERATED.parent.parent / "tools" / ".vocab_forms.txt").write_text(
        "\n".join(forms) + "\n", encoding="utf-8"
    )
    print(f"{len(ranked)} words; lowest kept per-billion {ranked[-1][1]:.2f}; "
          f"{len(forms)} surface forms for the bigram pass")


if __name__ == "__main__":
    main()
