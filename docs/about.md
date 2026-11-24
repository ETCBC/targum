# The ETCBC Targum Corpus

Six Aramaic Targum corpora, reconciled against their diplomatic manuscript transcriptions and
published as Text-Fabric.

| | |
|---|---|
| word slots | 640,353 |
| verses | 26,094 |
| manuscripts | 46 |
| canonical `(book, chapter, verse)` addresses | 5,866 |
| features | 48 over 8 node types |

## The corpora

| corpus | what it is |
|---|---|
| `onqelos` | Targum Onqelos, the standard Babylonian Targum, after Sperber 1959 |
| `neofiti_full` | Codex Neofiti 1, full text including the marginal variants |
| `neofiti_base` | the same codex, base reading only, so one manuscript under two views |
| `pseudo_jonathan` | Targum Pseudo-Jonathan, after Clarke et al. 1984 |
| `fragment_targum_*` | the Fragment Targums, 4 recensions, after Klein 1980 |
| `cairo_genizah_targum_fragment_*` | 39 Cairo Genizah fragments, after Klein 1986 |

`neofiti_base` and `neofiti_full` are **not two witnesses**. The `crossref` edge states which
pairs are parallels between manuscripts, labelled `witness`, and which are two views of one
manuscript, labelled `view`, because counting them together makes the number of witnesses
attesting a verse wrong by one on every Neofiti verse. A third label, `same_witness`, is reserved
for one manuscript under one view holding more than one verse record at a single address, which
nothing in the corpus now does.

## Start here

* **[The features](transcription.md)**, all 48 of them, each with its measured coverage,
  the ceilings that belong to the source rather than to this dataset, the withdrawn features and
  what replaces them, and the two things that are recorded but are deliberately not features.
* `T.nodeFromSection(('Genesis', 1, 1))` resolves, because the three section levels are `book`,
  `chapter` and `verse`. The manuscript is reached through `structureTypes`, which carries
  `text -> book -> chapter -> verse`.
* A section address is shared between witnesses, with 5,853 of 5,866 addresses carried
  by more than one manuscript, so resolving a section answers with one witness's verse. Use the
  `crossref` edge or the structure to establish which.

## What this is not

**There is no syntactic tier**, and that is a stated non-goal. The source supplies no syntactic
annotation, so phrases, clauses and sentences would be new scholarly annotation of 640,353 words
rather than extraction. The same applies to person, tense and voice, whose source columns are
empty on every analysed unit, and the feature page gives the detail.

## Provenance

PostgreSQL is the source of truth, and the XML and Text-Fabric representations are regenerated
from it. **No identifier of the source lexicon is published.** Those identifiers are internal,
and the feature page names each feature withdrawn for that reason together with what replaces it.
