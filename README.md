# The ETCBC Targum Corpus
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23785216.svg)](https://doi.org/10.5281/zenodo.23785216) [![License: CC BY-NC 4.0](https://img.shields.io/badge/license-CC_BY--NC_4.0-red)](https://creativecommons.org/licenses/by-nc/4.0/deed.en)


This repository contains [Text-Fabric](https://annotation.github.io/text-fabric/tf/) representations of Jewish Aramaic translations of the Hebrew Bible, known collectively as Targums or Targummim (sing. 'Targum'). The datasets contain linguistic annotations in accordance with other Text-Fabric datasets such as the [BHSA](https://github.com/ETCBC/bhsa) as maintained by the [Eep Talstra Centre for Bible and Computer](https://etcbc.nl/), as well as the [Samaritan Pentateuch](https://github.com/DT-UCPH/sp) and [Peshitta](https://github.com/etcbc/syriac) as  maintained by the [CACCT project](https://github.com/CACCHT).

PostgreSQL and XML datasets are included as well, in addition to Extract-Transform-Load (ETL) pipelines to convert from SQL to XML to Text-Fabric.

---
## Quickstart

This data is best processed using [Context-Fabric](https://github.com/Context-Fabric/context-fabric). The [Text-Fabric](https://github.com/annotation/text-fabric) API is used throughout; for those unfamiliar with the Text Fabric API, we recommend the [start](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/start.ipynb) and [search](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/search.ipynb) tutorials, both of which use the BHSA database of the Hebrew Bible. The data is also provided in XML and SQL format for those who want to look at intermediate representations.

Dependencies can be found in the Pipfile and can be installed using `pipenv`:

``` python
cd path/to/this/directory
pipx install pipenv
pipenv shell
pipenv install
```

Once the dependencies are installed within your pipenv environment, the easiest way to start querying the Targum data is via Jupyter notebook. [quickstart.ipynb](programs/quickstart.ipynb) is a guided tour of the corpus: it loads the dataset, lists what the dataset contains, reads a verse across different manuscripts, compares the same verse across the witnesses, and runs a series of searches.

---

## Texts

The following Targummim are included:

* **Pseudo-Jonathan:** British Library Add. Ms. 27031 (Clark, 1984)
* **Fragment Targums** (Klein, 1980):
  - **Fragment P:** Paris, ms. hebr. 110
  - **Fragment V:** Biblioteca Apostolica, Vatican, Ebr. 440
  - **Fragment N:** Nürnberg Stadtbibliothek, Solg. 2,2
* **Cairo Genizah Targum Fragments** (Klein, 1992): A, AA, B, BB, Br, C, CC, D, DD, E, EE, F, F2, FF, G, GG, H, HH, I, J, JJ, K, KK, LL, M, MM, NN, PP, Q, R, RR, S, T, U, W, X, Y, Z
* **Neofiti:** MS Neofiti, no. 1 ([Vatlib Digital View](https://digi.vatlib.it/view/MSS_Neofiti.1))
* **Onqelos:** (Bar Ilan text, based off of mss from Sperber 1959)

The texts of Pseudo-Jonathan, Fragment Targums, and Cairo Genizah Fragments include a small number of variant readings. 
The texts of Neofiti and Onqelos contains thousands of variant readings and emendations. To retain this scribal and editorial layer as first order data, two views of Neofiti are provided:

  - A 'full text' view that includes the base text alongside those short variant readings inserted in the manuscript interlinearly and in marginalia. Long form marginalia are included as well; and 
  - A 'base raw' view that excludes variants and other editorial emendations.

---

## Features

All text features are based on the ETCBC conventions. Feature naming adhere more closely to the [ETCBC Syriac corpus](https://github.com/ETCBC/syriac) than the [BHSA](https://github.com/ETCBC/bhsa/) conventions to support interoperability between Aramaic corpora.

Consonantal texts use Aramaic square script, and vocalization of Targummim use the Tiberian vowel system.

### Word-Level Features

- **`cons`**: Consonantal text of the realized word in ETCBC transcription
- **`cons_utf8`**: Consonantal text of the realized word in Aramaic square script
- **`g_cons`**: Consonantal text of a word group in ETCBC transcription
- **`g_cons_utf8`**: Consonantal text of a word group in Aramaic square script
- **`voc`**: Vocalized text of the realized word in ETCBC transcription
- **`voc_utf8`**: Vocalized text of the realized word in Aramaic square script
- **`g_voc`**: Vocalized text of a word group in ETCBC transcription
- **`g_voc_utf8`**: Vocalized text of a word group in Aramaic square script
- **`lex`**: Lexeme in ETCBC transcription
- **`lex0`**: `lex` with the disambiguation material removed
- **`lex_utf8`**: Lexeme in Aramaic square script
- **`freq_lex`**: How many words of the corpus carry this lexeme
- **`rank_lex`**: Position of the lexeme in the frequency list of the corpus
- **`gloss`**: English gloss
- **`definition`**: Extended translation or dictionary definition
- **`description`**: Description of a text, view, word or lemma
- **`sp`**: Part of speech
- **`vs`**: Verbal stem / binyan
- **`gn`**: Gender (nominal only, partial)
- **`nu`**: Number (nominal only, partial)
- **`st`**: Nominal state (abs/emph/cons, partial)
- **`trailer`**: Content after a word (empty space or `None`)
- **`root`**: Root, typically of a verb
- **`part`**: Which part of a word this node is, counting from 1, where an editorial boundary divides one printed word in two
- **`source`**: Provenance of a word. `word` where the morphology was placed on the word itself, `word_group` where the group carries a surface form that no morphology points at, `none` where the manuscript records a word carrying no analysis, and `segment` where the word stands in for a segment that no analysed word reaches
- **`uid`**: Independent unique identifier of the node
- **`id`**: Identifier carried over from the relational representation

### Position and Text Features

- **`line`**: Vocalized text of a verse in ETCBC transcription
- **`line_utf8`**: Vocalized text of a verse in Aramaic square script
- **`segment`**: Vocalized text of a segment in ETCBC transcription
- **`segment_utf8`**: Vocalized text of a segment in Aramaic square script
- **`start_idx`**: One-based character offset of the first character of a word or segment within `line`
- **`end_idx`**: One-based character offset of the last character of a word or segment within `line`, so that `substr(line, start_idx, end_idx - start_idx + 1)` returns it
- **`rank`**: Ordinal position of a node among its siblings within the line, counting from the start of the enclosing node
- **`reading`**: Which reading of a word group this is. Readings competing for one position of the line share a `rank` and differ here, 0 being the reading the edition prints
- **`type`**: Type of the node, such as `unmarked_text` for a segment or `full_text` for a view

### Node Hierarchy

- **`text`**: Name of an Aramaic text, often a manuscript
- **`manuscript`**: The manuscript that a text witnesses
- **`book`**: Name of a Biblical book
- **`chapter`**: Chapter of the book
- **`view`**: Grouping of segments based on editorial and emendation filters present in the text
- **`verse`**: A line of text, typically (though not always) corresponding to a verse in a book or manuscript
- **`segment`**: Grouping of words and word groups based on position within discrete editorial or emendation blocks (e.g., variants)
- **`word_group`**: Word groups (space-delimited units of characters, including immediately ensuing variants; contains at least one word)
- **`lexeme`**: One node per lexeme of the corpus, carrying the lexical data that would otherwise be repeated on every token of it
- **`word`**: Words (slots), the smallest semantic elements, carrying number, gender, part of speech and the rest of the morphology

### Edge Features

- **`parent`**: Edge between a node and its parent node
- **`sibling`**: Edge between a node and each of its preceding sibling nodes, labelled with the distance between them
- **`crossref`**: Parallel witnesses. An edge between two `verse` nodes that carry the same canonical `(book, chapter, verse)` address

--- 
## Data Model

More details on the data model can be found in the forthcoming article:

> "Graph Datasets of the Jewish Aramaic Pentateuch"