#!/usr/bin/env python3
"""Offline stand-in for the keyboard's prediction metrics.

Simulates a typical keyboard on real conversational text and reports:
  * next-word accuracy (top-1 / top-3) before any letter is typed;
  * keystrokes saved when the user taps a suggestion as soon as the word
    appears among 3 suggestions while typing.

Prediction: candidates from the trigram context (last two words) first,
then the bigram context (last word), then the word list, each ranked by its
frequency; while typing, candidates are filtered by the typed prefix.

Test text (not shipped, evaluation only), from NLTK's data repository:
webtext/overheard.txt (overheard conversations) and the NPS chat corpus.

Usage:
  python3 tools/evaluate.py WORDS BIGRAMS TRIGRAMS [--text DIR]
"""

from __future__ import annotations

import argparse
import io
import re
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

NLTK = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/"
TOKEN_RE = re.compile(r"[a-z]+(?:'[a-z]+)?")
SUGGESTIONS = 3


def fetch_text(cache: Path) -> list[list[str]]:
    """Utterances as lowercase token lists."""
    cache.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for corpus in ("webtext", "nps_chat"):
        zpath = cache / f"{corpus}.zip"
        if not zpath.exists():
            with urllib.request.urlopen(NLTK + f"{corpus}.zip", timeout=60) as r:
                zpath.write_bytes(r.read())
        with zipfile.ZipFile(zpath) as z:
            for name in z.namelist():
                if corpus == "webtext" and name.endswith("overheard.txt"):
                    for line in io.TextIOWrapper(z.open(name), encoding="latin-1"):
                        # drop the "Speaker:" label
                        lines.append(line.split(":", 1)[-1])
                elif corpus == "nps_chat" and name.endswith(".xml"):
                    xml = z.read(name).decode("latin-1")
                    # post text precedes its <terminals> annotation
                    for cls, text in re.findall(r'<Post class="([^"]+)"[^>]*>([^<]*)', xml):
                        if cls != "System":
                            text = re.sub(r"&[a-z]+;", " ", text)
                            # anonymised user names, e.g. "10-19-20sUser7"
                            lines.append(re.sub(r"\S*user\d*\S*", " ", text, flags=re.I))
    utterances = []
    for line in lines:
        line = line.lower().replace("’", "'")
        toks = TOKEN_RE.findall(line)
        if len(toks) >= 2:
            utterances.append(toks)
    return utterances


def load(path: Path, n: int) -> dict[tuple, int]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        out[tuple(parts[:n])] = int(parts[n])
    return out


class Model:
    def __init__(self, words: dict, bigrams: dict, trigrams: dict) -> None:
        self.freq = {k[0]: v for k, v in words.items()}
        self.bi: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for (a, b), v in bigrams.items():
            self.bi[a].append((b, v))
        self.tri: dict[tuple[str, str], list[tuple[str, int]]] = defaultdict(list)
        for (a, b, c), v in trigrams.items():
            self.tri[(a, b)].append((c, v))
        for d in (self.bi, self.tri):
            for k in d:
                d[k].sort(key=lambda x: -x[1])
        # Top words for every prefix (word-list fallback while typing).
        ranked = sorted(self.freq, key=lambda w: -self.freq[w])
        self.prefix: dict[str, list[str]] = defaultdict(list)
        for w in ranked:
            for i in range(0, len(w) + 1):
                lst = self.prefix[w[:i]]
                if len(lst) < SUGGESTIONS:
                    lst.append(w)

    def suggest(self, prev2: str | None, prev1: str | None, prefix: str) -> list[str]:
        out: list[str] = []
        sources = []
        if prev2 and prev1:
            sources.append(self.tri.get((prev2, prev1), ()))
        if prev1:
            sources.append(self.bi.get(prev1, ()))
        for src in sources:
            for w, _ in src:
                if w.startswith(prefix) and w not in out:
                    out.append(w)
                    if len(out) == SUGGESTIONS:
                        return out
        for w in self.prefix.get(prefix, ()):
            if w not in out:
                out.append(w)
                if len(out) == SUGGESTIONS:
                    break
        return out


def evaluate(model: Model, utterances: list[list[str]]) -> dict[str, float]:
    top1 = top3 = n = 0
    typed = cost = 0
    for toks in utterances:
        for i, w in enumerate(toks):
            p2 = toks[i - 2] if i >= 2 else None
            p1 = toks[i - 1] if i >= 1 else None
            if i >= 1:
                s = model.suggest(p2, p1, "")
                n += 1
                top1 += bool(s) and s[0] == w
                top3 += w in s
            # keystrokes: letters + space; a tap inserts word + space
            full = len(w) + 1
            spent = full
            for k in range(0, len(w)):
                if w in model.suggest(p2, p1, w[:k]):
                    spent = k + 1
                    break
            typed += full
            cost += spent
    return {"top1": 100 * top1 / n, "top3": 100 * top3 / n,
            "saved": 100 * (1 - cost / typed)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("words", type=Path)
    parser.add_argument("bigrams", type=Path)
    parser.add_argument("trigrams", type=Path)
    parser.add_argument("--text", type=Path, default=Path(__file__).resolve().parents[1] / ".work" / "eval")
    args = parser.parse_args()
    text = fetch_text(args.text)
    model = Model(load(args.words, 1), load(args.bigrams, 2), load(args.trigrams, 3))
    r = evaluate(model, text)
    print(f"next word top-1 {r['top1']:.1f}%  top-3 {r['top3']:.1f}%  "
          f"keystrokes saved {r['saved']:.1f}%  ({sum(map(len, text))} words)")


if __name__ == "__main__":
    main()
