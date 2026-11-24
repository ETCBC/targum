"""The exclusion register, the summary table and the gate.

The register names every unit the suite does not validate, bucketed by the test that does
not validate it, and checks each bucket against the shortfall that test reported. Because
it compares itself against the other modules, it calls their measurements rather than
relying on the order pytest happens to run them in. Running this module alone therefore
runs the whole suite's measurements, which is the point: the register is only meaningful
beside the figures it is derived from."""

import csv
import json
import os
import re
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

import yaml

import baseline_corpus as C
from test_baseline_composition import (
    run_01_words_compose_the_word_group,
    run_02_words_compose_the_segment,
    run_03_word_groups_compose_the_verse_line,
    run_04_segments_compose_the_verse_line,
    run_05_words_compose_the_verse_line,
    run_the_word_tier_offsets_resolve,
)
from test_baseline_features import run_06_ordinals_agree_with_node_order
from test_baseline_lexeme import run_13_the_lexeme_belongs_to_its_surface
from test_baseline_structure import (
    run_10_sections_are_determined,
    run_15_the_publication_key,
)


_MEASUREMENTS = (
    run_01_words_compose_the_word_group,
    run_02_words_compose_the_segment,
    run_03_word_groups_compose_the_verse_line,
    run_04_segments_compose_the_verse_line,
    run_05_words_compose_the_verse_line,
    run_06_ordinals_agree_with_node_order,
    run_the_word_tier_offsets_resolve,
    run_10_sections_are_determined,
    run_13_the_lexeme_belongs_to_its_surface,
    run_15_the_publication_key,
)


# Writes the exclusion register: every unit this suite does not validate, bucketed by the test
# that does not validate it.
#
# The tests above report populations and pass rates, which say how much of the dataset is sound but
# not WHICH part. A consumer who wants only validated material, and a maintainer closing the gap,
# both need the units named. This module names them, and it is written here rather than in a script
# of its own so that it cannot drift from the figures above: the final check asserts that every
# bucket's size equals the shortfall the corresponding test reported.
#
# IDENTIFIERS, not node numbers. Node numbers are assigned by the compiler and move whenever the
# dataset is rebuilt, so a register keyed on them is worthless the moment it is useful. Each unit
# is therefore keyed on something the dataset carries about the unit itself:
#
#   word_group   `id`, which is also how test 1 groups the pieces of a split group
#   segment      `id`
#   word         `uid`, unique within one corpus
#   verse        its address, the (text, book, chapter, verse) tuple
#
# Every row additionally carries the address and the corpus, so a bucket can be read without the
# dataset in hand, and `n_slots`, the number of word slots the unit covers, so the cost of an
# exclusion is visible before it is taken.
#
# Three files are written, because the register answers three different questions.
#
#   baseline_exclusions.csv       one row per unit per bucket. The worklist.
#   baseline_excluded_slots.csv   one row per DISTINCT word slot implicated by any bucket, with
#                                 the buckets that implicate it. This is the filter a consumer
#                                 applies, since a slot is where every tier ultimately lands.
#   baseline_exclusions.json      the manifest: the build it was measured against, the key
#                                 convention, and every bucket with its population and shortfall,
#                                 including the buckets that are empty. An empty bucket is a
#                                 result and is recorded as one.
#
# A test that passes completely contributes an empty bucket rather than no bucket, so the absence
# of a name from this register always means validated and never means unexamined.
#
# One bucket is narrower than the figure printed above it, and deliberately. Test 13 counts 10,067
# words whose lexeme shares no letter with their surface, and it then accounts for all but 5,076 of
# them as abbreviations, lemmas spelled with the substituted letter, or the lemma of a sibling or
# neighbouring word. Those 4,991 are explained, the test counts them as passing, and the register
# does not name them. The bucket carries the unexplained remainder, read from the test's own
# classification rather than re-derived here, so the two cannot disagree about what counts as
# explained.
@C.once
def run_the_exclusion_register():
    C.setup()
    globals().update(C.exports())
    for _m in _MEASUREMENTS:
        _m()
    EXCL_DIR = REPO_ROOT / "data" / "exclusions"
    EXCL_DIR.mkdir(parents=True, exist_ok=True)

    # bucket -> (node type, [(corpus, text, book, chapter, verse, unit_id, n_slots, detail)])
    _buckets = OrderedDict()


    def _bucket(name, node_type):
        _buckets[name] = (node_type, [])
        return _buckets[name][1]


    _b1 = _bucket("1 words compose the word group", "word_group")
    _b2 = _bucket("2 words compose the segment", "segment")
    _b3 = _bucket("3 word groups compose the verse line", "verse")
    _b4 = _bucket("4 segments compose the verse line", "verse")
    _b5 = _bucket("5 words compose the verse line", "verse")
    _b6 = _bucket("6 ordinals agree with node order", "verse")
    _bo = _bucket("word offsets carried by the word tier", "word")
    _b10 = _bucket("10 sections are determined", "verse")
    _b13 = _bucket("13 the lexeme belongs to its surface", "word")
    _b15 = _bucket("15 the publication key", "verse")

    for _k, _vns in verse_nodes.items():
        _c = corpus_of_verse[_k]
        _text, _bk, _ch, _vs = _k
        _addr = (_c, _text, _bk, _ch, _vs)
        _line = max({F.line.v(_v) or "" for _v in _vns})

        # test 1, by the group's own id, as test 1 counts it
        _by_id = defaultdict(list)
        for _v in _vns:
            for _g in L.d(_v, otype="word_group"):
                _by_id[F.id.v(_g)].append(_g)
        for _gid, _nodes in _by_id.items():
            _ws = [_w for _g in _nodes for _w in L.d(_g, otype="word")
                   if F.source.v(_w) != "none"]
            if not _ws:
                continue
            if letters("".join(F.voc.v(_w) or "" for _w in _ws)) != letters(
                    F.g_voc.v(_nodes[0]) or ""):
                _b1.append((*_addr, _gid, len(_ws), "words do not spell the group"))

        # test 2, by the segment's own id
        for _v in _vns:
            for _s in L.d(_v, otype="segment"):
                _gs, _sw = L.d(_s, otype="word_group"), L.d(_s, otype="word")
                _target = letters(F.segment.v(_s))
                _every = letters("".join(F.voc.v(_w) or "" for _w in _sw))
                _base = letters("".join(F.voc.v(_w) or "" for _g in _gs
                                        if F.reading.v(_g) == 0
                                        for _w in L.d(_g, otype="word")))
                if not (_every == _target or _base == _target):
                    _b2.append((*_addr, F.id.v(_s), len(_sw),
                                "neither every reading nor the base reading spells the segment"))

        # test 3
        _seen, _built = set(), []
        for _v in _vns:
            for _g in L.d(_v, otype="word_group"):
                if F.id.v(_g) in _seen:
                    continue
                _seen.add(F.id.v(_g))
                _built.append(F.g_voc.v(_g) or "")
        _nslots = sum(len(L.d(_v, otype="word")) for _v in _vns)
        if letters("".join(_built)) != letters(_line):
            _b3.append((*_addr, "", _nslots, "the word groups do not spell the line"))

        # test 4
        _segs = [_s for _v in _vns for _s in L.d(_v, otype="segment")]
        if letters("".join(F.segment.v(_s) or "" for _s in _segs)) != letters(_line):
            _b4.append((*_addr, "", _nslots, "the segments do not spell the line"))

        # test 5
        _ws = [_w for _v in _vns for _w in L.d(_v, otype="word")]
        if "".join((F.voc.v(_w) or "") + (F.trailer.v(_w) or "")
                   for _w in _ws).strip() != _line:
            _b5.append((*_addr, "", _nslots, "the words do not spell the line exactly"))

        # the word tier's offsets, and test 13, both by the word's own uid
        for _w in _ws:
            if F.start_idx.v(_w) is None:
                _bo.append((*_addr, F.uid.v(_w), 1, "the word carries no offset into the line"))
            if C.SHARED["why_of"].get(_w) == C.SHARED["buckets"][-1]:
                _b13.append((*_addr, F.uid.v(_w), 1,
                             f"lex0 {F.lex0.v(_w)} shares no letter with cons "
                             f"{etcbc_letters(F.cons.v(_w))}, and no cause was found"))

    # test 10, which is counted over the text tier rather than over verse_nodes
    for _t in F.otype.s("text"):
        for _v in L.d(_t, otype="verse"):
            _chn = L.u(_v, otype="chapter")
            if not (F.verse.v(_v) is not None
                    and not (_chn and F.chapter.v(_chn[0]) in ("0", 0))):
                _b10.append((corpus_of(_t), F.text.v(_t),
                             F.book.v(L.u(_v, otype="book")[0]),
                             F.chapter.v(_chn[0]) if _chn else None, F.verse.v(_v),
                             "", len(L.d(_v, otype="word")),
                             "no verse number, or a chapter the source could not place"))

    # ---- write the worklist ----
    _COLS = ["test", "node_type", "corpus", "text", "book", "chapter", "verse",
             "unit_id", "n_slots", "detail"]
    with (EXCL_DIR / "baseline_exclusions.csv").open("w", newline="", encoding="utf8") as _fh:
        _wr = csv.writer(_fh)
        _wr.writerow(_COLS)
        for _name, (_nt, _rows) in _buckets.items():
            for _row in sorted(_rows, key=lambda _r: (_r[1], str(_r[2]), str(_r[3]),
                                                      str(_r[4]), str(_r[5]))):
                _wr.writerow([_name, _nt, *_row])

    # ---- write the slot filter: one row per distinct word slot, with its buckets ----
    _slot_tests = defaultdict(set)
    _slot_where = {}
    for _name, (_nt, _rows) in _buckets.items():
        for _row in _rows:
            _c, _text, _bk, _ch, _vs, _uid, _n, _detail = _row
            if _nt == "word":
                _nodes = []
                _slot_tests[(_text, _uid)].add(_name)
                _slot_where[(_text, _uid)] = (_c, _text, _bk, _ch, _vs)
    for _name, (_nt, _rows) in _buckets.items():
        if _nt == "word":
            continue
        for _row in _rows:
            _c, _text, _bk, _ch, _vs, _uid, _n, _detail = _row
            _vns = verse_nodes.get((_text, _bk, _ch, _vs), ())
            if _nt == "verse":
                _targets = [_w for _v in _vns for _w in L.d(_v, otype="word")]
            else:
                _targets = [_w for _v in _vns
                            for _u in L.d(_v, otype=_nt) if F.id.v(_u) == _uid
                            for _w in L.d(_u, otype="word")]
            for _w in _targets:
                _key = (_text, F.uid.v(_w))
                _slot_tests[_key].add(_name)
                _slot_where[_key] = (_c, _text, _bk, _ch, _vs)

    with (EXCL_DIR / "baseline_excluded_slots.csv").open("w", newline="", encoding="utf8") as _fh:
        _wr = csv.writer(_fh)
        _wr.writerow(["corpus", "text", "book", "chapter", "verse", "word_uid", "tests"])
        for _key in sorted(_slot_tests, key=lambda _k: (str(_k[0]), str(_k[1]))):
            _c, _text, _bk, _ch, _vs = _slot_where[_key]
            _wr.writerow([_c, _text, _bk, _ch, _vs, _key[1],
                          "; ".join(sorted(_slot_tests[_key]))])

    # ---- write the manifest ----
    _pop = {_n: _p for _n, (_p, _ok) in results.items()}
    _short = {_n: _p - _ok for _n, (_p, _ok) in results.items()}
    _manifest = {
        "measured_against": {
            "version": TF_VERSION,
            "xmlVersion": meta.get("xmlVersion"),
            "dateWritten": meta.get("dateWritten"),
        },
        "unit_key": {
            "word_group": "id", "segment": "id", "word": "uid",
            "verse": "the (text, book, chapter, verse) address",
        },
        "note": ("A unit absent from this register is validated by every test that examines it. "
                 "An empty bucket means the test passed completely, not that it was not run."),
        "buckets": [
            {
                "test": _name,
                "node_type": _nt,
                "excluded": len(_rows),
                "population": _pop.get(_name),
                "slots_covered": sum(_r[6] for _r in _rows),
            }
            for _name, (_nt, _rows) in _buckets.items()
        ],
        "excluded_slots": len(_slot_tests),
        "total_slots": sum(len(L.d(_v, otype="word")) for _vns in verse_nodes.values()
                           for _v in _vns),
    }
    (EXCL_DIR / "baseline_exclusions.json").write_text(
        json.dumps(_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf8")

    print(f"wrote {EXCL_DIR.relative_to(REPO_ROOT)}/")
    print(f"  {'bucket':<44} {'type':>11} {'excluded':>9} {'of':>9} {'slots':>9}")
    print("  " + "-" * 86)
    for _name, (_nt, _rows) in _buckets.items():
        print(f"  {_name:<44} {_nt:>11} {len(_rows):>9,} "
              f"{(_pop.get(_name) or 0):>9,} {sum(_r[6] for _r in _rows):>9,}")
    print("  " + "-" * 86)
    print(f"  {'distinct word slots implicated':<44} {'word':>11} "
          f"{len(_slot_tests):>9,} {_manifest['total_slots']:>9,} "
          f"{100.0 * len(_slot_tests) / _manifest['total_slots']:>8.2f}%")
    print()

    # Every bucket must be exactly the shortfall its test reported, which is what keeps this register
    # honest: a predicate that drifts from the one above shows up here as a mismatch rather than as a
    # quietly different file.
    for _name, (_nt, _rows) in _buckets.items():
        if _name in _short:
            check(f"register agrees with {_name!r}", len(_rows), _short[_name],
                  "the register is generated from the same predicate the test counts with, so a "
                  "difference here means the two have drifted apart")


def test_the_exclusion_register_agrees_with_the_tests():
    _mark = len(C.violations)
    run_the_exclusion_register()
    C.assert_own(_mark, "the exclusion register")


# Collects the tests into one table. The population column states what was counted, which differs
# by test: groups for test 1, segments for test 2, verses for tests 3 through 6 and for test 10,
# words for tests 7 to 9 and for test 12, features for test 11, ordered verse pairs for test
# 14 and addresses for test 15. This is the summary to consult after the
# dataset is regenerated, because a change in any row reflects a change in the data or in the
# boundary of what the dataset publishes.
def report_summary():
    print(f"  {'test':<40} {'population':>12} {'pass':>12} {'%':>8}")
    print("  " + "-" * 76)
    for name, (n, ok) in results.items():
        print(f"  {name:<40} {n:>12,} {ok:>12,} {100.0 * ok / n:>8.2f}")


# The gate. Every check added above records its failures rather than raising, so that one run
# produces every figure; this is where the run is allowed to fail.
#
# The six original tests measure a corpus whose figures legitimately vary by manuscript, so they
# assert almost nothing and the table above is their report. The checks collected here are
# different in kind: each one states something that is either true of the published dataset or is
# a defect in it. A failure names the feature, what the dataset carries and what it should carry.
def gate():
    print(f"{len(violations)} failed check(s)\n")
    for _name, _got, _want, _note in violations:
        _g = f"{_got:,}" if isinstance(_got, int) else repr(_got)
        _wa = f"{_want:,}" if isinstance(_want, int) else repr(_want)
        print(f"  FAIL  {_name}\n          carries {_g}, expected {_wa}")
        if _note:
            print(f"          {_note}")

    return 1 if violations else 0
