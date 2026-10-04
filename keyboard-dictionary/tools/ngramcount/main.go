// ngramcount streams Google Books Ngram (2020 export) files and sums the
// match counts of each n-gram over a year range.
//
// Usage:
//
//	ngramcount -from 1990 -min 40 [-vocab words.txt] URL... > counts.tsv
//
// Each URL is a gzipped export file such as
// https://storage.googleapis.com/books/ngrams/books/20200217/eng-fiction/1-00000-of-00001.gz
// Files are fetched and decompressed concurrently and never stored on disk.
//
// N-grams carrying part-of-speech tags (any token containing "_") are
// skipped; only the untagged surface forms are counted. With -vocab, every
// token of an n-gram must appear (case-sensitively) in the vocabulary file.
//
// Output: "ngram<TAB>count" for each n-gram whose summed count >= -min,
// in no particular order.
package main

import (
	"bufio"
	"bytes"
	"compress/gzip"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

func main() {
	from := flag.Int("from", 1990, "first year to count (inclusive)")
	to := flag.Int("to", 2019, "last year to count (inclusive)")
	minCount := flag.Int64("min", 40, "drop n-grams with fewer matches")
	vocabPath := flag.String("vocab", "", "optional file with one allowed token per line")
	workers := flag.Int("j", 4, "files processed concurrently")
	flag.Parse()

	var vocab map[string]struct{}
	if *vocabPath != "" {
		var err error
		if vocab, err = readVocab(*vocabPath); err != nil {
			fail(err)
		}
	}

	urls := make(chan string)
	results := make(chan map[string]int64)
	var wg sync.WaitGroup
	for i := 0; i < *workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for u := range urls {
				counts, err := processWithRetry(u, *from, *to, *minCount, vocab)
				if err != nil {
					fail(fmt.Errorf("%s: %w", u, err))
				}
				results <- counts
			}
		}()
	}
	go func() {
		for _, u := range flag.Args() {
			urls <- u
		}
		close(urls)
		wg.Wait()
		close(results)
	}()

	// Export files are sharded by n-gram, so an n-gram never spans two
	// files; results can be written as they arrive.
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()
	done := 0
	for counts := range results {
		for ngram, c := range counts {
			fmt.Fprintf(out, "%s\t%d\n", ngram, c)
		}
		done++
		fmt.Fprintf(os.Stderr, "ngramcount: %d/%d files done\n", done, flag.NArg())
	}
}

func readVocab(path string) (map[string]struct{}, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	vocab := make(map[string]struct{})
	for _, line := range strings.Split(string(data), "\n") {
		if line = strings.TrimSpace(line); line != "" {
			vocab[line] = struct{}{}
		}
	}
	return vocab, nil
}

func processWithRetry(url string, from, to int, minCount int64, vocab map[string]struct{}) (map[string]int64, error) {
	var err error
	for attempt, wait := 0, 2*time.Second; attempt < 5; attempt, wait = attempt+1, wait*2 {
		var counts map[string]int64
		if counts, err = process(url, from, to, minCount, vocab); err == nil {
			return counts, nil
		}
		fmt.Fprintf(os.Stderr, "ngramcount: %s: %v (retrying in %s)\n", url, err, wait)
		time.Sleep(wait)
	}
	return nil, err
}

func process(url string, from, to int, minCount int64, vocab map[string]struct{}) (map[string]int64, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP %s", resp.Status)
	}
	gz, err := gzip.NewReader(bufio.NewReaderSize(resp.Body, 4<<20))
	if err != nil {
		return nil, err
	}
	r := bufio.NewReaderSize(gz, 4<<20)

	counts := make(map[string]int64)
	for {
		line, err := r.ReadSlice('\n')
		if err == bufio.ErrBufferFull {
			// Pathologically long line: skip the rest of it.
			for err == bufio.ErrBufferFull {
				_, err = r.ReadSlice('\n')
			}
			continue
		}
		if len(line) > 0 {
			if ngram, c := parseLine(line, from, to, vocab); c >= minCount {
				counts[ngram] = c
			}
		}
		if err == io.EOF {
			return counts, nil
		}
		if err != nil {
			return nil, err
		}
	}
}

// parseLine handles "ngram\tyear,matches,volumes\tyear,matches,volumes...".
func parseLine(line []byte, from, to int, vocab map[string]struct{}) (string, int64) {
	line = bytes.TrimRight(line, "\r\n")
	tab := bytes.IndexByte(line, '\t')
	if tab <= 0 {
		return "", 0
	}
	ngram := line[:tab]
	if bytes.IndexByte(ngram, '_') >= 0 {
		return "", 0
	}
	if vocab != nil {
		for _, tok := range bytes.Split(ngram, []byte{' '}) {
			if _, ok := vocab[string(tok)]; !ok {
				return "", 0
			}
		}
	}
	var total int64
	for rest := line[tab+1:]; len(rest) > 0; {
		field := rest
		if i := bytes.IndexByte(rest, '\t'); i >= 0 {
			field, rest = rest[:i], rest[i+1:]
		} else {
			rest = nil
		}
		parts := bytes.SplitN(field, []byte{','}, 3)
		if len(parts) < 2 {
			continue
		}
		year, err := strconv.Atoi(string(parts[0]))
		if err != nil || year < from || year > to {
			continue
		}
		n, err := strconv.ParseInt(string(parts[1]), 10, 64)
		if err == nil {
			total += n
		}
	}
	return string(ngram), total
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, "ngramcount:", err)
	os.Exit(1)
}
