# The ETCBC Targum Corpus
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21925395.svg)](https://doi.org/10.5281/zenodo.21925395) [![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](https://opensource.org/license/mit)

This repository contains [Text-Fabric](https://annotation.github.io/text-fabric/tf/) representations of Jewish Aramaic translations of the Hebrew Bible, known collectively as Targums or Targummim (sing. 'Targum'). The datasets contain linguistic annotations in accordance with other Text-Fabric datasets such as the [BHSA](https://github.com/ETCBC/bhsa) as maintained by the [Eep Talstra Centre for Bible and Computer](https://etcbc.nl/), as well as the [Samaritan Pentateuch](https://github.com/DT-UCPH/sp) and [Peshitta](https://github.com/etcbc/syriac) as  maintained by the [CACCT project](https://github.com/CACCHT).

PostgreSQL and XML datasets are included as well, in addition to Extract-Transform-Load (ETL) pipelines to convert from SQL to XML to Text-Fabric.

> **Status:** These datasets are a work in progress and should be treated as in an **alpha** stage.

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

The texts of Pseudo-Jonathan, Fragment Targums, and Cairo Genizah Fragments include a small number of variant readings. 
The text of Neofiti contains thousands of variant readings and emendations. To retain this scribal and editorial layer as first order data, two views of Neofiti are provided:

  - A 'full text' view that includes the base text alongside those short variant readings inserted in the manuscript interlinearly and in marginalia; and 
  - A 'base raw' view that excludes variants and other editorial emendations.

Future versions of the data will include longer form marginalia, as well as other views of Neofiti which will incorporate different combinations of scribal and editorial emendations. 

---

## Features

All text features are based on the ETCBC conventions. Feature naming adhere more closely to the [ETCBC Syriac corpus](https://github.com/ETCBC/syriac) than the [BHSA](https://github.com/ETCBC/bhsa/) conventions to support interoperability between Aramaic corpora.

Consonantal texts use Aramaic square script, and vocalization of Palestinian Targummim use the Tiberian vowel system.

### Word-Level Features

* **`cons`**: Consonantal text of the realized word in ETCBC transcription
* **`cons_utf8`**: Consonantal text of the realized word in Aramaic square script
* **`voc`**: Vocalized text of the realized word in ETCBC transcription
* **`voc_utf8`**: Vocalized text of the realized word in Aramaic square script
* **`lex`**: Lexeme in ETCBC transcription
* **`gloss`**: English gloss
* **`definition`**: Extended translation or dictionary definition
* **`sp`**: Part of speech
* **`vs`**: Verbal stem / binyan
* **`gn`**: Gender (nominal only)
* **`nu`**: Number (nominal only)
* **`st`**: Nominal state (partial)
* **`trailer`**: Content after a word (empty space or `None`)
* **`root`**: Root, typically of a verb


### Node Hierarchy

* **`text`**: Name of an Aramaic text, typically by book
* **`book`**: Biblical book (typically Pentateuchal)
* **`chapter`**: Chapter of the Aramaic text (as applicable)
* **`verse`**: A line of text, typically (though not always) corresponding to a verse in a book or manuscript
* **`segment`**: Grouping of monads/monad groups based on position within discrete editorial or emendation blocks (e.g., variants)
* **`mg`**: MonadGroups (space-delimited units of characters, including immediately ensuing variants; contains at least one Monad)
* **`m`**: Monads (slots). Smallest elements with word-level features such as number, gender, and part of speech

### Planned Additions

Future versions will more completely address `gn`, `nu`, and `st`, alongside the introduction of:

* **`vt`**: Verbal tense
* **`vo`**: Voice
* **`ps`**: Person

--- 
## Data Model

More details on the data model can be found in the forthcoming article:

> "Graph Datasets of the Jewish Aramaic Pentateuch"