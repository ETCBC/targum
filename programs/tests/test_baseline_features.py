"""Whether a feature carries what its name and its documentation say it carries.

Ordinals against publication order, the transliteration's own conventions, the lexeme
inventory, the two features that were once named for something other than their
content, every feature counted by the node type its values actually fall on, and the
features this version added."""

import csv
import json
import os
import re
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

import yaml

import baseline_corpus as C

# The measurement bodies below read the corpus handles and helpers by bare name.
# `C.exports()` publishes them into this module once the corpus is loaded, which is
# why each measurement calls it before doing anything else.


# TEST 6. Agreement of the stored ordinals with the publication order.
#
# Method: within each verse, read the segments and the word groups in node order, the order the
# dataset publishes, and count the adjacent pairs whose stored ordinal decreases. For segments the
# ordinals are `rank` and `start_idx`. For word groups the ordinal is the pair (`rank`, `reading`),
# because groups competing for one position share a rank and are ordered among themselves by
# reading. The final column tests whether the ranks of the word groups of a verse form a dense
# sequence starting from zero, the property that makes rank usable as a word index.
#
# What it measures: whether a consumer reading the corpus in node order and a consumer sorting by
# the stored ordinals obtain the same sequence. An inversion would allow a verse to be published in
# an order that its own features contradict, a fault the preceding tests would not detect, because
# each of them reads in node order throughout.
@C.once
def run_06_ordinals_agree_with_node_order():
    C.setup()
    globals().update(C.exports())
    test6 = defaultdict(Counter)
    for _k, _vns in verse_nodes.items():
        _r = test6[corpus_of_verse[_k]]
        _r["verses"] += 1
        segs = [s for v in _vns for s in L.d(v, otype="segment")]
        ranks = [F.rank.v(s) for s in segs]
        starts = [F.start_idx.v(s) for s in segs]
        _r["segments"] += len(segs)
        _r["segment_rank_inversions"] += sum(
            1 for a, b in zip(ranks, ranks[1:]) if a is not None and b is not None and b < a)
        _r["segment_span_inversions"] += sum(
            1 for a, b in zip(starts, starts[1:]) if a is not None and b is not None and b < a)
        gs = [(F.rank.v(g), F.reading.v(g)) for v in _vns for g in L.d(v, otype="word_group")]
        _r["word_groups"] += len(gs)
        _r["group_order_inversions"] += sum(1 for a, b in zip(gs, gs[1:]) if b < a)
        slots = {rank for rank, _ in gs}
        _r["slot_rank_dense"] += sorted(slots) == list(range(len(slots)))

    table("TEST 6  stored ordinals against publication order", test6,
          ["verses", "segments", "segment_rank_inversions", "segment_span_inversions",
           "word_groups", "group_order_inversions", "slot_rank_dense"],
          pct=[("% dense", "slot_rank_dense", "verses")])
    results["6 ordinals agree with node order"] = (
        sum(test6[c]["verses"] for c in CORPORA), sum(test6[c]["slot_rank_dense"] for c in CORPORA))


def test_06_ordinals_agree_with_node_order():
    _mark = len(C.violations)
    run_06_ordinals_agree_with_node_order()
    C.assert_own(_mark, "06_ordinals_agree_with_node_order")


# TEST 7. Case, spacing and stray diacritics in the ETCBC transliterated features.
#
# Method: count, per feature, the nodes whose value contains a lowercase letter. In the scheme
# the transliteration module defines, a lowercase letter is the final form of its consonant, so
# that `n` is a final nun against a medial `N`. The only lowercase letters that occur are
# `k m n p y`, and
# they are finals and nothing else. `y` is a final tsade, not a yod: yod is `J`.
#
# That is this repository extending ETCBC rather than following it. BHSA writes `MLK>` and
# `<BDJK`, all uppercase, because in Hebrew the final form is positionally predictable and so
# carries no information. Here the language is agglutinative and the decomposition of the source
# joins words, which is why a final letter can appear mid-string, and the
# reviewer who raised this read those 128 cases as errors. They are not errors; they are the
# reason the distinction cannot be re-derived from position.
#
# The distinction is nonetheless redundant HERE, which is what makes uppercasing safe. Every
# square-script column is derived directly from the source transliteration, selecting the final
# glyph from the
# own case; `ETCBC_TRANSLITERATION_HEBREW_CONSONANTS` is referenced only by its own definition
# and there is no ETCBC -> Hebrew path at all. So the final form is recorded twice, once in the
# square script and once in the case of a transliteration that claims to be ETCBC, and it is the
# transliteration that is wrong about itself. `upper()` is applied at the publication boundary,
# the stored columns keep the case of the source, and uppercasing preserves length so that the
# offsets still resolve.
#
# What it measures: whether the published transliteration is ETCBC. Every column must be 0.
#
# Two further integrity populations ride along. The internal space in `cons` USED TO BE
# deliberate. A lexical entry filed as several orthographic words occupied a single slot, and
# the space was restored so that the published line reconstructed character for character, which
# is why every other test here compares through `letters()`. The figure was asserted at its
# documented size of 2,750 rather than at zero, and the measurement described splitting those runs as
# deferred work for which the figure was the starting point.
#
# That work has since been done, and the expectation is now 0. A multi-word surface is split on
# its own whitespace and each part takes its own slot, which affects 5,636 words. No published
# consonantal form holds an internal space, so this check is an invariant rather than a pinned
# ceiling: a space returning to the feature would mean that a surface had reached the slot tier
# unsplit. The ordinals that number those parts are not published, because they describe the
# internal segmentation model rather than the text, so this check is the published evidence that
# the split occurred.
# U+0740 is the Genizah lacuna mark, and zero is the wrong expectation for it. This is a
# correction to the first version of this measurement. Measured over the published corpus there are 11
# occurrences in `voc` and 1,093 in `g_voc`, and every one of the 11 is a word whose ENTIRE `voc`
# is a run of three to seven dots, with no `id`, no `cons` and no offset: a lacuna standing in
# for a word, which is the one place the mark belongs. None of the 11 is on a word the
# morphology was placed on. On the group tier 837 of the 1,093 are mixed with letters, which is a
# partially lacunose orthographic word and is equally correct. So the invariant is not absence but
# segregation: the mark must never share a word with a letter, and the published line must hold
# none at all. It holds none, which is exactly why those 11 words are correctly unlocated.

# `lex0` is `lex` with the BHSA disambiguation material removed, so it is an ETCBC string in its
# own right and has to fold with the rest. It is named conditionally because this measurement has to run
# against a dataset compiled before the feature existed as well as after.
@C.once
def run_07_the_etcbc_features_are_uppercase():
    C.setup()
    globals().update(C.exports())
    ETCBC_WORD = ("cons", "voc", "lex", "root") + (
        ("lex0",) if hasattr(F, "lex0") else ())
    ETCBC_GROUP = ("g_cons", "g_voc")
    _LOWER = re.compile(r"[a-z]")
    DOT = "\u0740"


    def lowercase_in(s):
        return bool(s) and bool(_LOWER.search(s))


    test7 = defaultdict(Counter)
    for _k, _vns in verse_nodes.items():
        _r = test7[corpus_of_verse[_k]]
        for _v in _vns:
            _r["verses"] += 1
            _r["line"] += lowercase_in(F.line.v(_v))
            _r["line_u0740"] += DOT in (F.line.v(_v) or "")
            for _s in L.d(_v, otype="segment"):
                _r["segments"] += 1
                _r["segment"] += lowercase_in(F.segment.v(_s))
            for _g in L.d(_v, otype="word_group"):
                _r["word_groups"] += 1
                for _f in ETCBC_GROUP:
                    _r[_f] += lowercase_in(Fs(_f).v(_g))
                _gv = F.g_voc.v(_g) or ""
                _r["g_voc_u0740"] += DOT in _gv
                _r["g_voc_u0740_mixed"] += DOT in _gv and bool(_gv.strip(DOT + " "))
            for _w in L.d(_v, otype="word"):
                _r["words"] += 1
                _clean = True
                for _f in ETCBC_WORD:
                    _val = Fs(_f).v(_w)
                    _bad = lowercase_in(_val)
                    _clean &= not _bad
                    _r[_f] += _bad
                    _r[f"{_f}_mid"] += lowercase_in(_val[:-1] if _val else None)
                _r["words_upper"] += _clean
                _r["cons_space"] += " " in (F.cons.v(_w) or "").strip()
                _vv = F.voc.v(_w) or ""
                _r["voc_u0740"] += DOT in _vv
                # The two ways the mark could be wrong: sharing a word with a letter, or sitting on a
                # word the morphology was placed on rather than on a stand-in for a missing one.
                _r["voc_u0740_mixed"] += DOT in _vv and bool(_vv.strip(DOT + " "))
                _r["voc_u0740_on_a_word"] += DOT in _vv and F.source.v(_w) == "word"

    table("TEST 7  lowercase in the ETCBC features, by tier", test7,
          ["words", "cons", "voc", "lex", "root", "word_groups", "g_cons", "g_voc",
           "verses", "line", "segments", "segment"])
    print()
    table("TEST 7  a final letter written mid-string, and the two diacritic populations", test7,
          ["words_upper", "cons_mid", "voc_mid", "lex_mid", "root_mid",
           "cons_space", "voc_u0740", "voc_u0740_mixed", "voc_u0740_on_a_word",
           "g_voc_u0740", "g_voc_u0740_mixed", "line_u0740"])
    print()

    _t7 = Counter()
    for _c in CORPORA:
        _t7.update(test7[_c])
    for _f in (*ETCBC_WORD, *ETCBC_GROUP, "line", "segment"):
        check(f"lowercase in `{_f}`", _t7[_f], 0,
              "lowercase is the final form; the ETCBC features are uppercased at the "
              "publication boundary and the final glyph stays in the *_utf8 columns")
    for _f in ETCBC_WORD:
        check(f"a final letter mid-string in `{_f}`", _t7[f"{_f}_mid"], 0)
    # Segregation, not absence. The 9 and the 94 are pinned as ceilings, the way `cons_space` is.
    check("U+0740 sharing a word with a letter", _t7["voc_u0740_mixed"], 0,
          "a lacuna mark on a word that has letters of its own is a stray diacritic; a word "
          "that is nothing but lacuna marks is a lacuna, and that is all 9 of them")
    check("U+0740 on a word the morphology reached", _t7["voc_u0740_on_a_word"], 0)
    check("U+0740 in `line`", _t7["line_u0740"], 0,
          "the published line carries no lacuna mark, which is why the 9 lacuna words "
          "carry no offset into it")
    check("U+0740 in `voc`", _t7["voc_u0740"], 11,
          "DOCUMENTED: 11 words whose whole surface is a lacuna, 9 in neofiti_full and 2 in the "
          "Genizah material. `voc_u0740_mixed` holds the invariant at 0")
    check("U+0740 in `g_voc`", _t7["g_voc_u0740"], 1093,
          "DOCUMENTED: 999 Genizah, 89 neofiti_full and 5 base_raw groups. 837 are a lacuna beside "
          "letters, which is a partially lacunose orthographic word and is equally correct")
    check("internal space in `cons`", _t7["cons_space"], 0,
          "the multi-word surfaces are split on their own whitespace, so each part now takes its "
          "own slot. An invariant since the rebuild, where it had been a pinned ceiling of 2,750. "
          "A space returning to this feature means a surface reached the slot tier unsplit")

    results["7 the ETCBC features are uppercase"] = (
        sum(test7[c]["words"] for c in CORPORA), sum(test7[c]["words_upper"] for c in CORPORA))


def test_07_the_etcbc_features_are_uppercase():
    _mark = len(C.violations)
    run_07_the_etcbc_features_are_uppercase()
    C.assert_own(_mark, "07_the_etcbc_features_are_uppercase")


# TEST 8. The lexeme inventory of each corpus, against the inventory of the corpora whose `lex`
# is drawn from a lemma.
#
# Method: collect the distinct lexemes per corpus, then count how many of them occur in neither
# Neofiti corpus. Those two are the reference set because they are the only two whose `lex` the
# view layer sourced from the lemma tree, while the other three read the surface column of the
# analysed unit. All five corpora are analysed against one dictionary, so a lexeme attested in
# Pseudo-Jonathan and in no Palestinian Targum is either genuine Late Jewish Literary Aramaic
# vocabulary or an artefact, and the proportion tells which.
#
# What it measures: whether `lex` is a lexeme at all. A surface form inflates the inventory
# without limit, because `>JTJHJBT`, `D>JTJHJBT` and `W>JTJHJBT` are three values where the lemma
# `JHB` is one, and almost none of them can recur in another corpus by chance. `lex_eq_cons` is
# the same fact read a second way: a lexeme equals the surface form only where the word is
# uninflected and unprefixed, so a high rate at four letters or more is the signature of a
# surface-form lexeme, and the verb column is the sharpest form of it, because an Aramaic verb
# is
# practically never its own dictionary headword.
#
# Interpretation. The inventory figures are now pinned, because they have been measured off the
# regenerated view bodies rather than predicted: 2,484 / 2,281 / 2,946 / 1,824 / 1,183 distinct
# lexemes, 2,500 in the reference union and 3,692 in the corpus as a whole, against 20,779
# before. The three corpora that used to publish a surface form fall from 14,104 / 5,794 / 2,970
# values outside the reference inventory to 1,016, 176 and 149, so 90.9 per cent of what looked
# like Pseudo-Jonathan vocabulary was an artefact of the source column, and what is left is the
# right order of magnitude for genuine Late Jewish Literary Aramaic.
#
# Set sizes are pinned and node counts are not. A distinct-value count is the same whether it is
# taken over matview rows or over TF nodes, because `generate_xml` merges only words whose whole
# attribute dictionary is identical, the lexeme included. The two word counts count nodes,
# so they are reported and left to the `results` row.
#
# `lex_eq_cons` stops being a defect measure here and the columns are kept for continuity. With a
# surface-form lexeme the equality was itself the defect, whereas with a lemma it is ordinary,
# since an unprefixed singular noun is its own headword. The figure therefore rises even though
# the fault is gone. The
# column that still means something is the verb one: 14,233 verbs equalled their own surface form
# before and 93 do after, because an Aramaic verb is practically never its dictionary headword.
#
# It reads `lex0` where the dataset has one. Following BHSA, `lex` carries the disambiguation
# material, which is `[` for a verb, `/` for a noun, and zero or more `=` signs for lexemes
# sharing consonants. `lex0` is the same value with that material removed. The inventory question
# is about the lexeme, so it is asked of the undisambiguated form.
@C.once
def run_08_the_lexeme_inventory_of_each_corpus():
    C.setup()
    globals().update(C.exports())
    LEX0 = "lex0" if hasattr(F, "lex0") else "lex"
    print(f"reading the lexeme from `{LEX0}`"
          + ("" if LEX0 == "lex0" else "  (no `lex0` in this dataset yet)"))

    test8 = defaultdict(Counter)
    lex_sets = defaultdict(set)
    _lexf = Fs(LEX0)
    for _k, _vns in verse_nodes.items():
        _c = corpus_of_verse[_k]
        _r = test8[_c]
        for _v in _vns:
            for _w in L.d(_v, otype="word"):
                _lex, _cons = _lexf.v(_w), F.cons.v(_w)
                _r["words"] += 1
                _r["lex_present"] += _lex is not None
                if _lex is None:
                    continue
                lex_sets[_c].add(_lex)
                _r["lex_eq_cons"] += _lex == _cons
                if _cons is not None and len(_cons) >= 4 and _lex == _cons:
                    _r["eq_4plus"] += 1
                    _r["eq_4plus_verb"] += F.sp.v(_w) == "verb"

    _reference = lex_sets["neofiti_base_raw"] | lex_sets["neofiti_full"]
    for _c in CORPORA:
        test8[_c]["distinct_lex"] = len(lex_sets[_c])
        test8[_c]["distinct_outside"] = len(lex_sets[_c] - _reference)

    for _k, _vns in verse_nodes.items():
        _r = test8[corpus_of_verse[_k]]
        for _v in _vns:
            for _w in L.d(_v, otype="word"):
                _lex = _lexf.v(_w)
                if _lex is not None and _lex not in _reference:
                    _r["words_outside"] += 1

    table("TEST 8  the lexeme inventory, against the lemma-sourced corpora", test8,
          ["words", "lex_present", "distinct_lex", "distinct_outside", "words_outside"],
          pct=[("% of the inventory outside", "distinct_outside", "distinct_lex"),
               ("% of words", "words_outside", "lex_present")])
    print()
    table("TEST 8  the lexeme that is its own surface form", test8,
          ["lex_present", "lex_eq_cons", "eq_4plus", "eq_4plus_verb"],
          pct=[("% lex == cons", "lex_eq_cons", "lex_present")])
    print()
    print(f"  {len(_reference):,} distinct lexemes in the reference inventory; "
          f"{len(set().union(*lex_sets.values())):,} in the corpus as a whole")
    print()


def test_08_the_lexeme_inventory_of_each_corpus():
    _mark = len(C.violations)
    run_08_the_lexeme_inventory_of_each_corpus()
    C.assert_own(_mark, "08_the_lexeme_inventory_of_each_corpus")


# TEST 9. Two features that carry something other than what they are named for.
#
# `gloss` is non-null on every word in the corpus, which is not a fact about lexical coverage.
# The
# tail of its COALESCE in the view layer is `concat_ws(', ', category, description)`, the same
# expression published beside it as `description`, so where the source has no gloss of any kind
# and no full definition, `gloss` is handed the lexical category, which is the literal value
# "nominal, proper name". A consumer filtering on a non-null gloss therefore receives the whole
# corpus.
# `gloss_is_a_category` names that population.
#
# `text` is two features under one name. The word element's character data is set from
# `cons_utf8` and the XML converter promotes element text to a feature called `text`, while the
# schema already carries `text` for the manuscript name, and `text` is a section feature
# (`@sectionFeatures=text,book,chapter`), so the collision is with the corpus's own spine. The two
# halves never disagree: across every word that has one, `text` differs from `cons_utf8` in zero
# cases, and that is the proof that the word half carries no information and can simply stop
# being emitted. This test asserts both the redundancy and its removal, so it keeps its value
# after the fix: if `text` ever comes back on a word carrying something of its own, the first
# check fails rather than the second.
@C.once
def run_09_a_feature_name_means_one_thing():
    C.setup()
    globals().update(C.exports())
    test9 = defaultdict(Counter)
    for _k, _vns in verse_nodes.items():
        _r = test9[corpus_of_verse[_k]]
        for _v in _vns:
            for _w in L.d(_v, otype="word"):
                _g, _d, _t = F.gloss.v(_w), F.description.v(_w), F.text.v(_w)
                _r["words"] += 1
                _r["gloss_present"] += _g is not None
                _r["gloss_is_a_category"] += _g is not None and _g == _d
                _r["has_definition"] += F.definition.v(_w) is not None
                _r["carries_text"] += _t is not None
                _r["text_differs"] += _t is not None and _t != F.cons_utf8.v(_w)

    table("TEST 9  gloss against description, and the word half of `text`", test9,
          ["words", "gloss_present", "gloss_is_a_category", "has_definition",
           "carries_text", "text_differs"],
          pct=[("% gloss is a category", "gloss_is_a_category", "gloss_present")])
    print()

    _t9 = Counter()
    for _c in CORPORA:
        _t9.update(test9[_c])
    check("`text` on a word differing from `cons_utf8`", _t9["text_differs"], 0,
          "the word half of `text` is a byte-for-byte copy of cons_utf8; if this is ever "
          "non-zero it has started carrying information and must not simply be dropped")
    check("word nodes carrying `text`", _t9["carries_text"], 0,
          "`text` is also the section feature of the `text` node type; the word half is "
          "redundant and is no longer emitted")
    check("words whose `gloss` is a lexical category", _t9["gloss_is_a_category"], 0,
          "the COALESCE tail hands `gloss` the value published beside it as `description`")

    results["9 `text` is one feature"] = (
        sum(test9[c]["words"] for c in CORPORA),
        sum(test9[c]["words"] - test9[c]["carries_text"] for c in CORPORA))


def test_09_a_feature_name_means_one_thing():
    _mark = len(C.violations)
    run_09_a_feature_name_means_one_thing()
    C.assert_own(_mark, "09_a_feature_name_means_one_thing")


# TEST 11. Every node feature counted by the node type its occurrences actually fall on.
#
# The method is to read the backing store of each node feature directly, which is a mapping
# keyed by node number, and to tally the node type of every key. That makes the matrix exact and
# inexpensive,
# over all 495,216 slots and every higher node, rather than sampled.
#
# What it measures: whether a feature name means ONE thing. Cell 3 above asks a version of this
# question from the first 400 nodes of each type, which describes the dataset well enough to read
# the tests by, but cannot see a feature that lives overwhelmingly on one type and occasionally on
# another. That is exactly the shape of the fault the review found: `text` is the manuscript name
# on 68 `text` nodes and the surface form on 490,496 words, and it is also a SECTION feature, so
# the collision is with the corpus's own addressing. Nothing in the serialisation chain could have
# caught it, because the word half is produced by the XML converter promoting element character
# data to a feature and therefore has no row in the published schema and no source column. It is
# the one feature
# in the dataset outside the contract the `views_tf` docstring claims is total.
#
# Some names legitimately measure one quantity at two tiers, and the assertion is that the
# overloaded set is EXACTLY those: `id` is an identifier, the same kind of thing wherever it
# appears, and `rank`, `start_idx` and `end_idx` are the ordinal and the two offsets, defined the
# same way for a word, a word group and a segment. `text` was a sixth, and the only one whose two
# readings were different kinds of thing. This is the generic guard: it fails on the NEXT such
# feature without anyone having to think of it.
#
# The two groups are now named apart, because they are permitted for
# different reasons:
#
#   `lex`, `lex0` and `lex_utf8` are overloaded deliberately. The lexeme node type is additive,
#   in that it carries the lexical data that was previously repeated on every token,
#   and BHSA likewise carries `lex` on `word` and on its own `lex` node type. The same string
#   at both tiers is the same kind of thing, which is precisely the test this measurement applies, so
#   they belong in the allowed set rather than in an exemption.
#
#   `uid` has left that group, because the verse identifier is withheld. Such an identifier
#   collides almost
#   completely across the three family tables, so a consumer joining on it read the wrong row
#   silently. It is now a word feature only, and the second check below would have read that
#   as a tier that stopped carrying it. The check is therefore split, so that the tier pairs
#   must
#   still be paired, and `uid` is asserted to be single-tier, so re-publishing it at the verse
#   tier fails here rather than passing quietly.
@C.once
def run_11_every_feature_counted_by_its_node_type():
    C.setup()
    globals().update(C.exports())
    TIER_PAIRS = {"id", "rank", "start_idx", "end_idx"}
    LEXEME_TIER = {"lex", "lex0", "lex_utf8"}
    ALLOWED_OVERLOAD = TIER_PAIRS | LEXEME_TIER

    _types = list(F.otype.all)
    matrix = {}
    for _f in sorted(api.Fall()):
        if _f == "otype":
            continue
        _c = Counter()
        for _n in Fs(_f).data:
            _c[F.otype.v(_n)] += 1
        matrix[_f] = _c

    _w0 = max(len("feature"), max(len(f) for f in matrix))
    _w = {t: max(len(t), 9) for t in _types}
    print("TEST 11  node features by the node type they occur on")
    print("  " + "feature".ljust(_w0) + "  " + "  ".join(t.rjust(_w[t]) for t in _types)
          + "  " + "types".rjust(5))
    print("  " + "-" * _w0 + "  " + "  ".join("-" * _w[t] for t in _types) + "  " + "-" * 5)
    for _f, _c in matrix.items():
        _mark = "" if len(_c) == 1 else ("  <- tier pair" if _f in ALLOWED_OVERLOAD
                                         else "  <- OVERLOADED")
        print("  " + _f.ljust(_w0) + "  "
              + "  ".join((f"{_c[t]:,}" if _c[t] else "-").rjust(_w[t]) for t in _types)
              + f"  {len(_c):>5}" + _mark)
    print()

    overloaded = {f for f, c in matrix.items() if len(c) > 1}
    print(f"  overloaded: {', '.join(sorted(overloaded)) or 'none'}")
    print(f"  allowed:    {', '.join(sorted(ALLOWED_OVERLOAD))}")
    check("features overloaded across node types", len(overloaded - ALLOWED_OVERLOAD), 0,
          "a name carrying two different kinds of thing: "
          + (", ".join(sorted(overloaded - ALLOWED_OVERLOAD)) or "none"))
    check("tier-pair features that lost their second tier",
          len(ALLOWED_OVERLOAD - overloaded), 0,
          "`id`, `rank`, `start_idx` and `end_idx` are each defined at more than one tier, and "
          "`lex`, `lex0` and `lex_utf8` are published on `word` and on `lexeme`, and one of them "
          "falling "
          "back to a single type means a tier stopped carrying it")
    check("`uid` tiers, after the verse identifier was withheld", len(matrix["uid"]), 1,
          "a word feature only. Unit identifiers collide across the three family tables, so a "
          "consumer joining on `verse/@uid` read the wrong row silently")

    results["11 a feature name means one thing"] = (
        len(matrix), sum(1 for f, c in matrix.items() if len(c) == 1 or f in ALLOWED_OVERLOAD))


def test_11_every_feature_counted_by_its_node_type():
    _mark = len(C.violations)
    run_11_every_feature_counted_by_its_node_type()
    C.assert_own(_mark, "11_every_feature_counted_by_its_node_type")


# TEST 12. The features added in this version, and whether they say what they claim.
#
# The method is to assert that each feature sits on the tier the documentation places it on, and
# then to assert the property that makes it worth publishing. A feature that exists and is wrong
# is worse than one that is absent, because a consumer has no means of telling. A feature read
# from the wrong tier is worse still, because it returns None without raising.
#
# This version publishes six features that the previous release did not. Four of them sit on the
# lexeme tier, which is itself new, and one on the manuscript tier. The sixth is the parallel
# witness edge, which test 14 covers in full.
#
# A larger set of candidates was considered and withheld, and the assertions below require each
# of them to be absent. Three classes account for all of them. The first is identifiers of the
# relational source, whose values a consumer cannot resolve. The second is values recoverable
# from the rest of the dataset. The third is values that do not vary, which answer no question
# while occupying space on every node of their tier. Asserting absence matters as much as
# asserting presence, because a withdrawn feature that returns in a later rebuild would be a
# silent change to a citable dataset.
@C.once
def run_12_the_features_of_this_version():
    C.setup()
    globals().update(C.exports())
    _WORD_TIER = ["lex0", "lex_utf8"]
    _LEXEME_TIER = ["lex0", "lex_utf8", "freq_lex", "rank_lex"]
    _TEXT_TIER = ["manuscript"]

    # Withheld deliberately. `lex_id` and `lex_key` were identifiers, `language` and `dialect` did not
    # vary usefully, `lex0` already recovers what `lex_dialects`, `gloss_norm` and `voc_lex` were
    # consulted for at the lexeme tier, and `variant`, `nametype`, `piece` and `pieces` were either
    # a single legend sentence or an ordinal of the internal segmentation model.
    _WITHDRAWN = ["lex_id", "lex_key", "language", "dialect", "lex_dialects", "gloss_norm",
                  "voc_lex", "variant", "nametype", "piece", "pieces"]

    _all_features = TF_FEATURES


    def _occurs_on(feat, otype):
        """How many nodes of `otype` carry `feat`.

        The result is 0 both when the feature is absent from the dataset and when it is present on
        another tier, which is the confusion this measurement exists to detect.
        """
        if feat not in _all_features:
            return 0
        _f = Fs(feat)
        return sum(1 for _n in F.otype.s(otype) if _f.v(_n) is not None)


    print("TEST 12  the features of this version, and the tier each one occupies")
    _tiers = [("word", _WORD_TIER), ("lexeme", _LEXEME_TIER), ("text", _TEXT_TIER)]
    for _otype, _feats in _tiers:
        for _f in _feats:
            _n = _occurs_on(_f, _otype)
            print(f"  {'ok  ' if _n else 'FAIL'}  {_f:<13} on {_otype:<7} {_n:>8,} nodes")
            check(f"`{_f}` occurs on the `{_otype}` tier", int(_n > 0), 1,
                  "declared in config/xml.yml and emitted by tf_pipeline.SCHEMA_ROWS")
    print()

    print("TEST 12  the features withheld from this version")
    for _f in _WITHDRAWN:
        _absent = _f not in _all_features
        print(f"  {'ok  ' if _absent else 'FAIL'}  {_f:<13} is withheld and absent")
        check(f"`{_f}` is absent from the dataset", int(not _absent), 0,
              "withheld as an unresolvable identifier, a recoverable value or a constant")
    print()

    # The word to lexeme relation. The lexeme tier is resumed and is not contained by the text tree,
    # so a lexeme node's slots are distributed across the corpus and containment is the only route
    # from a word to the properties of its lexeme.
    C.SHARED["lexeme_of"] = lexeme_of = {}
    for _lx in F.otype.s("lexeme"):
        for _w in L.d(_lx, otype="word"):
            lexeme_of[_w] = _lx

    _MARKERS = set("[/=")
    test12 = defaultdict(Counter)
    for _k, _vns in verse_nodes.items():
        _r = test12[corpus_of_verse[_k]]
        for _v in _vns:
            for _w in L.d(_v, otype="word"):
                _r["words"] += 1
                _lex, _lex0 = F.lex.v(_w), F.lex0.v(_w)
                _lx = lexeme_of.get(_w)
                _r["lex_utf8"] += F.lex_utf8.v(_w) is not None
                _r["lexeme_node"] += _lx is not None
                if _lex0 is None and _lex is None:
                    _r["no_lexeme"] += 1
                    continue
                _r["lexeme"] += 1
                # The disambiguation shape, asserted per word rather than in aggregate. This single
                # predicate catches a marker placed on the wrong base, a base that has drifted away
                # from the lexeme it belongs to, and a stray character in either.
                _ok = (_lex is not None and _lex0 is not None
                       and _lex.startswith(_lex0)
                       and set(_lex[len(_lex0):]) <= _MARKERS)
                _r["bhsa_shaped"] += _ok
                _r["pos_marker"] += bool(_lex) and (_lex.endswith("[") or "/" in _lex)
                _r["homonym_marker"] += "=" in (_lex or "")
                # A word that carries a lexeme but reaches no lexeme node would be one whose lexical
                # identity nothing published can state. This is the assertion that makes withdrawing
                # the lexeme identifier payable.
                _r["lexeme_without_node"] += _lx is None

    table("TEST 12  coverage of the lexical features", test12,
          ["words", "lexeme", "no_lexeme", "lex_utf8", "lexeme_node"],
          pct=[("% with a lexeme", "lexeme", "words"),
               ("% reaching a lexeme node", "lexeme_node", "words")])
    print()
    table("TEST 12  the disambiguation shape", test12,
          ["lexeme", "bhsa_shaped", "pos_marker", "homonym_marker", "lexeme_without_node"],
          pct=[("% carrying a marker", "pos_marker", "lexeme")])
    print()

    _t12 = Counter()
    for _c in CORPORA:
        _t12.update(test12[_c])
    check("`lex` not built on `lex0`", _t12["lexeme"] - _t12["bhsa_shaped"], 0,
          "every lexeme must be `lex0` followed only by characters drawn from `[`, `/` and `=`")
    check("lexeme-bearing words that reach no `lexeme` node", _t12["lexeme_without_node"], 0,
          "containment is the only edge from a word to its lexeme, so a word that reaches no "
          "lexeme node has no published lexical identity")

    # `rank_lex` carries the identity of the lexeme tier, which is why the tier needs no separate
    # key. The ranking is total rather than dense, so it is a bijection onto the lexeme nodes, and
    # the assertion is that property rather than mere presence: a dense ranking would give every
    # hapax legomenon the same value and would identify nothing.
    _ranks = [F.rank_lex.v(_lx) for _lx in F.otype.s("lexeme")]
    _n_lexemes = len(_ranks)
    print(f"  {_n_lexemes:,} lexeme nodes, ranks {min(_ranks):,} to {max(_ranks):,}, "
          f"{len(set(_ranks)):,} distinct")
    check("lexeme nodes sharing a `rank_lex`", _n_lexemes - len(set(_ranks)), 0,
          "a total ranking is a bijection onto the lexeme nodes, which is what allows the tier to "
          "be keyed on it")
    check("gaps in the `rank_lex` sequence", sorted(_ranks) != list(range(1, _n_lexemes + 1)), False,
          "the ranking must cover 1 to the number of lexemes without a gap")

    # `freq_lex` is counted over the four distinct witnesses and deliberately not over the base view
    # of Neofiti, which is a second view of a manuscript already counted. A lexeme attested only in
    # that view therefore has a frequency of 0, which is the honest value rather than a missing one.
    _freqs = [F.freq_lex.v(_lx) for _lx in F.otype.s("lexeme")]
    print(f"  {sum(_freqs):,} tokens counted across {_n_lexemes:,} lexemes, "
          f"{sum(1 for _f in _freqs if _f == 0)} of them attested only in the base view")
    check("lexeme nodes with no `freq_lex`", sum(1 for _f in _freqs if _f is None), 0,
          "the frequency is counted for every lexeme, and 0 is a value rather than an absence")
    print()

    # The manuscript tier. `text` names the manuscript everywhere except Neofiti, where two views
    # describe one codex, so the collapse from 46 text nodes to 45 manuscripts is the whole content
    # of this feature and is what test 14 relies on to tell a parallel from a view.
    _ms = Counter(F.manuscript.v(_t) for _t in F.otype.s("text"))
    _n_texts = sum(_ms.values())
    print(f"  {_n_texts} text nodes over {len(_ms)} manuscripts")
    for _m, _n in sorted(_ms.items(), key=lambda kv: (-kv[1], kv[0] or "")):
        if _n > 1:
            print(f"    {str(_m):<34} {_n:>4} text nodes")
    check("text nodes with no `manuscript`", _ms[None], 0,
          "every text node names the manuscript it witnesses")
    check("manuscripts carrying more than one text node",
          sum(1 for _n in _ms.values() if _n > 1), 1,
          "exactly one manuscript is published under two views, and that is Neofiti 1")
    print()

    results["12 the features of this version say what they claim"] = (
        _t12["words"], _t12["words"] - (_t12["lexeme"] - _t12["bhsa_shaped"])
                                     - _t12["lexeme_without_node"])


def test_12_the_features_of_this_version():
    _mark = len(C.violations)
    run_12_the_features_of_this_version()
    C.assert_own(_mark, "12_the_features_of_this_version")

