# The ETCBC Targum Corpus features

48 features over 8 node types, 640,353 word slots, 26,094 verses and
46 manuscripts.

Generated from the feature declaration in `config/xml.yml` and from the database. Every coverage
figure below is measured, at the feature's own tier, over the six publication views.

> **Coverage is uneven, and the figure is the point.** Several features are filled for only a
> small minority of their tier. That is a property of the source lexicon rather than a gap in this
> dataset, and nothing done here moves it. Every row below carries its own measured coverage, so a
> consumer who reads that figure first can design around it, whereas one who discovers it later
> has the harder problem. The ceilings, below, say where each limit comes from.

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
`(book, chapter, verse)` addresses, 5,853 are carried by more than one **manuscript**, by up
to 12 of them, because `book` names the biblical book rather than the manuscript.
Counting by verse node rather than by manuscript raises both figures, the difference being
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
| [`id`](#id) | `word_group` | 100.0% | 463,466 | 463,477 |
| [`rank`](#rank) | `word_group` | 100.0% | 463,477 | 463,477 |
| [`reading`](#reading) | `word_group` | 100.0% | 463,477 | 463,477 |
| [`g_voc`](#g-voc) | `word_group` | 100.0% | 463,466 | 463,477 |
| [`g_cons`](#g-cons) | `word_group` | 100.0% | 463,466 | 463,477 |
| [`g_voc_utf8`](#g-voc-utf8) | `word_group` | 100.0% | 463,466 | 463,477 |
| [`g_cons_utf8`](#g-cons-utf8) | `word_group` | 100.0% | 463,466 | 463,477 |
| [`source`](#source) | `word` | 100.0% | 640,353 | 640,353 |
| [`part`](#part) | `word` | 100.0% | 640,353 | 640,353 |
| [`trailer`](#trailer) | `word` | 100.0% | 640,353 | 640,353 |
| [`start_idx`](#start-idx) | `word` | 97.5% | 624,651 | 640,353 |
| [`end_idx`](#end-idx) | `word` | 97.5% | 624,651 | 640,353 |
| [`uid`](#uid) | `word` | 99.4% | 636,717 | 640,353 |
| [`lex`](#lex) | `word` | 98.1% | 628,387 | 640,353 |
| [`lex0`](#lex0) | `word` | 98.1% | 628,387 | 640,353 |
| [`lex_utf8`](#lex-utf8) | `word` | 98.1% | 628,387 | 640,353 |
| [`cons`](#cons) | `word` | 100.0% | 640,208 | 640,353 |
| [`voc`](#voc) | `word` | 100.0% | 640,353 | 640,353 |
| [`cons_utf8`](#cons-utf8) | `word` | 100.0% | 640,352 | 640,353 |
| [`voc_utf8`](#voc-utf8) | `word` | 100.0% | 640,353 | 640,353 |
| [`root`](#root) | `word` | 93.3% | 597,573 | 640,353 |
| [`gn`](#gn) | `word` | 1.1% | 7,175 | 640,353 |
| [`vs`](#vs) | `word` | 16.4% | 105,044 | 640,353 |
| [`sp`](#sp) | `word` | 98.1% | 628,390 | 640,353 |
| [`st`](#st) | `word` | 31.3% | 200,596 | 640,353 |
| [`nu`](#nu) | `word` | 31.3% | 200,600 | 640,353 |
| [`gloss`](#gloss) | `word` | 92.6% | 593,262 | 640,353 |
| [`definition`](#definition) | `word` | 92.5% | 592,446 | 640,353 |
| [`description`](#description) | `word` | 100.0% | 640,353 | 640,353 |
| [`lex`](#lex) | `lexeme` | 100.0% | 7,058 | 7,058 |
| [`lex0`](#lex0) | `lexeme` | 100.0% | 7,058 | 7,058 |
| [`lex_utf8`](#lex-utf8) | `lexeme` | 100.0% | 7,058 | 7,058 |
| [`freq_lex`](#freq-lex) | `lexeme` | 100.0% | 7,058 | 7,058 |
| [`rank_lex`](#rank-lex) | `lexeme` | 100.0% | 7,058 | 7,058 |
| [`id`](#id) | `segment` | 100.0% | 72,737 | 72,737 |
| [`start_idx`](#start-idx) | `segment` | 99.9% | 72,671 | 72,737 |
| [`end_idx`](#end-idx) | `segment` | 99.9% | 72,671 | 72,737 |
| [`type`](#type) | `segment` | 100.0% | 72,737 | 72,737 |
| [`rank`](#rank) | `segment` | 100.0% | 72,737 | 72,737 |
| [`segment`](#segment) | `segment` | 100.0% | 72,737 | 72,737 |
| [`segment_utf8`](#segment-utf8) | `segment` | 100.0% | 72,737 | 72,737 |
| [`verse`](#verse) | `verse` | 100.0% | 26,094 | 26,094 |
| [`line`](#line) | `verse` | 100.0% | 26,094 | 26,094 |
| [`line_utf8`](#line-utf8) | `verse` | 100.0% | 26,094 | 26,094 |
| [`chapter`](#chapter) | `chapter` | 100.0% | 1,210 | 1,210 |
| [`book`](#book) | `book` | 100.0% | 85 | 85 |
| [`id`](#id) | `book` | 100.0% | 85 | 85 |
| [`text`](#text) | `text` | 100.0% | 47 | 47 |
| [`manuscript`](#manuscript) | `text` | 100.0% | 47 | 47 |
| [`view`](#view) | `text` | 100.0% | 47 | 47 |

## Feature by feature

### `id`

*on `word_group` nodes, 100.0%, 463,466 of 463,477* *(stored as an integer, so it sorts numerically)*

xml id, associated to primary key in other data stores (SQL)

### `rank`

*on `word_group` nodes, 100.0%, 463,477 of 463,477* *(stored as an integer, so it sorts numerically)*

ordinal position of the node among its siblings, counting from the start of the enclosing node, within the line

### `reading`

*on `word_group` nodes, 100.0%, 463,477 of 463,477* *(stored as an integer, so it sorts numerically)*

which reading of a word group this is; readings competing for one position of the line share a rank and differ here, 0 being the one the edition prints. Value 0 is the "original" reading the first scribe wrote in the manuscript, and 1, 2, 3 are the scribal or editorial emendation candidates. Every rank that has any reading has a reading 0. Almost all of them come from one editorial marker, and are defined by segment types such as 'variant,'interlinear,'addition' etc. This distribution is a property of the view type.

### `g_voc`

*on `word_group` nodes, 100.0%, 463,466 of 463,477*

Vocalized text of a word group in ETCBC transcription

### `g_cons`

*on `word_group` nodes, 100.0%, 463,466 of 463,477*

Consonantal text of a word group in ETCBC transcription

### `g_voc_utf8`

*on `word_group` nodes, 100.0%, 463,466 of 463,477*

Vocalized text of a word group in Aramaic square script

### `g_cons_utf8`

*on `word_group` nodes, 100.0%, 463,466 of 463,477*

Consonantal text of a word group in Aramaic square script

### `source`

*on `word` nodes, 100.0%, 640,353 of 640,353*

provenance of a word; "word" where morphology was placed on it, "word_group" where the word group carries a surface form that no morphology points at, and "none" where the manuscript has a word that was never analysed

### `part`

*on `word` nodes, 100.0%, 640,353 of 640,353* *(stored as an integer, so it sorts numerically)*

Which part of a word this node is, counting from 1, where an editorial boundary divides one printed word in two. A word with `part` 1 and no sibling is whole

### `trailer`

*on `word` nodes, 100.0%, 640,353 of 640,353*

Content after a word (empty space or None)

### `start_idx`

*on `word` nodes, 97.5%, 624,651 of 640,353* *(stored as an integer, so it sorts numerically)*

one-based character offset of the first character of a word or of a segment within `line`, the ETCBC transliteration of the verse that contains it; a segment's offsets are the minimum and the maximum of the offsets of the words it holds, and both tiers leave them absent where the word carries no surface form or where the word tier and `line` diverge. A reading transcribed on a line of its own, marginal or a whole-verse variant, is not part of `line`. Its words carry no offsets, and the offsets of its segment locate instead the words of `line` that the reading annotates, absent where those words could not be identified

### `end_idx`

*on `word` nodes, 97.5%, 624,651 of 640,353* *(stored as an integer, so it sorts numerically)*

one-based character offset of the last character of a word or of a segment within `line`, so that `substr(line, start_idx, end_idx - start_idx + 1)` returns the word's own `voc` or the segment's own `segment`

### `uid`

*on `word` nodes, 99.4%, 636,717 of 640,353*

independent unique identifier of the node

### `lex`

*on `word` nodes, 98.1%, 628,387 of 640,353*

Lexeme in ETCBC transcription

### `lex0`

*on `word` nodes, 98.1%, 628,387 of 640,353*

`lex` with the disambiguation material removed, so that two homographs of one part of speech share a value. The companion to `lex` that the BHSA also publishes, and the value to group by when counting vocabulary

### `lex_utf8`

*on `word` nodes, 98.1%, 628,387 of 640,353*

Lexeme in Aramaic square script

### `cons`

*on `word` nodes, 100.0%, 640,208 of 640,353*

Consonantal text of a word in ETCBC transcription

### `voc`

*on `word` nodes, 100.0%, 640,353 of 640,353*

Vocalized text of a word in ETCBC transcription

### `cons_utf8`

*on `word` nodes, 100.0%, 640,352 of 640,353*

Consonantal text of a word in Aramaic square script

### `voc_utf8`

*on `word` nodes, 100.0%, 640,353 of 640,353*

Vocalized text of a word in Aramaic square script

### `root`

*on `word` nodes, 93.3%, 597,573 of 640,353*

Root, typically of a verb

### `gn`

*on `word` nodes, 1.1%, 7,175 of 640,353*

Gender (nominal only, partial)

### `vs`

*on `word` nodes, 16.4%, 105,044 of 640,353*

Verbal stem / binyan

### `sp`

*on `word` nodes, 98.1%, 628,390 of 640,353*

Part of speech

### `st`

*on `word` nodes, 31.3%, 200,596 of 640,353*

Nominal state (abs/emph/cons, partial)

### `nu`

*on `word` nodes, 31.3%, 200,600 of 640,353*

Number (nominal only, partial)

### `gloss`

*on `word` nodes, 92.6%, 593,262 of 640,353*

English gloss

### `definition`

*on `word` nodes, 92.5%, 592,446 of 640,353*

Extended translation or dictionary definition

### `description`

*on `word` nodes, 100.0%, 640,353 of 640,353*

Description of a text, view, word, lemma, etc.

### `lex`

*on `lexeme` nodes, 100.0%, 7,058 of 7,058*

Lexeme in ETCBC transcription

### `lex0`

*on `lexeme` nodes, 100.0%, 7,058 of 7,058*

`lex` with the disambiguation material removed, so that two homographs of one part of speech share a value. The companion to `lex` that the BHSA also publishes, and the value to group by when counting vocabulary

### `lex_utf8`

*on `lexeme` nodes, 100.0%, 7,058 of 7,058*

Lexeme in Aramaic square script

### `freq_lex`

*on `lexeme` nodes, 100.0%, 7,058 of 7,058* *(stored as an integer, so it sorts numerically)*

How many words of the corpus carry this lexeme, on `lexeme` nodes.

### `rank_lex`

*on `lexeme` nodes, 100.0%, 7,058 of 7,058* *(stored as an integer, so it sorts numerically)*

Position of the lexeme in the frequency list of the corpus, 1 being the most frequent, on `lexeme` nodes.

### `id`

*on `segment` nodes, 100.0%, 72,737 of 72,737* *(stored as an integer, so it sorts numerically)*

xml id, associated to primary key in other data stores (SQL)

### `start_idx`

*on `segment` nodes, 99.9%, 72,671 of 72,737* *(stored as an integer, so it sorts numerically)*

one-based character offset of the first character of a word or of a segment within `line`, the ETCBC transliteration of the verse that contains it; a segment's offsets are the minimum and the maximum of the offsets of the words it holds, and both tiers leave them absent where the word carries no surface form or where the word tier and `line` diverge. A reading transcribed on a line of its own, marginal or a whole-verse variant, is not part of `line`. Its words carry no offsets, and the offsets of its segment locate instead the words of `line` that the reading annotates, absent where those words could not be identified

### `end_idx`

*on `segment` nodes, 99.9%, 72,671 of 72,737* *(stored as an integer, so it sorts numerically)*

one-based character offset of the last character of a word or of a segment within `line`, so that `substr(line, start_idx, end_idx - start_idx + 1)` returns the word's own `voc` or the segment's own `segment`

### `type`

*on `segment` nodes, 100.0%, 72,737 of 72,737*

type of the node (e.g., unmarked_text for segment, full_text for view). A segment of type marginal holds a reading written in the margin of the manuscript. A reading transcribed on a line of its own, whether marginal or a variant of the whole verse from another witness, follows the words of the verse it annotates

### `rank`

*on `segment` nodes, 100.0%, 72,737 of 72,737* *(stored as an integer, so it sorts numerically)*

ordinal position of the node among its siblings, counting from the start of the enclosing node, within the line

### `segment`

*on `segment` nodes, 100.0%, 72,737 of 72,737*

Grouping of words and word groups based on position within discrete editorial or emendation blocks (e.g., variants)

### `segment_utf8`

*on `segment` nodes, 100.0%, 72,737 of 72,737*

Vocalized text of a segment in Aramaic square script

### `verse`

*on `verse` nodes, 100.0%, 26,094 of 26,094* *(stored as an integer, so it sorts numerically)*

A line of text, typically (though not always) corresponding to a verse in a book or manuscript

### `line`

*on `verse` nodes, 100.0%, 26,094 of 26,094*

Vocalized text of a verse in ETCBC transcription. The words of a reading transcribed on a line of its own, marginal or a whole-verse variant, are not part of it

### `line_utf8`

*on `verse` nodes, 100.0%, 26,094 of 26,094*

Vocalized text of a verse in Aramaic square script

### `chapter`

*on `chapter` nodes, 100.0%, 1,210 of 1,210* *(stored as an integer, so it sorts numerically)*

Chapter of the book

### `book`

*on `book` nodes, 100.0%, 85 of 85*

Name of Biblical book

### `id`

*on `book` nodes, 100.0%, 85 of 85* *(stored as an integer, so it sorts numerically)*

xml id, associated to primary key in other data stores (SQL)

### `text`

*on `text` nodes, 100.0%, 47 of 47*

Name of an Aramaic text, often a manuscript

### `manuscript`

*on `text` nodes, 100.0%, 47 of 47*

The manuscript that a text witnesses, carried by `text` nodes.

### `view`

*on `text` nodes, 100.0%, 47 of 47*

Grouping of segments based on editorial and emendation filters present in the text

## The ceilings, and why they belong to the source

| feature | coverage | why it stops there |
|---|---|---|
| `ps` person | **absent** | the source column is null on every analysed unit |
| `vt` tense and aspect | **absent** | likewise null throughout |
| voice | **absent** | likewise null throughout |
| `prs`, `nme`, `pfm`, `vbe`, `uvf` | **absent** | no source for them at all |
| `vs` stem | partial | the source vocabulary encodes the stem and nothing else, and some verbs carry none |
| `gn` gender | partial | recorded for a minority of the noun entries this corpus uses, and the limit is the lexicon's |
| `nu`, `st` | partial | partial in the lexicon, and part of the `st` population is a value the source itself marks as ambiguous |

This column states the kind of limit rather than a figure. The measured coverage of each of these
features is in the feature table above, where it is recomputed on every rebuild.

**Verbal morphology would be new annotation here rather than extraction.** The source returns the
stem and that is the whole of it. The three empty columns are deliberately **not dropped** from
the database, because a dropped column cannot be re-measured, so counting them remains the
falsification of this claim for anyone who doubts it.

**Segmentation stops at the proclitic.** Most source words are a single unit and the mean is a
little above one, so the decomposition is real and it is prefixal. Enclitics do not split,
although the source flags the boundary where a preposition carries a pronominal suffix, which is
one unit holding two morphemes of which the second has been named. Nouns and verbs with suffixes
carry no flag at all, so any count taken from that flag is a floor.

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
| `uid` | `verse` | The verse key of the relational source, with the same family scoping problem. Read the canonical address instead, since `(book, chapter, verse)` is a section path and `T.nodeFromSection(('Genesis', 1, 1))` resolves. |
| `text` on `word` | `word` | A byte-for-byte copy of the word's own `cons_utf8`, published under a name that the text node also used, so one feature held both word values and manuscript names while `text` was a structure feature besides. Measured, no value differed from `cons_utf8`. Read `cons_utf8`. |
| `language` | `word` | A constant. Every token of the corpus carried the single value `Aramaic`, so the feature answered no question while occupying a feature file of its own. Read `dialect` in the database for the isolect of a text. |
| `lex_dialects`, `gloss_norm`, `voc_lex` | `lexeme` | Properties of a dictionary entry rather than of this corpus, each covering a minority of the lexeme tier and each recoverable from the lexicon the lexeme names. Read `lex0` to group the vocabulary, and `gloss` and `definition` for the published translation. |
| `nametype` | `word` | The onomastic category of a proper noun. Withdrawn to keep the published word tier to what the manuscript and its analysis state. The words themselves are unaffected and resolve to a lexical entry as before. |
| `piece`, `pieces` | `word` | Ordinals of the internal segmentation model, numbering the whitespace-delimited parts of a lexical entry filed as several orthographic words. Withdrawn because they describe the model rather than the text. The split itself is published, in that no `cons` value holds an internal space. Read `part`, which numbers the editorial division of a word. |
| `variant` | `word_group` | A description of the witness a reading comes from. Withdrawn because all but a handful of the readings that carried a value held one repeated legend sentence, which also named an internal file reference that a consumer cannot resolve. Read the segment `type`, which states the editorial state of the reading, and `reading`, which orders the candidates. |

## What is recorded but is not a feature

**The editorial flag register.** 13,121 published words carry one or more open
editorial exceptions, across 23 distinct reasons, and these are deliberately not a
Text-Fabric feature. A flag is an editorial working state that changes as a campaign resolves
rows, whereas a published feature is frozen at the rebuild, so it would be stale the following
day. Two of its levels are not coverage gaps but stated uncertainty about claims this dataset
publishes regardless: the words whose assignment to a reading is unconfirmed, and those whose
morpheme boundary is unproved. Query the register directly in PostgreSQL:

```sql
SELECT word_uid, flag FROM neofiti_full_mat_next WHERE flag IS NOT NULL;
```

**The witness a reading comes from.** 15,506 published readings carry a mark identifying
the witness, of which 22 carry one that the legend of the source does not describe.
Neither the mark nor its description is published as a feature. The mark alone is an internal
code that means nothing without its description, and the descriptions themselves proved to be
one repeated legend sentence on all but a handful of readings. The editorial state of a reading is
published, as the segment `type` and the `reading` ordinal.

## The absent syntactic tier, as a non-goal

This corpus has **no phrase, clause or sentence tier**, and will not acquire one in this release.
That is a stated non-goal rather than an omission. The source supplies no syntactic annotation,
so a syntactic tier would be new scholarly annotation of 640,353 words rather than extraction. A
consumer trained on the BHSA, where phrase, clause and sentence are node types and `function`,
`rela` and `typ` are features, will find none of them here, and should read the absence as this
dataset declining to invent them.
