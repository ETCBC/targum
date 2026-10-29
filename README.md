# The ETCBC Targum Corpus
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21925395.svg)](https://doi.org/10.5281/zenodo.21925395) [![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](https://opensource.org/license/mit)

This repository contains [Text-Fabric](https://annotation.github.io/text-fabric/tf/) representations of Jewish Aramaic translations of the Hebrew Bible, known collectively as Targums or Targummim (sing. 'Targum'). The datasets contain linguistic annotations in accordance with other Text-Fabric datasets such as the [BHSA](https://github.com/ETCBC/bhsa) as maintained by the [Eep Talstra Centre for Bible and Computer](https://etcbc.nl/), as well as the [Samaritan Pentateuch](https://github.com/DT-UCPH/sp) and [Peshitta](https://github.com/etcbc/syriac) as  maintained by the [CACCT project](https://github.com/CACCHT).

PostgreSQL and XML datasets are included as well, in addition to Extract-Transform-Load (ETL) pipelines to convert from SQL to XML to Text-Fabric.

---

## Texts

The following Targummim are included:

* **Pseudo-Jonathan:** British Library Add. Ms. 2703 (Clark, 1984)
* **Fragment Targums** (Klein, 1980):
  - **Fragment P:** Paris, ms. hebr. 110
  - **Fragment V:** Biblioteca Apostolica, Vatican, Ebr. 440
  - **Fragment N:** Nürnberg Stadtbibliothek, Solg. 2,2
* **Cairo Genizah Targum Fragments** (Klein, 1992): A, AA, B, BB, Br, C, CC, D, DD, E, EE, F, F2, FF, G, GG, H, HH, I, J, JJ, K, KK, LL, M, MM, NN, PP, Q, R, RR, S, T, U, W, X, Y, Z
* **Neofiti:** MS Neofiti, no. 1 ([Vatlib Digital View](https://digi.vatlib.it/view/MSS_Neofiti.1))
* **Onqelos:** (Sperber 1959, Bible in Aramaic Vol I)

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
- **`g_lex`**: Realization of the lexeme in ETCBC transcription
- **`g_lex_utf8`**: Realization of the lexeme in Aramaic
- **`freq_lex`**: How many words of the corpus carry this lexeme
- **`rank_lex`**: Position of the lexeme in the frequency list of the corpus
- **`gloss`**: English gloss
- **`definition`**: Extended translation or dictionary definition
- **`sp`**: Part of speech
- **`vs`**: Verbal stem / binyan
- **`vt`**: Verbal tense
- **`vo`**: Voice
- **`ps`**: Person
- **`gn`**: Gender (nominal only, partial)
- **`nu`**: Number (nominal only, partial)
- **`st`**: Nominal state (abs/emph/cons, partial)
- **`trailer`**: Content after a word (empty space or `None`)
- **`root`**: Root, typically of a verb
- **`part`**: Which part of a word this node is, counting from 1, where an editorial boundary divides one printed word in two

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
- **`word`**: Words (slots)—the smallest semantic elements, carrying number, gender, part of speech and the rest of the morphology

### Edge Features

- **`parent`**: Edge between a node and its parent node
- **`sibling`**: Edge between a node and each of its preceding sibling nodes, labelled with the distance between them
- **`crossref`**: Parallel witnesses. An edge between two `verse` nodes that carry the same canonical `(book, chapter, verse)` address

--- 
## Data Model

More details on the data model can be found in the forthcoming article:

> "Graph Datasets of the Jewish Aramaic Pentateuch"