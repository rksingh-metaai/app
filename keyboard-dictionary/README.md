# English (India) keyboard dictionary

A production `en_IN` dictionary for Android keyboards built on AOSP LatinIME
(HeliBoard, OpenBoard, AOSP forks and similar keyboards). Every source allows
commercial use.

| | |
|---|---|
| Words | 165,113 |
| Next-word predictions (bigrams) | 432,933 |
| 3-word predictions (trigrams) | 4,842,972 (`output/en_IN_trigrams.tsv.gz`) |
| Spelling | British/Indian forms rank first, and US forms are kept |
| Licence | CC BY 3.0 attribution plus the SCOWL notice (see [Licences](#licences)) |

## What's inside

- **General English vocabulary.** It comes from Google Books Ngram (2020
  export, books published 1990–2019).
  - **Frequencies** mix *English Fiction*, which is mostly dialogue and
    closest to how people type (60% weight), with *British English*, whose
    spelling Indian English follows (40% weight).
  - **Spelling check.** Every word must appear in SCOWL (spell-checker word
    lists), or be common enough to be real slang (`gonna`, `okay`). Typos and
    scanning errors are therefore dropped.
  - **Casing comes from usage.** `India` is almost always capitalised, so
    only `India` is kept. `bill` and `Bill` are both common, so both are kept.
- **Next-word predictions.** These are word pairs counted from 25 GB of
  English Fiction 2-grams. The 5k most common words get up to 12 predictions
  each, with fewer for rarer words.
- **3-word predictions (trigrams).** These predict the next word from the
  previous two (`I'm going → to`, `one of → the`, `thank you → for`). They
  are counted from about 220 GB of English Fiction 3-grams, keeping the 5 best
  next words for each two-word context. Standard AOSP/HeliBoard `.dict` files
  only use bigrams, so trigrams ship as a separate TSV for keyboards with
  their own prediction engine.
- **Contractions** (`don't`, `I'm`, `you're` and so on). The source text
  splits them into separate words, so their frequencies are reconstructed from
  the word pairs. They also get their own predictions (`I'm going`,
  `don't know`).
- **Indian layers, curated by hand.** These words get minimum frequencies
  because Indian users type them far more often than books suggest:
  - Indian English: `lakh`, `crore`, `prepone`, Aadhaar/UPI/GST, food,
    clothing, festivals, cricket and languages.
  - About 1,000 places: states, union territories, district headquarters,
    city neighbourhoods, rivers and landmarks.
  - About 1,000 Indian first names and surnames.
  - About 900 Hinglish (romanised Hindi) words, with spelling variants
    (`nahi`/`nahin`/`nhi`, `accha`/`achha`/`acha`). These rank below everyday
    English.
  - Chat and tech words that books under-represent: `okay`, `thanks`,
    `lol`, `OTP`, `WhatsApp`, `selfie` and so on.
  - Hand-picked word pairs: `happy Diwali`, `Eid Mubarak`, `Tamil Nadu`,
    `kaise ho` and so on.
- **Offensive words**, including slurs and romanised Hindi abuse. They are
  flagged `possibly_offensive=true` with frequency 0. They stay in the
  dictionary so that typing them isn't "corrected", but they are never
  suggested while "Block offensive words" is on. They are also never used as
  predictions.

## Layout

```
build.py                    assembles output/ from data/ (Python 3.9+, stdlib only, offline)
data/
  generated/unigrams.tsv    base vocabulary, per-billion frequency     (from tools/)
  generated/bigrams.tsv     next-word predictions, AOSP 0-255 scale    (from tools/)
  generated/contractions.tsv contraction frequencies                   (from tools/)
  generated/trigrams.tsv.gz 3-word predictions, AOSP 0-255 scale (gzip, from tools/)
  contractions.txt          contraction -> split pair mapping used by tools/
  spelling_gb.tsv           US -> British spelling pairs
  indian_english.txt        Indian English terms, acronyms, food, festivals, languages
  places.txt                states, cities, district HQs, neighbourhoods, landmarks
  names.txt                 Indian first names and surnames
  hinglish.txt              romanised Hindi/Urdu
  modern.txt                chat / tech / app words (okay, lol, OTP, WhatsApp)
  extra_words.txt           lowercase words allowed although SCOWL lacks them
  keep_lowercase.txt        ordinary words that also exist as names (will, west, ...)
  offensive.txt             words to flag as offensive
  exclude.txt               words to drop from the generated vocabulary
  bigrams.txt               hand-written word pairs
output/
  en_IN.combined            AOSP source word list -> compile to .dict
  en_IN.tsv                 word / frequency / offensive (for custom engines)
  en_IN_bigrams.tsv         word / next / frequency       (for custom engines)
  en_IN_trigrams.tsv.gz     word1 / word2 / next / frequency (gzip; custom engines only)
tools/
  fetch_ngrams.sh           regenerates data/generated/ (streams ~250 GB)
  ngramcount/               Go streamer that sums n-gram counts over years
  prepare_unigrams.py       vocabulary selection, casing and SCOWL validation
  prepare_bigrams.py        predictions and contraction reconstruction
  prepare_trigrams.py       3-word predictions
tests/                      pytest suite
```

## Building

```sh
cd keyboard-dictionary
python3 build.py              # writes output/ (takes a few seconds, works offline)
python3 -m pytest -q tests
```

To regenerate the frequency data from scratch (a few hours, needs Go
and network access):

```sh
tools/fetch_ngrams.sh && python3 build.py
```

### Editing the curated lists

In the curated files, words are separated by whitespace and `#` starts a
comment.

- A line `@@ 150` sets the minimum frequency (0–255) for the lines below it.
- A single word can override its frequency with `word=160`.

How frequencies are merged:

- A curated word keeps the higher of its curated and data-derived frequency.
- A capitalised curated word (`Delhi`) replaces its lowercase entry
  (`delhi`). There are two exceptions:
  - Acronyms (`PIN`) never replace the lowercase word.
  - Words listed in `keep_lowercase.txt` are kept in lowercase too.

  In both cases the capitalised form ranks just below the lowercase word.

After any change, bump `VERSION` in `build.py` so installed keyboards pick up
the update, then run the tests.

**Size:** to ship a smaller dictionary, lower `MAX_WORDS` in
`tools/prepare_unigrams.py`, or `K_BY_RANK` in `tools/prepare_bigrams.py` for
fewer predictions, then rerun them. The rarest words carry low frequencies,
so they are suggested only on a near-exact match.

**Frequency scale:** f = 33 × log10(occurrences per billion words) − 5.7.
For example, `the` is about 250, `India` about 151, and a word seen 6 times
per billion is about 20.

## Compiling to a binary `.dict`

Android keyboards load the binary format. Compile it with AOSP's `dicttool`,
either the prebuilt `dicttool_aosp.jar` from the HeliBoard dictionaries
project or one built from `tools/dicttool` in AOSP LatinIME:

```sh
java -jar dicttool_aosp.jar makedict -s output/en_IN.combined -d main_en_in.dict
```

Then use the file in one of these ways:

- **HeliBoard / OpenBoard**: go to Settings → Languages & Layouts → English
  (India) → Dictionary → Add dictionary.
- **Your own LatinIME fork**: put it at `app/src/main/res/raw/main_en_in.dict`.
- **A custom engine**: load `output/en_IN.tsv`, `output/en_IN_bigrams.tsv`
  and `output/en_IN_trigrams.tsv.gz` (gunzip first) into a trie or SQLite. To predict, look up
  the last two words in the trigrams first, fall back to the last word in the
  bigrams, then fall back to word frequency. Skip rows where `offensive` is 1 unless the user has
  opted in.

## Licences

The dictionary is built only from sources that allow commercial use:

- **Google Books Ngram Viewer datasets** (2020 export) are licensed under
  [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). Include this
  attribution in your app's open-source notices: *"Word frequencies derived
  from the Google Books Ngram dataset (Google, 2020), CC BY 3.0."*
- **SCOWL** (Spell Checker Oriented Word Lists) © Kevin Atkinson and
  contributors. It is used only to validate spellings. Its MIT-like licence
  requires its copyright notice, which is reproduced in
  [`LICENSES/SCOWL.txt`](LICENSES/SCOWL.txt).
- **The curated Indian lists, spelling pairs, contraction rules and tools**
  were written for this project and belong to it.

This is not legal advice. Have your counsel review the licences before you
ship.
