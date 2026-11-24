"""The corpus, the shared helpers, and the state the baseline tests record into.

Importing this module costs nothing. `setup()` loads the corpus and builds the material every
test shares, and it is memoised, so the first test to need it pays and the rest do not.

The suite is split by category across `test_baseline_*.py`. Run it as pytest, or run
`python -m programs.tests.baseline_report` for the full report, the summary table and the gate.
"""
from __future__ import annotations

import functools
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from dotenv import load_dotenv

import cfabric

# ## The corpus
#
# The corpus holds Onqelos, Targum Pseudo-Jonathan, the Fragment
# Targums, Cairo Genizah fragments, and Targum Neofiti. Neofiti is represented in two views, a
# 'base' text that keeps only unmarked segments, excluding variants and interlinear or in-line
# additions, and a 'full' text that places every segment side by side. The text is Jewish Aramaic (Babylonian for Onqelos, Palestinian for everything else), carried in ETCBC transliteration and in Aramaic square script.
#
# # Tests
# The object hierarchy is `text > book > chapter > verse > segment > word_group > word`, and `word`
# is the slot type. A `lexeme` tier sits above `word` and is the one node type not contained within
# the text tree, since the occurrences of a lexeme are distributed across the whole corpus.
# `word_group` is included as a step toward full consistency across the hierarchy while the
# underlying data model continues to develop. The segment `type` feature records the editorial
# state of a run of text, with values including `unmarked_text`, `variant`, `addition`,
# `editorial_deletion`, `broken_text`, and `interlinear`. Segments and words both carry `start_idx`
# and `end_idx`, one-based character offsets into the `line` feature of the verse that contains
# them. A segment's offsets are the minimum and the maximum of the offsets of the words it holds, so
# the two tiers agree by construction.
#
# Two features record how a word relates to the published line. `source` is `word` where
# morphological analysis was placed directly on the word, `word_group` where the group carries a
# surface form that the analysis does not individually cover, `none` where the manuscript records a
# word that carries no morphological analysis at all, and `segment` where the word stands in for a
# segment that no analysed word reaches, carrying that segment's own text so the segment can still
# be published. `part` counts the parts of a word that an editorial boundary cuts in two. The two
# parts share their `word_group` and its `id`, each sits in the segment that its own characters
# fall in, and a word with `part` 1 and no sibling is whole. Because a split word group occupies
# two nodes, the tests below that speak of a word group treat all nodes sharing one `id` as a
# single unit.
#
# ## Baseline tests
#
# Tests 1 to 5 move up through the object hierarchy and ask whether a given tier of nodes
# reconstructs the tier above it, for example whether the segments of a verse reconstruct the verse
# line. Test 4 also resolves the segment offsets against the line they index. Test 6 checks whether
# the stored ordinals agree with the order in which the dataset publishes its nodes.
#
# Each test reports its figures per corpus, because the five corpora differ substantially in how
# much morphological analysis their source material provides.
#
# ### Reading the results
#
# Tests 1, 3, 4, and 5 report figures that vary by corpus, reflecting properties of the source
# material. Most of the failures fall into two categories, which the second table of test 1
# isolates: surface forms whose morphological analysis covers only part of the word, and a
# diacritic written one way at the word tier and another way at the word group tier.
#
# Test 2 reports a figure that describes the publication boundary itself. A word that straddles two
# editorial states is contained by only one segment, leaving the other segment without a word group
# that spells it. The same effect limits the proportion of segment spans whose slice returns the
# segment, and the proportion of verses whose segments spell the line, both reported in test 4.
#
# ## Interoperability tests
#
# Tests 7 to 14 ask a different kind of question. Tests 1 to 6 measure a corpus whose figures
# legitimately vary by manuscript, so they assert almost nothing and their table is their report.
# Tests 7 to 14 state invariants, and each one is either true of the published dataset or is a
# defect in it. They were written in response to an external review of the dataset, and most of
# them failed on the build that the review read.
#
# Test 7 asks whether the published transliteration is ETCBC. Lowercase is a private extension of
# this project, in which a lowercase letter is the final form of its consonant. The BHSA writes
# every consonant uppercase, because in Hebrew the final form is predictable from position. Here it
# is not, which is why a final letter can appear mid-string, but it is recorded a second time in
# the square-script features, so the ETCBC features are uppercased at the publication boundary.
# Two integrity populations ride along with that check. The internal space that a multi-word
# lexical entry once left in the consonantal form is now absent, so that figure is an invariant at
# zero rather than a pinned ceiling. The Genizah lacuna mark is deliberate, which is a correction
# to the first version of this suite. Every one of its occurrences in the vocalised form is a
# word whose entire surface is a run of dots, standing in for a word the manuscript has lost, so
# the invariant is that the mark never shares a word with a letter rather than that it never
# occurs. Its population rose when the line coordinate was corrected to carry the chapter, which
# publishes every line reference the Genizah material holds rather than one for each verse
# number, so the figure is a wider view of the same notation and not a change to it.
#
# Test 8 asks whether `lex` is a lexeme. It counts the distinct lexemes of each corpus and how many
# of them appear in neither Neofiti corpus, those being the two whose lexeme the view layer drew
# from the lemma tree rather than from the surface column of the word, and it reads the same fact a
# second way as the words whose `lex` equals their `cons`. Its inventory figures are pinned,
# because they were measured against the regenerated view bodies before the rebuild and are
# therefore a prediction that the rebuild has to reproduce. Its node counts are reported, because a
# node count is not a set size.
#
# Test 9 covers two features that carried something other than what they are named for: `gloss`,
# whose fallback handed it the lexical category published beside it as `description`, and the word
# half of `text`, which was a byte-for-byte copy of `cons_utf8` published under the name of the
# section feature of the corpus.
#
# Test 10 is the section census, and the figures it pins are a documented ceiling rather than a
# target. A chapter 0 is the corpus stating that an unlocalised fragment names its book and not its
# chapter, and turning it into a chapter 1 would be a fabrication. It passes, and is the regression
# guard.
#
# Test 11 counts every node feature by the node type its occurrences fall on, and asserts that the
# only names present at two tiers are those that measure one quantity at two tiers. It is the
# generic form of what test 9 found by hand, and it fails on the next such feature without anyone
# having to anticipate it.
#
# Test 12 covers the features that this version publishes and the previous one did not, together
# with the larger set of candidates that were considered and withheld. For each feature present it
# asserts the property that makes the feature worth publishing rather than merely its presence, and
# for each feature withheld it asserts absence. Both directions matter. A feature read from the
# wrong tier returns `None` without raising, which is the sharpest reason to assert the tier and
# not the name, and a withheld feature that returned in a later rebuild would be a silent change to
# a citable dataset. The strongest of the assertions are structural. For every word that has a
# lexeme, `lex` must begin with `lex0` and the remainder must be drawn from `[`, `/` and `=` and
# nothing else, which catches a marker on the wrong base, a base that has drifted, and a stray
# character in one statement. For the lexeme tier, `rank_lex` must be a total ranking covering 1 to
# the number of lexemes without a gap, because that property is what allows the tier to be keyed on
# it and is why no separate lexeme identifier is published.
#
# Test 13 asks where the lexeme and the surface disagree, and decomposes the words that share no
# letter with their own lexeme into the causes that account for them. Two causes that earlier
# versions could name are no longer separable from published features, so those words now fall
# through to the remaining rows and the unexplained row is reported rather than pinned.
#
# Test 14 is the parallel witness edge, `crossref`, which is a feature of the core data rather than
# a module to be fetched alongside it. Two verses are parallel when they carry the same book,
# chapter and verse, so the relation is given by the data and is not inferred, and there is no
# similarity threshold and no choice of method. The test asserts that the edge is that relation: it
# is symmetric in both directions, never joins two addresses, never leaves two nodes at one address
# unjoined, and is labelled correctly across all three of `witness`, where the manuscripts differ
# and the relation is a parallel, `view`, where one manuscript is read two ways, which is Neofiti 1
# and nothing else, and `same_witness`, where one manuscript under one view holds two verse records
# at one address, which nothing in the corpus now does. It ends in four worked examples, because the
# purpose of the edge is the questions it makes inexpensive.
#
# Test 15 is the publication key, and it is the gate the six original tests could not
# provide. A line record keyed on the verse number alone cannot separate two references in one
# manuscript that share that number, and the collision is silent, so one mis-keyed component
# publishes a transcription at an address it does not belong to, duplicates the enclosing chapter,
# and drops references from the dataset with nothing to record their absence. The test asserts that
# no manuscript publishes one transcription at two interleaving addresses, that an address is one
# verse node, and that the addresses which only a chapter-bearing and book-bearing key can express
# are still there to be counted. That last figure is coverage stated from inside the dataset, since
# comparing the dataset against the source's own list of references would need the source.
#
# Each of these reports through `check`, which records a failure and continues, so that one run
# produces every figure. The last stage is the gate.

# Recorded rather than raised, so that one run produces every figure. Each test asserts only the
# violations it added itself, and the report form asserts the total at the end.
violations: list[tuple] = []

# The population and pass count of each test, keyed by the name the summary prints.
results: dict[str, tuple[int, int]] = {}

# The two artefacts that cross between modules: the word-to-lexeme map built while the features
# of this version are tested, and the classification performed while the lexeme is tested against
# its surface. Both are reached through this dictionary rather than through import order.
SHARED: dict[str, object] = {}

_TET = "V"                       # The ETCBC tet in this transliteration scheme.
_NOT_ETCBC = re.compile(r"[^A-Z><]")
_WS = re.compile(r"\s+")


def once(fn):
    """Run at most once, and return what the first call returned.

    Every measurement is wrapped in this, so a module that needs another module's figures can
    simply call for them without caring whether pytest has run that module yet.
    """
    @functools.wraps(fn)
    def wrapper(*a, **kw):
        if not hasattr(wrapper, "_value"):
            wrapper._value = fn(*a, **kw)
        return wrapper._value
    return wrapper


def check(name, got, want, note=""):
    """Record a failure and continue, rather than stopping on the first one.

    The six original tests measure a corpus whose figures legitimately vary by manuscript, so
    they assert almost nothing and their tables are the report. A check is different in kind:
    it states something that is either true of the published dataset or is a defect in it.
    """
    ok = got == want
    if not ok:
        violations.append((name, got, want, note))
    tail = "" if ok else f"  expected {want:,}"
    print(f"  {'ok  ' if ok else 'FAIL'}  {name:<46} {got:>9,}{tail}")
    if not ok and note:
        print(f"          {note}")
    return ok


def assert_own(mark, name):
    """Fail the calling test on the violations it added, naming each one."""
    mine = violations[mark:]
    assert not mine, f"{name}: " + "; ".join(
        f"{n} carries {g!r}, expected {w!r}" for n, g, w, _ in mine)


# The names the measurement bodies read by bare name. `setup()` creates most of them, so they
# cannot be imported at module load, and `exports()` publishes them afterwards instead.
EXPORTS = (
    "api F E L T S Fs Es TF_FEATURES TF_VERSION TF_DIR REPO_ROOT ORG REPO CF meta tf_meta "
    "plain letters etcbc_letters table check violations results CORPORA corpus_of verse_nodes "
    "corpus_of_verse VERSE_KEY_COLUMNS _TET _NOT_ETCBC _WS declared SHARED"
).split()


def exports():
    """The shared namespace, for a test module to publish into its own globals."""
    setup()
    g = globals()
    missing = [n for n in EXPORTS if n not in g]
    assert not missing, f"setup() did not define: {', '.join(missing)}"
    return {n: g[n] for n in EXPORTS}


def letters(s):
    """The comparison class used throughout.

    Strips whitespace so that strings drawn from different tiers, which do not always agree on
    how much space they record, can still be compared fairly.
    """
    return _WS.sub("", s or "")


def etcbc_letters(s):
    """ETCBC consonants only.

    `cons` can also hold the lacuna dots, and that is not a letter the lexeme could be expected
    to share.
    """
    return _NOT_ETCBC.sub("", s or "")


# Loads the dataset and reports its provenance. The version string, the version of the XML the
# dataset was compiled from, and the compilation timestamp are read from the metadata of the
# `otype` feature, which every Text-Fabric dataset carries. The node counts printed here are the
# quantities every later test is measured against.
#
# The corpus is loaded through context-fabric rather than through the advanced application layer
# of Text-Fabric, and three consequences follow from that.
#
# First, the corpus is addressed by path rather than by organisation and repository.
# `cfabric.Fabric(locations, modules)` reads the versioned dataset directory directly, so the
# suite depends neither on an environment resolving a repository name nor on an environment
# file existing at all. That is what allows this file to run unchanged in a fresh checkout.
#
# Second, context-fabric loads from its own binary cache, which retains feature values and
# discards the header block that carries the metadata. The metadata available through the library
# is therefore empty, and the provenance reported below depends on it, so `tf_meta` reads the
# header out of the shipped feature file itself. That is not a workaround. It reads the artefact
# being published rather than a library's parse of it, so it cannot disagree with what ships. The
# binary cache also holds no staleness check against the feature files beside it, which is why
# the pipeline deletes it after every compile, and reading the files directly is immune to the
# question either way.
#
# Third, there is no advanced application layer, so the helper defined below replaces it and
# prints rather than rendering markup, which keeps the output legible in a terminal and in a
# difference listing.
#
# The version is deliberately not pinned here. The declared version of the dataset is
# read from the application configuration, which is the same value the compiler writes into the
# metadata of every feature, so this suite cannot describe an older build than the dataset
# ships. An earlier version pinned the string as a literal and continued to report itself as
# current across a rebuild, which would have described a superseded corpus throughout.
# Defines the material shared by every test below.
#
# `letters` is the comparison class used throughout. It strips whitespace so that strings drawn
# from different tiers of the corpus, which do not always agree on how much space they record, can
# still be compared fairly.
#
# `verse_nodes` keys each verse by the pair (manuscript, uid). The `uid` feature is unique within
# one corpus and repeats across corpora, so the manuscript name is needed to make the key unique.
# Every verse now occupies exactly one verse node. Two verses of the Genizah material once
# occupied more than one, because the order in which the dataset published their words did not
# keep the rows of those verses contiguous. The tests below still aggregate over the list of
# nodes that share a key, which costs nothing and keeps them from assuming a property of one
# build.
#
# `table` prints one row per corpus with a total, and takes derived percentage columns as
# (label, numerator, denominator) triples.
@once
def setup():
    import os
    from pathlib import Path

    import yaml
    from dotenv import load_dotenv

    import cfabric

    REPO_ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "config/xml.yml").exists())
    load_dotenv(REPO_ROOT / ".env")

    TF_VERSION = yaml.safe_load((REPO_ROOT / "app/config.yaml").read_text())["provenanceSpec"]["version"]
    TF_DIR = REPO_ROOT / "tf" / TF_VERSION

    # Kept for the provenance line only. Loading no longer goes through them.
    ORG = os.environ.get("TF_ORG") or "etcbc"
    REPO = os.environ.get("TF_REPO") or "targum"

    # The silence level is passed to both calls, because the loader takes its own. Without it the
    # library logs one line per feature as it loads, which is longer than most of the output below
    # and conveys nothing that the feature inventory does not. The accepted levels are "verbose",
    # "auto", "terse" and "deep".
    CF = cfabric.Fabric(locations=str(REPO_ROOT / "tf"), modules=TF_VERSION, silent="deep")
    api = CF.loadAll(silent="deep")
    F, E, L, T, S = api.F, api.E, api.L, api.T, api.S
    Fs, Es = api.Fs, api.Es
    TF_FEATURES = set(CF.features)


    def tf_meta(feature="otype"):
        """The `@`-metadata of one feature, read from the shipped `.tf` file.

        cfabric serves feature data out of its `.cfm` cache, which stores values and drops the `@`
        header, so `CF.features[f].metaData` is empty. Every `.tf` file opens with its own metadata
        block, terminated by the first line that does not start with `@`, so reading it is four lines
        and is authoritative about the artefact rather than about a cache of it.
        """
        out = {}
        path = TF_DIR / f"{feature}.tf"
        if not path.exists():
            return out
        with path.open(encoding="utf8") as fh:
            for line in fh:
                if not line.startswith("@"):
                    break
                if "=" in line:
                    key, value = line[1:].rstrip("\n").split("=", 1)
                    out[key] = value
        return out


    def plain(node, withNodes=True):
        """Print a node and the words it contains, in place of the app layer's `pretty`.

        One line of heading and one line per word: the vocalised surface, the lexeme, the part of
        speech and `source`, which together are what the failing measurements below are inspected for.
        """
        otype = F.otype.v(node)
        head = f"{otype} {node}" if withNodes else otype
        bits = []
        for name in ("id", "reading", "type", "verse", "chapter", "book", "text"):
            if name in TF_FEATURES:
                value = Fs(name).v(node)
                if value is not None:
                    bits.append(f"{name}={value!r}")
        print(f"{head}  {'  '.join(bits)}")
        for w in L.d(node, otype="word") if otype != "word" else (node,):
            print(f"    {w:>8}  {F.voc.v(w)!r:<22} lex={F.lex.v(w)!r:<14} "
                  f"sp={F.sp.v(w)!r:<8} source={F.source.v(w)!r}")


    meta = tf_meta("otype")

    declared = yaml.safe_load((REPO_ROOT / "config/xml.yml").read_text())["featureDescriptions"]

    import re
    from collections import Counter, defaultdict

    _WS = re.compile(r"\s+")


    def letters(s):
        return _WS.sub("", s or "")


    CORPORA = ["cairo_genizah", "frag_targ", "neofiti_base_raw", "neofiti_full", "psj","onq"]
    _BY_NAME = {"neofiti_base": "neofiti_base_raw", "neofiti_full": "neofiti_full",
                "pseudo_jonathan": "psj","onqelos":"onq"}


    def corpus_of(text_node):
        name = F.text.v(text_node)
        if name.startswith("cairo"):
            return "cairo_genizah"
        if name.startswith("fragment_targum"):
            return "frag_targ"
        return _BY_NAME[name]


    VERSE_KEY_COLUMNS = ("text_text", "book_book", "chapter_chapter", "verse_verse")

    verse_nodes = defaultdict(list)
    corpus_of_verse = {}
    for _t in F.otype.s("text"):
        _name, _corpus = F.text.v(_t), corpus_of(_t)
        for _v in L.d(_t, otype="verse"):
            _k = (_name, F.book.v(L.u(_v, otype="book")[0]),
                  F.chapter.v(L.u(_v, otype="chapter")[0]), F.verse.v(_v))
            verse_nodes[_k].append(_v)
            corpus_of_verse[_k] = _corpus


    def table(title, rows, cols, pct=(), key="corpus"):
        keys = [k for k in CORPORA if k in rows] + [k for k in rows if k not in CORPORA]
        totals = Counter()
        for k in keys:
            totals.update(rows[k])
        head = [key, *cols, *(lbl for lbl, _, _ in pct)]
        body = []
        for k in [*keys, "TOTAL"]:
            r = totals if k == "TOTAL" else rows[k]
            body.append([k, *(f"{r[c]:,}" for c in cols),
                         *(f"{100.0 * r[n] / r[d]:.2f}" if r[d] else "-" for _, n, d in pct)])
        w = [max(len(str(x)) for x in col) for col in zip(head, *body)]
        rule = "  ".join("-" * i for i in w)
        print(title)
        print("  " + "  ".join(h.rjust(i) for h, i in zip(head, w)))
        print("  " + rule)
        for line in body[:-1]:
            print("  " + "  ".join(str(x).rjust(i) for x, i in zip(line, w)))
        print("  " + rule)
        print("  " + "  ".join(str(x).rjust(i) for x, i in zip(body[-1], w)))


    results = {}
    print(f"{len(verse_nodes):,} verses distributed over "
          f"{sum(len(v) for v in verse_nodes.values()):,} verse nodes")

    globals().update({k: v for k, v in locals().items() if not k.startswith("__")})
    return True
