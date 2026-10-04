# English (India) keyboard dictionary

An `en_IN` word list for Android keyboards built on AOSP LatinIME (HeliBoard,
OpenBoard, AOSP forks and similar). It contains:

- **Core English**: about 47k words ranked by how often they are used.
  Frequencies come from OpenSubtitles 2018, which is close to how people type
  in chat.
- **Indian spelling**: British spellings rank first (`colour`, `organise`,
  `travelling`). The US spelling stays in the list at a lower rank.
- **Indian English words**: `lakh`, `crore`, `prepone`, `timepass`, `jugaad`,
  Aadhaar/UPI/GST, food, clothing, festivals, cricket and Indian languages.
- **Indian names and places**: states, union territories, about 200 cities and
  neighbourhoods, rivers, landmarks, and common first names and surnames.
- **Hinglish**: romanised Hindi such as `kya`, `hai`, `nahi`/`nahin`/`nhi`,
  `accha`/`achha`, `yaar`. These words rank below everyday English, so they
  never push an English suggestion aside.
- **Contractions**: `don't`, `I'm`, `you're` and so on, properly capitalised
  (`I`, `Monday`, `India`).
- **Bigrams**: common word pairs such as `happy Diwali`, `Eid Mubarak`,
  `Tamil Nadu`, `kaise ho`.
- **Offensive words**: flagged with `possibly_offensive=true` and set to
  frequency 0, so they are hidden when "Block offensive words" is on.

## Layout

```
build.py                 build script (Python 3.9+, standard library only)
data/
  exclude.txt            junk tokens removed from the base list
  capitalize.txt         English proper nouns that are always capitalised
  keep_lowercase.txt     ordinary words that also exist as names (will, west, ...)
  contractions.txt       don't, I'm, ... (@frag uses the base frequency of the fragment)
  spelling_gb.tsv        US -> British spelling pairs
  indian_english.txt     Indian English terms, acronyms, food, festivals, languages
  places.txt             states, cities, rivers, landmarks
  names.txt              Indian first names and surnames
  hinglish.txt           romanised Hindi/Urdu
  offensive.txt          words to flag as offensive
  bigrams.txt            word pairs: first second frequency
output/
  en_IN.combined         AOSP source word list (compile this into a .dict)
  en_IN.tsv              word / frequency / offensive, for custom keyboards
tests/                   pytest suite (runs offline against a small fixture)
```

## Building

```sh
cd keyboard-dictionary
python3 build.py                        # downloads and caches the base list, then writes output/
python3 build.py --report-recased       # also lists lowercase words that were replaced by a capitalised form
python3 -m pytest -q tests
```

The base list is downloaded once into `.cache/` and its sha256 is checked. Run
the tests after editing anything in `data/`. They fail if the committed
`output/` no longer matches a fresh build.

### Editing the lists

Curated files (`indian_english.txt`, `places.txt`, `names.txt`,
`hinglish.txt`) hold words separated by whitespace, and `#` starts a comment.

- A line `@@ 150` sets the default frequency (0–255) for the lines below it.
- A single word can override its frequency with `word=160`.

How frequencies are merged:

- A curated word that is already in the base list keeps the higher of the two
  frequencies.
- A capitalised word (`Delhi`) replaces its lowercase base entry (`delhi`).
  There are two exceptions:
  - Acronyms (`PIN`) never replace the lowercase word.
  - Words listed in `keep_lowercase.txt` are kept in lowercase too.

  In both cases the capitalised form ranks just below the lowercase word.

After editing, bump `VERSION` in `build.py` (and `DATE` if you like) so
keyboards pick up the new dictionary.

## Compiling to a binary `.dict`

Android keyboards load the binary format, not the `.combined` text. Compile it
with AOSP's `dicttool`. A prebuilt `dicttool_aosp.jar` is distributed with the
HeliBoard dictionaries project (`codeberg.org/Helium314/aosp-dictionaries`), or
you can build `tools/dicttool` from AOSP LatinIME yourself:

```sh
java -jar dicttool_aosp.jar makedict -s output/en_IN.combined -d output/main_en_IN.dict
```

The build environment used for this commit could not download or run
`dicttool`, so `main_en_IN.dict` is not included. Run the command above
locally.

## Using it

- **HeliBoard / OpenBoard**: go to Settings → Languages & Layouts → English
  (India) → Dictionary → Add dictionary, then pick `main_en_IN.dict`.
- **Your own LatinIME-based keyboard**: put the file at
  `app/src/main/res/raw/main_en_in.dict`, or load it from storage through
  `BinaryDictionary`.
- **A fully custom keyboard**: load `output/en_IN.tsv` into a trie or SQLite
  table. Rank completions by `frequency`, and skip rows where `offensive` is 1
  unless the user has opted in.

## License

The base frequencies come from
[hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords),
which is derived from OpenSubtitles and licensed **CC-BY-SA 4.0**. The
generated word list (`output/`) is a derivative work and is distributed under
CC-BY-SA 4.0 as well. If you ship it in your app, include this attribution.
