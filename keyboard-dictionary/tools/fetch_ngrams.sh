#!/usr/bin/env bash
# Regenerate data/generated/ from Google Books Ngram (2020 export, CC BY 3.0)
# and SCOWL word lists (MIT-like licence).
#
# Streams ~30 GB from storage.googleapis.com; nothing large is kept on disk
# besides the intermediate count files (~1 GB) in $WORK.
# Requires: go, python3, curl, and either apt-get (Debian/Ubuntu) or the
# SCOWL "british-english-huge"/"american-english-huge" lists in $WORK.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${WORK:-$HERE/../.work}"
B=https://storage.googleapis.com/books/ngrams/books/20200217
mkdir -p "$WORK"
cd "$WORK"

(cd "$HERE/ngramcount" && go build -o "$WORK/ngramcount" .)

if [[ ! -f british-english-huge ]]; then
  apt-get download wbritish-huge wamerican-huge
  for p in wbritish-huge wamerican-huge; do dpkg-deb -x ${p}_*.deb "$p"; done
  cp wbritish-huge/usr/share/dict/british-english-huge .
  cp wamerican-huge/usr/share/dict/american-english-huge .
fi

# 1. Unigrams: English Fiction (1 file) + British English (4 files).
[[ -s uni_fiction.tsv ]] || ./ngramcount -min 40 "$B/eng-fiction/1-00000-of-00001.gz" > uni_fiction.tsv
[[ -s uni_gb.tsv ]] || ./ngramcount -min 40 $(for i in 0 1 2 3; do echo "$B/eng-gb/1-0000$i-of-00004.gz"; done) > uni_gb.tsv

python3 "$HERE/prepare_unigrams.py" --fiction uni_fiction.tsv --gb uni_gb.tsv \
  --scowl british-english-huge american-english-huge

# 2. Bigrams: English Fiction (47 files), restricted to the chosen vocabulary.
cp "$HERE/.vocab_forms.txt" vocab.txt
printf "'s\n'm\n're\n'll\n've\n'd\nnot\nca\nwo\nai\n" >> vocab.txt
[[ -s bi_fiction.tsv ]] || ./ngramcount -min 100 -vocab vocab.txt \
  $(for i in $(seq 0 46); do printf "$B/eng-fiction/2-%05d-of-00047.gz " "$i"; done) > bi_fiction.tsv

python3 "$HERE/prepare_bigrams.py" --bigrams bi_fiction.tsv --fiction-unigrams uni_fiction.tsv
echo "data/generated/ updated; now run: python3 build.py"
