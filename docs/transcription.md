# The ETCBC Targum Corpus features

48 features over 8 node types, 496,532 word slots, 19,589 verses and
45 manuscripts.

Generated from `config/xml.yml` and the database by `programs/feature_page.py`. Every coverage
figure below is measured, at the feature's own tier, over the five publication views.

> **Coverage is uneven, and the figure is the point.** Some features are filled for under 2% of
> their tier. That is a property of the source lexicon rather than a gap in this dataset. Gender
> is recorded for 468 of the 2,654 noun entries that this corpus uses, and nothing done here
> moves that. A consumer who knows that gender covers 1% of the corpus can design around it,
> whereas one who discovers it later has the harder problem. See the ceilings, below.

## The node types

`text` -> `book` -> `chapter` -> `verse` -> `segment` -> `word_group` -> `lexeme` -> `word`

`lexeme` is the one node type that is **not contained** in the text tree. Its slots are
distributed across the whole corpus and shared between the witnesses, exactly as the equivalent
tier in the BHSA is. Reach the lexeme of a word with `L.u(w, otype='lexeme')[0]`.

## Sections and structure

There are three section levels, `book`, `chapter` and `verse`, so
`T.nodeFromSection(('Genesis', 1, 1))` resolves, which is what every tool written against a
comparable corpus opens with.

A section address is **not unique across witnesses**. Of 5,866 distinct
`(book, chapter, verse)` addresses, 5,827 are carried by more than one **manuscript**, by up
to 8 of them, because `book` names the biblical book rather than the manuscript.
Counted by verse node rather than by manuscript the figures are 5,844 and 9, the difference being
Neofiti, which contributes two nodes to each of its addresses and is one codex. That is
deliberate, because a corpus of parallel witnesses cannot have the manuscript at its first
section level and also be comparable with anything else. The witness is reached two other ways.
`structureTypes` carries the full `text -> book -> chapter -> verse` path and is subject to no
three-level limit, and the **`crossref` edge** names every parallel explicitly, so that
`E.crossref.f(verse)` returns every other reading of that verse, labelled `witness`, `view` or
`same_witness`.

## The text formats

| format | renders |
|---|---|
| `text-orig-full` | `voc_utf8` and `trailer`, Aramaic square script, vocalised |
| `text-cons` | `cons_utf8` and `trailer`, square script, consonantal |
| `text-trans-full` | `voc` and `trailer`, ETCBC transliteration, vocalised |
| `text-trans-cons` | `cons` and `trailer`, ETCBC transliteration, consonantal |

**`text-orig-full` and `text-cons` are the same string outside the Cairo Genizah.** Vocalisation
is present on the Genizah fragments and largely absent elsewhere, so the two square-script
formats differ only where there is pointing to differ about. The two transliterated formats are
always available, because the ETCBC pair is derived.

## The features

| feature | node | coverage | filled | of |
|---|---|---|---|---|
| [`id`](#id) | `word_group` | 100.0% | 359,576 | 359,583 |
| [`rank`](#rank) | `word_group` | 100.0% | 359,583 | 359,583 |
| [`reading`](#reading) | `word_group` | 100.0% | 359,583 | 359,583 |
| [`g_voc`](#g-voc) | `word_group` | 100.0% | 359,574 | 359,583 |
| [`g_cons`](#g-cons) | `word_group` | 100.0% | 359,574 | 359,583 |
| [`g_voc_utf8`](#g-voc-utf8) | `word_group` | 100.0% | 359,574 | 359,583 |
| [`g_cons_utf8`](#g-cons-utf8) | `word_group` | 100.0% | 359,574 | 359,583 |
| [`source`](#source) | `word` | 100.0% | 496,532 | 496,532 |
| [`part`](#part) | `word` | 100.0% | 496,532 | 496,532 |
| [`trailer`](#trailer) | `word` | 100.0% | 496,532 | 496,532 |
| [`start_idx`](#start-idx) | `word` | 99.1% | 492,287 | 496,532 |
| [`end_idx`](#end-idx) | `word` | 99.1% | 492,287 | 496,532 |
| [`uid`](#uid) | `word` | 98.5% | 489,262 | 496,532 |
| [`lex`](#lex) | `word` | 97.3% | 482,964 | 496,532 |
| [`lex0`](#lex0) | `word` | 97.3% | 482,964 | 496,532 |
| [`lex_utf8`](#lex-utf8) | `word` | 97.3% | 482,964 | 496,532 |
| [`cons`](#cons) | `word` | 100.0% | 496,402 | 496,532 |
| [`voc`](#voc) | `word` | 100.0% | 496,532 | 496,532 |
| [`cons_utf8`](#cons-utf8) | `word` | 100.0% | 496,532 | 496,532 |
| [`voc_utf8`](#voc-utf8) | `word` | 100.0% | 496,532 | 496,532 |
| [`root`](#root) | `word` | 92.5% | 459,141 | 496,532 |
| [`gn`](#gn) | `word` | 1.1% | 5,364 | 496,532 |
| [`vs`](#vs) | `word` | 16.1% | 79,848 | 496,532 |
| [`sp`](#sp) | `word` | 97.3% | 482,966 | 496,532 |
| [`st`](#st) | `word` | 31.1% | 154,581 | 496,532 |
| [`nu`](#nu) | `word` | 31.1% | 154,585 | 496,532 |
| [`gloss`](#gloss) | `word` | 91.7% | 455,489 | 496,532 |
| [`definition`](#definition) | `word` | 91.6% | 454,901 | 496,532 |
| [`description`](#description) | `word` | 100.0% | 496,532 | 496,532 |
| [`lex`](#lex) | `lexeme` | 100.0% | 6,363 | 6,363 |
| [`lex0`](#lex0) | `lexeme` | 100.0% | 6,363 | 6,363 |
| [`lex_utf8`](#lex-utf8) | `lexeme` | 100.0% | 6,363 | 6,363 |
| [`freq_lex`](#freq-lex) | `lexeme` | 100.0% | 6,363 | 6,363 |
| [`rank_lex`](#rank-lex) | `lexeme` | 100.0% | 6,363 | 6,363 |
| [`id`](#id) | `segment` | 100.0% | 55,049 | 55,049 |
| [`start_idx`](#start-idx) | `segment` | 99.8% | 54,960 | 55,049 |
| [`end_idx`](#end-idx) | `segment` | 99.8% | 54,960 | 55,049 |
| [`type`](#type) | `segment` | 100.0% | 55,049 | 55,049 |
| [`rank`](#rank) | `segment` | 100.0% | 55,049 | 55,049 |
| [`segment`](#segment) | `segment` | 100.0% | 55,049 | 55,049 |
| [`segment_utf8`](#segment-utf8) | `segment` | 100.0% | 55,049 | 55,049 |
| [`verse`](#verse) | `verse` | 100.0% | 19,589 | 19,589 |
| [`line`](#line) | `verse` | 100.0% | 19,589 | 19,589 |
| [`line_utf8`](#line-utf8) | `verse` | 100.0% | 19,589 | 19,589 |
| [`chapter`](#chapter) | `chapter` | 100.0% | 987 | 987 |
| [`book`](#book) | `book` | 100.0% | 75 | 75 |
| [`id`](#id) | `book` | 100.0% | 75 | 75 |
| [`text`](#text) | `text` | 100.0% | 46 | 46 |
| [`manuscript`](#manuscript) | `text` | 100.0% | 46 | 46 |
| [`view`](#view) | `text` | 100.0% | 46 | 46 |

## Feature by feature

### `id`

*on `word_group` nodes, 100.0%, 359,576 of 359,583* *(stored as an integer, so it sorts numerically)*

Identifier of the node, corresponding to the primary key held in the relational source

### `rank`

*on `word_group` nodes, 100.0%, 359,583 of 359,583* *(stored as an integer, so it sorts numerically)*

Ordinal position of the node among its siblings, counting from the start of the enclosing node within the line. On a word group it counts every published unit of the verse in the order in which their characters appear in `line`, which includes the word groups that stand for segments no word of the manuscript reaches

### `reading`

*on `word_group` nodes, 100.0%, 359,583 of 359,583* *(stored as an integer, so it sorts numerically)*

Which reading of a word group this is. Readings competing for one position in the line share a `rank` and are distinguished here, 0 being the base reading that the edition prints and the reading the first scribe wrote. Values 1 and above are the scribal or editorial emendation candidates. Every rank that carries any reading carries a reading 0. The distribution of these values is a property of the view type, and the candidates are defined by segment types such as variant, interlinear and addition

### `g_voc`

*on `word_group` nodes, 100.0%, 359,574 of 359,583*

Vocalized text of a word group in ETCBC transcription

### `g_cons`

*on `word_group` nodes, 100.0%, 359,574 of 359,583*

Consonantal text of a word group in ETCBC transcription

### `g_voc_utf8`

*on `word_group` nodes, 100.0%, 359,574 of 359,583*

Vocalized text of a word group in Aramaic square script

### `g_cons_utf8`

*on `word_group` nodes, 100.0%, 359,574 of 359,583*

Consonantal text of a word group in Aramaic square script

### `source`

*on `word` nodes, 100.0%, 496,532 of 496,532*

Provenance of a word. `word` where the morphological analysis was placed on the word itself, `word_group` where the word group carries a surface form that no analysis points at, `none` where the manuscript has a word that was never analysed, and `segment` where the word stands for a segment that no word of the manuscript reaches and carries the text of that segment so that the segment can be published at all

### `part`

*on `word` nodes, 100.0%, 496,532 of 496,532* *(stored as an integer, so it sorts numerically)*

Which part of a word this node is, counting from 1, where an editorial boundary divides one printed word in two. The parts of one word share their word group and its `id`, each sits in the segment that its own characters fall within, and they are published in the order in which those characters appear in `line`. A word with `part` 1 and no sibling is whole

### `trailer`

*on `word` nodes, 100.0%, 496,532 of 496,532*

Content following a word, either a space or nothing

### `start_idx`

*on `word` nodes, 99.1%, 492,287 of 496,532* *(stored as an integer, so it sorts numerically)*

One-based character offset of the first character of a word or of a segment within `line`, the ETCBC transliteration of the verse that contains it. The offsets of a segment are the minimum and the maximum of the offsets of the words it holds. Both tiers leave the offsets absent where the word carries no surface form, and where the word tier and `line` diverge

### `end_idx`

*on `word` nodes, 99.1%, 492,287 of 496,532* *(stored as an integer, so it sorts numerically)*

One-based character offset of the last character of a word or of a segment within `line`, so that `substr(line, start_idx, end_idx - start_idx + 1)` returns the `voc` of the word or the text of the segment

### `uid`

*on `word` nodes, 98.5%, 489,262 of 496,532*

Independent unique identifier of the node

### `lex`

*on `word` nodes, 97.3%, 482,964 of 496,532*

Lexeme in ETCBC transcription, disambiguated as the BHSA disambiguates it. A trailing `[` marks a verb, `/` marks a noun or an adjective, and zero or more `=` signs distinguish lexemes that share consonants. The homonym count is taken from the source lexicon rather than assigned here, so it is stable across rebuilds, and it reaches at most seven `=` signs. Read `lex0` for the value with that material removed. Where the disambiguated string still collides the dataset publishes no finer key, and 1,068 of 32,018 lexical identities do collide, most of them an adjective against a noun, which the BHSA collapses as well. A word that is analysed but not assigned a lexical entry carries no value. The marker is a statement about the lexeme while `sp` is a statement about this token, so the two can legitimately disagree. 600 words of Pseudo-Jonathan carry `sp=subs` beneath a `lex` ending in `[`, and these are nominalised participles, a verb in the lexicon used here as a noun. The BHSA draws the same distinction in the same place

### `lex0`

*on `word` nodes, 97.3%, 482,964 of 496,532*

`lex` with the disambiguation material removed, so that two homographs of one part of speech share a value. The companion to `lex` that the BHSA also publishes, and the value to group by when counting vocabulary

### `lex_utf8`

*on `word` nodes, 97.3%, 482,964 of 496,532*

Lexeme in Aramaic square script

### `cons`

*on `word` nodes, 100.0%, 496,402 of 496,532*

Consonantal text of a word in ETCBC transcription, taken from the characters that the published line holds. Absent where the morpheme is not written in the word at all, which in an agglutinative language is an ordinary case. Read `source` and `part` to establish what such a word is

### `voc`

*on `word` nodes, 100.0%, 496,532 of 496,532*

Vocalized text of a word in ETCBC transcription

### `cons_utf8`

*on `word` nodes, 100.0%, 496,532 of 496,532*

Consonantal text of a word in Aramaic square script

### `voc_utf8`

*on `word` nodes, 100.0%, 496,532 of 496,532*

Vocalized text of a word in Aramaic square script

### `root`

*on `word` nodes, 92.5%, 459,141 of 496,532*

Root, typically of a verb

### `gn`

*on `word` nodes, 1.1%, 5,364 of 496,532*

Gender, nominal only. Partial, with a ceiling of approximately 1 per cent: 5,349 of 493,690 published words carry a value, or 1.08 per cent. The limit lies in the source lexicon rather than in the extraction, since of the 2,654 noun entries that this corpus uses only 660 carry a combined category and 468 a gender. Design queries around that coverage, because a query assuming this feature is populated is reading 1 per cent of the corpus

### `vs`

*on `word` nodes, 16.1%, 79,848 of 496,532*

Verbal stem, from a source vocabulary that encodes the stem and nothing else. Carried by 79,831 of the 81,875 words that `sp` calls a verb, or 97.50 per cent. The 2,044 without one are verbs to which the source assigns no category. This is the whole of the verbal morphology available in the source data. Person, tense and voice are not partial here but absent, and the columns that would hold them are empty on all 591,862 analysed units of the corpus. Supplying them would be new annotation rather than extraction

### `sp`

*on `word` nodes, 97.3%, 482,966 of 496,532*

Part of speech, one of `subs`, `verb`, `adjv`, `prep`, `advb`, `conj`, `pron`, `intj`, `nmpr` and `unknown`. Resolved from the glossed category first and from the lexical entry only where the former has no opinion, which is what closed the 59,690 words that previously carried none. The order matters, because 4,644 units whose entry is classified as a verb are nominalised participles that their own category correctly calls `subs`. Two source tags have no counterpart in this vocabulary and are left absent. The value `nmpr` is taken from the BHSA and is resolved last, so that it can only fill a part of speech that was otherwise absent, and it marks the words filed as proper or geographical names, which carry no lexical entry and therefore no part of speech of their own

### `st`

*on `word` nodes, 31.1%, 154,581 of 496,532*

Nominal state, either absolute, emphatic or construct, and `absolute or construct` where the source states the ambiguity rather than resolving it. Partial, and the determined share is smaller than the fill rate: 153,500 of 493,690 words carry a value, or 31.09 per cent, of which 47,336 carry the ambiguous one, so the state is actually determined on 106,164 words, or 21.5 per cent. Absent where nothing is determined. An earlier version published the empty string in those positions, which reads as a determination that there is no state

### `nu`

*on `word` nodes, 31.1%, 154,585 of 496,532*

Number, nominal only, either `sg` or `pl`. The source writes the singular differently and the value is mapped here so that the two are spelled consistently with each other and with the BHSA. Partial, covering 153,504 of 493,690 words, or 31.09 per cent

### `gloss`

*on `word` nodes, 91.7%, 455,489 of 496,532*

English gloss of the lexical entry. Absent where the entry has not been glossed. An earlier version resolved this feature to the same expression published beside it as `description`, which made it non-null on every word of the corpus and left 30,021 words holding a lexical category where a reader expects a translation

### `definition`

*on `word` nodes, 91.6%, 454,901 of 496,532*

Extended translation or dictionary definition

### `description`

*on `word` nodes, 100.0%, 496,532 of 496,532*

Description of a text, view, word or lexical entry

### `lex`

*on `lexeme` nodes, 100.0%, 6,363 of 6,363*

Lexeme in ETCBC transcription, disambiguated as the BHSA disambiguates it. A trailing `[` marks a verb, `/` marks a noun or an adjective, and zero or more `=` signs distinguish lexemes that share consonants. The homonym count is taken from the source lexicon rather than assigned here, so it is stable across rebuilds, and it reaches at most seven `=` signs. Read `lex0` for the value with that material removed. Where the disambiguated string still collides the dataset publishes no finer key, and 1,068 of 32,018 lexical identities do collide, most of them an adjective against a noun, which the BHSA collapses as well. A word that is analysed but not assigned a lexical entry carries no value. The marker is a statement about the lexeme while `sp` is a statement about this token, so the two can legitimately disagree. 600 words of Pseudo-Jonathan carry `sp=subs` beneath a `lex` ending in `[`, and these are nominalised participles, a verb in the lexicon used here as a noun. The BHSA draws the same distinction in the same place

### `lex0`

*on `lexeme` nodes, 100.0%, 6,363 of 6,363*

`lex` with the disambiguation material removed, so that two homographs of one part of speech share a value. The companion to `lex` that the BHSA also publishes, and the value to group by when counting vocabulary

### `lex_utf8`

*on `lexeme` nodes, 100.0%, 6,363 of 6,363*

Lexeme in Aramaic square script

### `freq_lex`

*on `lexeme` nodes, 100.0%, 6,363 of 6,363* *(stored as an integer, so it sorts numerically)*

How many words of the corpus carry this lexeme, on `lexeme` nodes. The feature of the same name in the BHSA. Counted over the four distinct witnesses and deliberately not over the base view of Neofiti, which is a second view of a manuscript already counted, since including it would inflate every Neofiti lexeme by very nearly a factor of two. The count covers 351,387 tokens over 6,363 lexemes, of which the conjunction accounts for 38,996. A lexeme attested only in the base view of Neofiti has a frequency of 0, which is the honest value and is true of eight of them

### `rank_lex`

*on `lexeme` nodes, 100.0%, 6,363 of 6,363* *(stored as an integer, so it sorts numerically)*

Position of the lexeme in the frequency list of the corpus, 1 being the most frequent, on `lexeme` nodes. The feature of the same name in the BHSA. The ranking is total over 1 to 6,363 rather than dense, because these 6,363 lexemes have only 389 distinct frequencies and a dense ranking would give every hapax legomenon the same number, leaving no answer to whether a lexeme falls within the hundred most frequent. Ties are broken on the lexeme and its lexical identity, so re-measuring after a rebuild reproduces the ranking rather than reordering it

### `id`

*on `segment` nodes, 100.0%, 55,049 of 55,049* *(stored as an integer, so it sorts numerically)*

Identifier of the node, corresponding to the primary key held in the relational source

### `start_idx`

*on `segment` nodes, 99.8%, 54,960 of 55,049* *(stored as an integer, so it sorts numerically)*

One-based character offset of the first character of a word or of a segment within `line`, the ETCBC transliteration of the verse that contains it. The offsets of a segment are the minimum and the maximum of the offsets of the words it holds. Both tiers leave the offsets absent where the word carries no surface form, and where the word tier and `line` diverge

### `end_idx`

*on `segment` nodes, 99.8%, 54,960 of 55,049* *(stored as an integer, so it sorts numerically)*

One-based character offset of the last character of a word or of a segment within `line`, so that `substr(line, start_idx, end_idx - start_idx + 1)` returns the `voc` of the word or the text of the segment

### `type`

*on `segment` nodes, 100.0%, 55,049 of 55,049*

Type of the node, such as `unmarked_text` for a segment or `full_text` for a view

### `rank`

*on `segment` nodes, 100.0%, 55,049 of 55,049* *(stored as an integer, so it sorts numerically)*

Ordinal position of the node among its siblings, counting from the start of the enclosing node within the line. On a word group it counts every published unit of the verse in the order in which their characters appear in `line`, which includes the word groups that stand for segments no word of the manuscript reaches

### `segment`

*on `segment` nodes, 100.0%, 55,049 of 55,049*

Grouping of words and word groups by their position within a discrete editorial or emendation block such as a variant reading. On a `segment` node this feature also holds the vocalised text of the segment in ETCBC transcription

### `segment_utf8`

*on `segment` nodes, 100.0%, 55,049 of 55,049*

Vocalized text of a segment in Aramaic square script

### `verse`

*on `verse` nodes, 100.0%, 19,589 of 19,589* *(stored as an integer, so it sorts numerically)*

A line of text, usually though not always corresponding to a verse of a book or manuscript. Section level 3, which is what allows `T.nodeFromSection((book, chapter, verse))` to resolve. Eleven verses carry no verse number in the source edition and publish a sentinel in its place, either 0, or 0 and -2 where one chapter holds two of them, because a section address can be neither null nor shared by two verses. Nine of the eleven are in the two fragment targum manuscripts and two are Cairo Genizah fragments, at Exodus 15 and Deuteronomy 34, which are the largest of the eleven at 42 and 148 words. The sentinel descends in steps of two so that it skips -1, which reading clients reserve as the missing-value sentinel of an integer feature. A published -1 would load back as a null and a comparison against it would raise rather than answer

### `line`

*on `verse` nodes, 100.0%, 19,589 of 19,589*

Vocalized text of a verse in ETCBC transcription

### `line_utf8`

*on `verse` nodes, 100.0%, 19,589 of 19,589*

Vocalized text of a verse in Aramaic square script

### `chapter`

*on `chapter` nodes, 100.0%, 987 of 987* *(stored as an integer, so it sorts numerically)*

Chapter of the book, and section level 2

### `book`

*on `book` nodes, 100.0%, 75 of 75*

Name of a biblical book, and section level 1. It names the biblical book rather than the manuscript, so one book name is shared by every witness that transmits it. Of the 5,866 distinct `(book, chapter, verse)` addresses in the corpus, 5,827 are carried by more than one manuscript and 5,844 by more than one `verse` node, the difference being the two views of Neofiti. Use `text` or `structureTypes` to identify the witness, `manuscript` to identify the codex, and `crossref` to reach the parallels

### `id`

*on `book` nodes, 100.0%, 75 of 75* *(stored as an integer, so it sorts numerically)*

Identifier of the node, corresponding to the primary key held in the relational source

### `text`

*on `text` nodes, 100.0%, 46 of 46*

Name of an Aramaic text, often a manuscript. Carried by `text` nodes and by nothing else. It is the outermost structure feature and is not a section feature, the three section levels being `book`, `chapter` and `verse`, so the witness is reached through `structureTypes`. Read `cons_utf8` for the letters of a word

### `manuscript`

*on `text` nodes, 100.0%, 46 of 46*

The manuscript that a text witnesses, carried by `text` nodes. The feature `text` is not this: it names the manuscript everywhere except Neofiti, where `neofiti_base` and `neofiti_full` are two views of a single codex, Neofiti 1. The corpus therefore carries 46 `text` values over 45 manuscripts, and that is the only such collapse. The feature is published because it is the one fact in the parallel witness relation that nothing else in the dataset can supply. Two verses are parallel when they share a `(book, chapter, verse)` address, which is derivable, but distinguishing a parallel, where two manuscripts translate the verse, from a single manuscript presented under two editorial filters, is not. Derived without this feature the relation splits 49,384 witness against 20 view, in place of the true 37,730, 11,654 and 20, so a consumer counting witnesses per verse would be wrong by one on all 5,827 Neofiti addresses

### `view`

*on `text` nodes, 100.0%, 46 of 46*

Grouping of segments according to the editorial and emendation filters applied to the text

## The ceilings, and why they belong to the source

| feature | coverage | why it stops there |
|---|---|---|
| `ps` person | **absent** | the source column is null on all 591,862 analysed units |
| `vt` tense and aspect | **absent** | likewise null throughout |
| voice | **absent** | likewise null throughout |
| `prs`, `nme`, `pfm`, `vbe`, `uvf` | **absent** | no source for them at all |
| `vs` stem | present | the source vocabulary encodes the stem and nothing else, and 2,049 verbs carry none |
| `gn` gender | about 1% | recorded for 468 of the 2,654 noun entries this corpus uses, with 96 more recoverable |
| `nu`, `st` | about 31% each | partial in the lexicon, and `st` is actually determined on 106,491 words against 47,485 that the source itself marks as ambiguous |

**Verbal morphology would be new annotation here rather than extraction.** The source returns the
stem and that is the whole of it. The three empty columns are deliberately **not dropped** from
the database, because a dropped column cannot be re-measured, so counting them remains the
falsification of this claim for anyone who doubts it.

**Segmentation stops at the proclitic.** 65.2% of source words are a single unit and the mean is
1.35, so the decomposition is real and it is prefixal. Enclitics do not split, although the source
flags the boundary: **57,728 units** are categorised as a preposition with a pronominal suffix,
which is one unit carrying two morphemes where the second has been named. Nouns and verbs with
suffixes carry no flag at all, so 57,728 is a floor.

## The withdrawn features

Features that earlier versions carried and this one does not. Each is listed with what to read
instead, because a consumer who finds one missing would otherwise read it as data loss. Features
are published only where the value is attested, varies, and is not recoverable from the rest of
the dataset.

| feature | tier | why, and what replaces it |
|---|---|---|
| `lex_id` | `word` | An identifier of the source lexicon. Withdrawn because its only use is to dereference against an external service, which would make the dataset permanently dependent on one. Read `lex` and `lex0`, and reach the lexeme tier with `L.u(w, otype='lexeme')[0]`. |
| `lex_key` | `lexeme` | A minted identifier for the lexeme tier. Withdrawn because the tier is already identified by `rank_lex`, which is a total ranking over 1 to the number of lexemes and so is a bijection onto those nodes. Read `rank_lex`, or `lex` where a readable label is wanted. |
| `id` | `word` | The primary key of the analysed unit in the relational source. Withdrawn because those identifiers collide almost completely across the three underlying table families, so a consumer joining on one without also knowing its family read an unrelated row silently, and in plausible Aramaic. Read `uid`, which is global. |
| `uid` | `verse` | The verse key of the relational source, with the same family scoping problem on 4,844 values. Read the canonical address instead, since `(book, chapter, verse)` is a section path and `T.nodeFromSection(('Genesis', 1, 1))` resolves. |
| `text` on `word` | `word` | A byte-for-byte copy of the word's own `cons_utf8`, published under a name that the text node also used, so one feature held 490,496 word values and 68 manuscript names while `text` was a structure feature besides. Measured, 0 of 490,495 values differed from `cons_utf8`. Read `cons_utf8`. |
| `language` | `word` | A constant. Every token of the corpus carried the single value `Aramaic`, so the feature answered no question while occupying 4.0 MB. Read `dialect` in the database for the isolect of a text. |
| `lex_dialects`, `gloss_norm`, `voc_lex` | `lexeme` | Properties of a dictionary entry rather than of this corpus, each covering a minority of the lexeme tier and each recoverable from the lexicon the lexeme names. Read `lex0` to group the vocabulary, and `gloss` and `definition` for the published translation. |
| `nametype` | `word` | The onomastic category of a proper noun. Withdrawn to keep the published word tier to what the manuscript and its analysis state. The words themselves are unaffected and resolve to a lexical entry as before. |
| `piece`, `pieces` | `word` | Ordinals of the internal segmentation model, numbering the whitespace-delimited parts of a lexical entry filed as several orthographic words. Withdrawn because they describe the model rather than the text. The split itself is published, in that no `cons` value holds an internal space. Read `part`, which numbers the editorial division of a word. |
| `variant` | `word_group` | A description of the witness a reading comes from. Withdrawn because 11,177 of the 11,203 readings that carried a value held the same legend sentence, which also named an internal file reference that a consumer cannot resolve. Read the segment `type`, which states the editorial state of the reading, and `reading`, which orders the candidates. |

## What is recorded but is not a feature

**The editorial flag register.** 16,634 published words carry one or more open
editorial exceptions, across 20 distinct reasons, and these are deliberately not a
Text-Fabric feature. A flag is an editorial working state that changes as a campaign resolves
rows, whereas a published feature is frozen at the rebuild, so it would be stale the following
day. Two of its levels are not coverage gaps but stated uncertainty about claims this dataset
publishes regardless: 1,098 words whose assignment to a reading is unconfirmed, and 671 whose
morpheme boundary is unproved. Query the register directly in PostgreSQL:

```sql
SELECT word_uid, flag FROM neofiti_full_mat_next WHERE flag IS NOT NULL;
```

**The witness a reading comes from.** 11,181 published readings carry a mark identifying
the witness, of which 22 carry one that the legend of the source does not describe.
Neither the mark nor its description is published as a feature. The mark alone is an internal
code that means nothing without its description, and the descriptions themselves proved to be a
single legend sentence on 11,177 of 11,203 readings. The editorial state of a reading is
published, as the segment `type` and the `reading` ordinal.

## The absent syntactic tier, as a non-goal

This corpus has **no phrase, clause or sentence tier**, and will not acquire one in this release.
That is a stated non-goal rather than an omission. The source supplies no syntactic annotation,
so a syntactic tier would be new scholarly annotation of 496,532 words rather than extraction. A
consumer trained on the BHSA, where phrase, clause and sentence are node types and `function`,
`rela` and `typ` are features, will find none of them here, and should read the absence as this
dataset declining to invent them.
