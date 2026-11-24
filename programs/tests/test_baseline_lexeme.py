"""The lexeme against the surface it was derived from.

Where the headword and the written form disagree about which letters they share, which
is mostly a substitution the source makes and partly a decomposition that attaches a
headword to a morpheme it does not spell. This test also performs the classification the
exclusion register reads, so it is kept in a module of its own."""

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
from test_baseline_features import run_12_the_features_of_this_version


# TEST 13. The lexeme against the surface, which is where `lex` and `cons` disagree about letters.
#
# The method is to ask, for every word that has both a lexeme and a surface form, whether any
# letter of `lex0` appears in `cons`. Two populations emerge, and they are unlike each other in
# both size and kind, which is why they are reported separately rather than as one failure count.
#
# The first is a letter the corpus had lost. The lemma identifiers of the source edition are
# lowercase, and its transliteration distinguishes tet from taw only by case, so a lowercased
# identifier cannot spell tet without colliding and the source substitutes another character for
# it. The character map used when the corpus was built held no entry for that substitute, so the
# conversion skipped it silently and the stored headword came out one letter short. An Aramaic
# corpus in which no lexeme and no root holds a tet is not a corpus with a rare letter. The fault
# has since been corrected in the transliteration and backfilled across the stored lemmas, so
# this measurement is now a regression guard rather than the original one.
#
# The assertion that the guard rests on has had to change, because it previously compared the
# published letter against the lemma identifier of the source, and that identifier is no longer
# part of the dataset. Two measurements replace it, and between them they cover more than the
# original did.
#
# Within the dataset, the identity becomes one that holds across two tiers. `lex0` is published
# on the lexeme tier as well as the word tier, so the question of whether the lemma spells a tet
# where the lexeme of the token does is answerable from published values alone. Both counts stand
# at 12,789, meaning the two tiers agree about the letter on every word that carries it, which is
# a stronger statement than the original, because it holds over values a consumer can read rather
# than over a key a consumer cannot resolve.
#
# Within the database, the classification that needs the identifier of the source remains in
# place and is still run, as four checks in the SQL baseline. They establish the reconstruction
# from the source lexicon with no rows left over, count what the missing letter cost, decompose
# the lemma that an analysed unit did not earn, and list the identifiers that resolve to nothing.
# That is the correct side of the boundary for them, since a question about an internal
# identifier belongs to the check that runs against the database rather than to the suite that
# measures the published artefact.
#
# The second population is a property of the lexical model and must not be read as a defect at
# all. The source attaches the headword of an entry to every analysed unit the entry covers, so a
# pronominal suffix or a one-letter clitic carries the lexeme of the word it attaches to. Of the
# words that share no letter with their lexeme, the decomposition below assigns each to exactly
# one cause, in order, and only the final row is unexplained. Most of that row is a one-letter
# surface.
#
# The predicates of the decomposition are drawn from published features only, which has cost it
# two rows. A compound lexical entry has no published proxy at all. A multi-word entry no longer
# has one either, now that the ordinal of the segmentation model is withheld: the only candidate
# predicate available, a word sharing its group, lexeme and part with another, admits 6,941 false
# positives against 5,636 true ones, so no proxy is offered in place of the measurement. Those
# words now fall through to the sibling, neighbour and unexplained rows, which is why the
# unexplained row is reported rather than pinned. A lemma spelled with a tet survives as a row,
# because the letter is now carried by `lex0` itself.
@C.once
def run_13_the_lexeme_belongs_to_its_surface():
    C.setup()
    globals().update(C.exports())
    run_12_the_features_of_this_version()
    test13 = defaultdict(Counter)
    _cand = {}                       # word -> (corpus, lex0 letters, cons letters)
    for _k, _vns in verse_nodes.items():
        _r = test13[corpus_of_verse[_k]]
        for _v in _vns:
            for _w in L.d(_v, otype="word"):
                _lex0, _cons = F.lex0.v(_w), etcbc_letters(F.cons.v(_w))
                _lx = C.SHARED["lexeme_of"].get(_w)
                _r["words"] += 1
                _r["tet_in_cons"] += _TET in _cons
                _r["tet_in_lex0"] += _TET in (_lex0 or "")
                _r["tet_in_root"] += _TET in (F.root.v(_w) or "")
                _r["tet_in_lexeme_tier"] += bool(_lx and _TET in (F.lex0.v(_lx) or ""))
                if not _lex0 or not _cons:
                    continue
                _r["comparable"] += 1
                if set(_lex0) & set(_cons):
                    continue
                _r["shares_no_letter"] += 1
                _cand[_w] = (corpus_of_verse[_k], _lex0, _cons)

    table("TEST 13  the tet the source substitutes, and what the lexeme kept of it", test13,
          ["words", "tet_in_cons", "tet_in_lex0", "tet_in_lexeme_tier", "tet_in_root"],
          pct=[("% of words whose lexeme spells one", "tet_in_lex0", "words")])
    print()

    # The decomposition. Each word falls in the first bucket that claims it, so the rows sum to
    # `shares_no_letter` and no word is counted twice.
    #
    # These rows do not match `baseline.sql` 16c's, and the reason is the node model rather than a
    # disagreement: a Text-Fabric `word_group` node is re-opened whenever its parent changes, so one
    # published `word_group_id` can be several nodes here, and a sibling that SQL finds inside the
    # group is found by the segment test instead. The total, and the transposition count the campaign
    # rests on, are identical either way.
    _BUCKETS = ["an abbreviation", "a lemma spelled with a tet",
                "the lemma of a sibling word", "the lemma of a neighbour", "unexplained"]
    _why = defaultdict(Counter)
    _why_of = {}                     # word -> its bucket, read by the exclusion register
    _transposed = set()
    C.SHARED["buckets"] = _BUCKETS
    C.SHARED["why_of"] = _why_of
    for _w, (_c, _lex0, _cons) in _cand.items():
        _group = (L.u(_w, otype="word_group") or (None,))[0]
        _siblings = [s for s in (L.d(_group, otype="word") if _group else []) if s != _w]
        _in_sibling = any(set(_lex0) <= set(etcbc_letters(F.cons.v(s))) for s in _siblings)
        # A transposition, meaning that the lexeme of this word is found in the surface of a sibling
        # while the lexeme of that sibling is found in this one, and neither is found in its own. No
        # process in the lexical model produces a mutual exchange of that kind.
        for _s in _siblings:
            if _s in _cand and set(_lex0) <= set(etcbc_letters(F.cons.v(_s))) \
                    and set(F.lex0.v(_s) or "") <= set(_cons):
                _transposed.add(_w)
        if "abbreviation" in (F.gloss.v(_w) or ""):
            _b = _BUCKETS[0]
        elif _TET in _lex0:
            _b = _BUCKETS[1]
        elif _in_sibling:
            _b = _BUCKETS[2]
        else:
            _segment = (L.u(_w, otype="segment") or (None,))[0]
            _near = [n for n in (L.d(_segment, otype="word") if _segment else [])
                     if (L.u(n, otype="word_group") or (None,))[0] != _group]
            _b = _BUCKETS[3] if any(set(_lex0) <= set(etcbc_letters(F.cons.v(n))) for n in _near) \
                 else _BUCKETS[4]
        _why[_b][_c] += 1
        _why[_b]["words"] += 1
        _why_of[_w] = _b

    _t13 = Counter()
    for _c in CORPORA:
        _t13.update(test13[_c])
    print("TEST 13  the words that share no letter with their own lexeme, by cause")
    print(f"  {'cause':<32} {'words':>8}")
    print("  " + "-" * 72)
    for _b in _BUCKETS:
        print(f"  {_b:<32} {_why[_b]['words']:>8,}")
    print("  " + "-" * 72)
    print(f"  {'TOTAL':<32} {sum(_why[_b]['words'] for _b in _BUCKETS):>8,}"
          f"   against shares_no_letter {_t13['shares_no_letter']:,}")
    print()
    _one_letter = sum(1 for _c, _l, _s in _cand.values() if len(_s) == 1)
    print(f"  {_one_letter:,} of the {_t13['shares_no_letter']:,} have a one-letter surface, "
          f"which is what a clitic or a pronominal suffix is")
    _groups = {(L.u(_w, otype='word_group') or (None,))[0] for _w in _transposed}
    print(f"  {len(_transposed):,} words in {len(_groups):,} word groups have their lemmas transposed")
    print()

    check("words whose lexeme holds a tet", _t13["tet_in_lex0"], 16091,
          "0 before the correction. Measured on the word tier against the 640,353-slot build")
    check("the lexeme tier disagreeing with the word tier about the letter",
          _t13["tet_in_lex0"] - _t13["tet_in_lexeme_tier"], 0,
          "the identity shared across the two tiers. `lex0` is published on `word` and on `lexeme`, "
          "and the two must spell the same lemma")
    check("words whose root holds a tet", _t13["tet_in_root"], 15370,
          "0 before the correction. Lower than `lex0` because the root covers fewer units, not "
          "because a letter was lost")
    check("words sharing no letter with their lexeme", _t13["shares_no_letter"], 10067,
          "a documented ceiling rather than a defect count. The source attaches the headword of an "
          "unit the entry covers. Re-pinned against the 640,353-slot build")
    check("word groups whose monads hold each other's lemma", len(_groups), 0,
          "all 14 were corrected in the source. This is an invariant rather than a ceiling, because "
          "no process in the lexical model produces a mutual exchange, so a new one is a defect")

    # The summary row: what is left to measure is how much of the lexeme-against-surface relation the
    # five rules above can ACCOUNT for, so the shortfall is the unexplained bucket and nothing else.
    results["13 the lexeme belongs to its surface"] = (
        _t13["comparable"], _t13["comparable"] - _why[_BUCKETS[-1]]["words"])


def test_13_the_lexeme_belongs_to_its_surface():
    _mark = len(C.violations)
    run_13_the_lexeme_belongs_to_its_surface()
    C.assert_own(_mark, "13_the_lexeme_belongs_to_its_surface")

