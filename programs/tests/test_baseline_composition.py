"""Whether each tier of the edition composes the tier above it.

The corpus is a hierarchy, and the claim that makes it an edition rather than a pile of
annotations is that the words spell the word group, the word groups spell the segment,
and the segments spell the line of transcription. These five tests and the offset report
measure exactly that, at each tier in turn. They assert almost nothing, because the
figures legitimately vary by manuscript, so their tables are the report and the
exclusion register names what they do not validate."""

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


# TEST 1. Composition of a word group from its words.
#
# Method: for every word group, concatenate the `voc` feature of the `word` nodes it contains, in
# slot order, and compare the result to the group's own `g_voc` feature under the letters
# comparison.
#
# A word group is treated here by its `id`, not as a single node. Where an editorial boundary cuts
# a word in two, each piece sits in a different segment, so the dataset publishes a second
# `word_group` node for it. Both nodes carry the whole source word as `g_voc`, and each holds only
# its own words. Reading such a group node by node would report it as failing twice for no real
# reason. Reading it by `id`, which is what this test does, states the intended claim: the
# morphological analysis of a word accounts for that word.
#
# What it measures: whether the morphological decomposition accounts for the surface form it was
# derived from. A group whose words spell it exactly is one where every character of the
# manuscript word is claimed by some morpheme.
#
# Words that the source never analysed at all, where `source` is `none` and which number 1,304,
# have no word group to
# spell: the dataset publishes each under a group node whose `id` and `g_voc` are both empty.
# Keying by `id` therefore collected every such word of a verse into ONE bucket whose target was
# the empty string, and that bucket failed once per verse that held any. Those words are excluded
# here, and a bucket the exclusion empties is dropped. It removes 602 phantom buckets carrying
# 599 of the 723 failures this test used to report: `groups` 361,013 -> 360,411, `differ`
# 723 -> 124, `words` 495,216 -> 493,912, and `%` 99.80 -> 99.97. `analysed`, `analysed_spelled`
# and `% of analysed` do not move at all (354,730 / 354,608 / 99.97), because a groupless bucket
# was never in the answerable population, which is why the proportion of analysed words is the
# honest column
# all along, and why the `%` column now agrees with it.
#
# Interpretation: `analysed` restricts the population to the groups whose words all carry
# morphological analysis, the set the decomposition can be evaluated against. The second table
# classifies the failures. `reordered` counts groups where the same letters appear in a different
# order, an alignment fault. `words_shorter` counts groups where the analysis covers only part of
# the surface form, a property of the source material. `dot_vs_mark` counts groups where the two
# strings differ only in whether a Genizah diacritic is written as a full stop or as the combining
# mark U+0740.
@C.once
def run_01_words_compose_the_word_group():
    C.setup()
    globals().update(C.exports())
    test1 = defaultdict(Counter)
    group_failures = []
    for _k, _vns in verse_nodes.items():
        _c = corpus_of_verse[_k]
        # The pieces of one word group, in node order, keyed by the group's own id.
        _by_id = defaultdict(list)
        for _v in _vns:
            for _g in L.d(_v, otype="word_group"):
                _by_id[F.id.v(_g)].append(_g)
        for _gid, _nodes in _by_id.items():
            ws = [w for _g in _nodes for w in L.d(_g, otype="word")
                  if F.source.v(w) != "none"]
            if not ws:
                continue
            built = "".join(F.voc.v(w) or "" for w in ws)
            target = F.g_voc.v(_nodes[0]) or ""
            analysed = {F.source.v(w) for w in ws} == {"word"}
            ok = letters(built) == letters(target)
            _r = test1[_c]
            _r["groups"] += 1
            _r["words"] += len(ws)
            _r["split_groups"] += len(_nodes) > 1
            _r["words_spell_group"] += ok
            _r["differ"] += not ok
            _r["analysed"] += analysed
            _r["analysed_spelled"] += analysed and ok
            if not ok:
                group_failures.append((_c, _nodes[0], target, built))
                _b, _t = letters(built), letters(target)
                _r["reordered"] += sorted(_b) == sorted(_t)
                _r["words_shorter"] += len(_b) < len(_t)
                _r["words_longer"] += len(_b) > len(_t)
                _r["dot_vs_mark"] += _b.replace("݀", ".") == _t

    table("TEST 1  the words of a word group spell the group", test1,
          ["groups", "split_groups", "words", "words_spell_group", "differ", "analysed",
           "analysed_spelled"],
          pct=[("%", "words_spell_group", "groups"), ("% of analysed", "analysed_spelled", "analysed")])
    print()
    table("TEST 1  the composition of the failures", test1,
          ["differ", "reordered", "words_shorter", "words_longer", "dot_vs_mark"])
    results["1 words compose the word group"] = (sum(test1[c]["groups"] for c in CORPORA),
                                                 sum(test1[c]["words_spell_group"] for c in CORPORA))

    # Displays four of the word groups that test 1 reports as failing, followed by one of them
    # rendered node by node by `plain`. The printed line gives the published surface form, the form the
    # words spell, and the analysis of each word, so the disagreement can be inspected directly. The
    # second table of test 1 already summarises the failures as a population.
    for _c, _g, _target, _built in group_failures[:4]:
        print(f"{_c:<16} word group {_g}: published {_target!r}, its words spell {_built!r}")
        print(f"{'':<16}   words: "
              + str([(F.voc.v(w), F.lex.v(w), F.sp.v(w), F.source.v(w)) for w in L.d(_g, otype='word')]))

    _c, _g, _target, _built = next((f for f in group_failures if f[0] == "neofiti_full"),
                                   group_failures[0])
    print(f"\n{_c}: word group {_g}")
    plain(_g, withNodes=True)


def test_01_words_compose_the_word_group():
    _mark = len(C.violations)
    run_01_words_compose_the_word_group()
    C.assert_own(_mark, "01_words_compose_the_word_group")


# TEST 2. Composition of a segment from the words it contains.
#
# Method: for every `segment` node, concatenate the `voc` feature of the `word` nodes it contains
# and compare the result to the segment's own `segment` feature under the letters comparison.
#
# The word tier is the correct level to measure at here. `g_voc` records the whole source word, so
# a word cut by an editorial boundary contributes only its own characters to each side, and a
# segment holding half a word would be compared against the whole word and fail by construction.
# The word tier carries exactly the characters of the segment it sits in. `whole_groups` keeps the
# group-level comparison for reference, and it fails wherever a word straddles two editorial
# states.
#
# `all_readings` uses every word in the segment. `base_reading` uses only the words of groups
# whose `reading` is 0, the underlying reading the first scribe wrote. A segment holding no
# variant satisfies both identically.
#
# What it measures: whether the word tier accounts for the editorial segment that contains it.
# Each word is attributed to the segment its own span falls in, and a word whose span crosses a
# segment boundary is split so that each piece belongs to its own segment.
@C.once
def run_02_words_compose_the_segment():
    C.setup()
    globals().update(C.exports())
    test2 = defaultdict(Counter)
    for _k, _vns in verse_nodes.items():
        _c = corpus_of_verse[_k]
        for _v in _vns:
            for _s in L.d(_v, otype="segment"):
                gs = L.d(_s, otype="word_group")
                ws = L.d(_s, otype="word")
                target = letters(F.segment.v(_s))
                every = letters("".join(F.voc.v(w) or "" for w in ws))
                base = letters("".join(F.voc.v(w) or "" for g in gs if F.reading.v(g) == 0
                                       for w in L.d(g, otype="word")))
                whole = letters("".join(F.g_voc.v(g) or "" for g in gs))
                _r = test2[_c]
                _r["segments"] += 1
                _r["with_words"] += bool(ws)
                _r["no_letters"] += not target
                _r["has_variants"] += any(F.reading.v(g) != 0 for g in gs)
                _r["filler_only"] += bool(ws) and all(F.source.v(w) == "segment" for w in ws)
                _r["all_readings"] += every == target
                _r["base_reading"] += base == target
                _r["either"] += (every == target or base == target)
                _r["whole_groups"] += whole == target

    table("TEST 2  the words of a segment spell the segment", test2,
          ["segments", "with_words", "no_letters", "has_variants", "filler_only",
           "all_readings", "base_reading", "either", "whole_groups"],
          pct=[("% either", "either", "segments"),
               ("% whole groups", "whole_groups", "segments")])
    results["2 words compose the segment"] = (sum(test2[c]["segments"] for c in CORPORA),
                                              sum(test2[c]["either"] for c in CORPORA))


def test_02_words_compose_the_segment():
    _mark = len(C.violations)
    run_02_words_compose_the_segment()
    C.assert_own(_mark, "02_words_compose_the_segment")


# TEST 3. Reconstruction of the verse line from the word group tier.
#
# Method: concatenate the `g_voc` feature of every word group of a verse, in publication order,
# and compare the result to the verse's `line` feature under the letters comparison. Variant
# readings are included, because the published line carries them inline.
#
# Each word group is counted once, by its `id`. A group that an editorial boundary cuts in two
# publishes as two nodes carrying the same `g_voc`, so concatenating over nodes instead of ids
# would double-count that word's surface form and fail the verse for an unrelated reason.
#
# What it measures: whether the surface forms recorded at the word group tier account for the
# verse line the dataset publishes. This is the strongest statement available at that tier, and it
# is independent of the morphological decomposition tested in test 1.
@C.once
def run_03_word_groups_compose_the_verse_line():
    C.setup()
    globals().update(C.exports())
    test3 = defaultdict(Counter)
    for _k, _vns in verse_nodes.items():
        _r = test3[corpus_of_verse[_k]]
        line = max({F.line.v(v) or "" for v in _vns})
        _seen, _built = set(), []
        for _v in _vns:
            for _g in L.d(_v, otype="word_group"):
                _gid = F.id.v(_g)
                if _gid in _seen:
                    continue
                _seen.add(_gid)
                _built.append(F.g_voc.v(_g) or "")
        _r["verses"] += 1
        _r["word_groups"] += len(_seen)
        _r["groups_spell_line"] += letters("".join(_built)) == letters(line)

    table("TEST 3  the word groups of a verse spell the verse line", test3,
          ["verses", "word_groups", "groups_spell_line"],
          pct=[("%", "groups_spell_line", "verses")])
    results["3 word groups compose the verse line"] = (sum(test3[c]["verses"] for c in CORPORA),
                                                       sum(test3[c]["groups_spell_line"] for c in CORPORA))


def test_03_word_groups_compose_the_verse_line():
    _mark = len(C.violations)
    run_03_word_groups_compose_the_verse_line()
    C.assert_own(_mark, "03_word_groups_compose_the_verse_line")


# TEST 4. Reconstruction of the verse line from the segment tier.
#
# Method: concatenate the `segment` feature of every `segment` node of a verse, in publication
# order, and compare the result to the verse's `line` feature under the letters comparison.
# Variant segments are included, because the published line carries the competing readings
# inline. Restricting the concatenation to segments that are not variants would still recover no
# verse that the full concatenation loses. `utf8_spell_line` repeats the comparison in Aramaic
# square script. `repeated` counts the segments a verse publishes more than once under one `id`,
# so the concatenation emits their text twice.
#
# The same loop resolves the segment offsets against the line, which the measurement below reports. The
# line cut at a segment's span is compared to the segment's own string, and the spans of a verse
# are then examined as a partition. They must not overlap, the material between two consecutive
# spans must be whitespace only, and the material before the first span and after the last span
# must also be whitespace. A verse that satisfies all three conditions has segments that tile the
# line. Whether the spans also ascend in publication order is test 6's question, asked of every
# tier at once. The word tier carries its own `start_idx` and `end_idx`, resolved two measurements below.
# A segment's span is the minimum and the maximum of the spans of the words it holds, so the two
# tiers agree by construction, and the word-level statement is the stronger of the two.
#
# What it measures: whether the editorial tier accounts for the verse line the dataset publishes.
# Test 3 asks that question of the word group tier and test 5 asks it of the word tier. The
# segment is the tier between them, and the only one of the three whose strings are runs of the
# line itself, independent of morphology.
#
# Interpretation: the second table restricts the population by the morphological analysis
# underneath. A segment carries morphological analysis when every word it holds has `source`
# `word`. A verse is analysed when every one of its segments does. That is the population the
# decomposition can be evaluated against, and it is reported beside the overall figure and beside
# the rate for the verses that hold an unanalysed segment, so the three can be read separately, as
# tests 1 and 5 do at their own tiers. The third table attributes the failures.
# `text_differs_from_its_span` counts the verses holding a segment whose stored string does not
# match the slice of the line named by its own offsets, the same containment boundary that test 2
# measures from the other side. `spans_still_cover_the_line` counts the failures whose geometry
# still returns the whole line, meaning the loss originates in the segment strings while the spans
# remain correct. The fourth table gives the proportion of the letters of each line that the
# segments emit at all. This proportion is high everywhere, so the shortfall consists of many
# small local losses spread across the text.
@C.once
def run_04_segments_compose_the_verse_line():
    C.setup()
    globals().update(C.exports())
    test4 = defaultdict(Counter)
    segment_failures = []
    for _k, _vns in verse_nodes.items():
        _r = test4[corpus_of_verse[_k]]
        line = max({F.line.v(v) or "" for v in _vns})
        line_utf8 = max({F.line_utf8.v(v) or "" for v in _vns})
        segs = [s for v in _vns for s in L.d(v, otype="segment")]
        target = letters(line)
        built = letters("".join(F.segment.v(s) or "" for s in segs))
        ok = built == target
        analysed, spans = [], set()
        for s in segs:
            ws = L.d(s, otype="word")
            analysed.append(bool(ws) and all(F.source.v(w) == "word" for w in ws))
            a, b = F.start_idx.v(s), F.end_idx.v(s)
            if a is None:
                _r["segment_no_offset"] += 1
                continue
            _r["segment_offset"] += 1
            _r["segment_slice_is_segment"] += line[a - 1:b] == (F.segment.v(s) or "")
            spans.add((a, b))
        every_analysed = bool(analysed) and all(analysed)
        _r["verses"] += 1
        _r["segments"] += len(segs)
        _r["repeated"] += len(segs) - len({F.id.v(s) for s in segs})
        _r["segments_spell_line"] += ok
        _r["utf8_spell_line"] += letters(
            "".join(F.segment_utf8.v(s) or "" for s in segs)) == letters(line_utf8)
        _r["line_letters"] += len(target)
        _r["segment_letters"] += len(built)
        _r["with_morphology"] += sum(analysed)
        _r["without_morphology"] += len(analysed) - sum(analysed)
        _r["analysed_verses"] += every_analysed
        _r["analysed_spell_line"] += every_analysed and ok
        _r["rest_verses"] += not every_analysed
        _r["rest_spell_line"] += (not every_analysed) and ok
        if spans:
            # A verse whose rows are not contiguous under the publication order is emitted as more
            # than one verse node, and a segment spanning the break is emitted once per node. The
            # partition is a statement about distinct spans, so they are collected as a set.
            ordered = sorted(spans)
            disjoint = all(nxt[0] > cur[1] for cur, nxt in zip(ordered, ordered[1:]))
            gaps_ws = all(not line[cur[1]:nxt[0] - 1].strip() for cur, nxt in zip(ordered, ordered[1:]))
            edges_ws = not line[:ordered[0][0] - 1].strip() and not line[ordered[-1][1]:].strip()
            _r["verses_with_spans"] += 1
            _r["spans_disjoint"] += disjoint
            _r["gaps_are_whitespace"] += gaps_ws
            _r["edges_are_whitespace"] += edges_ws
            _r["partitions_the_line"] += disjoint and gaps_ws and edges_ws
        if not ok:
            segment_failures.append((corpus_of_verse[_k], _k, target, built))
            _r["differ"] += 1
            _r["reordered"] += sorted(built) == sorted(target)
            _r["segments_shorter"] += len(built) < len(target)
            _r["segments_longer"] += len(built) > len(target)
            _r["text_differs_from_its_span"] += any(
                F.start_idx.v(s) is not None
                and line[F.start_idx.v(s) - 1:F.end_idx.v(s)] != (F.segment.v(s) or "")
                for s in segs)
            _r["spans_still_cover_the_line"] += letters(
                "".join(line[a - 1:b] for a, b in sorted(spans))) == target
            _r["segment_without_a_span"] += any(F.start_idx.v(s) is None for s in segs)

    table("TEST 4  the segments of a verse spell the verse line", test4,
          ["verses", "segments", "repeated", "segments_spell_line", "utf8_spell_line"],
          pct=[("%", "segments_spell_line", "verses"), ("% utf8", "utf8_spell_line", "verses")])
    print()
    table("TEST 4  by the morphology under the segment", test4,
          ["segments", "with_morphology", "without_morphology", "analysed_verses",
           "analysed_spell_line", "rest_verses", "rest_spell_line"],
          pct=[("% segments analysed", "with_morphology", "segments"),
               ("% of analysed verses", "analysed_spell_line", "analysed_verses"),
               ("% of the rest", "rest_spell_line", "rest_verses")])
    print()
    table("TEST 4  the composition of the failures", test4,
          ["differ", "reordered", "segments_shorter", "segments_longer",
           "text_differs_from_its_span", "spans_still_cover_the_line", "segment_without_a_span"])
    print()
    table("TEST 4  how much of each line the segments emit", test4,
          ["line_letters", "segment_letters"],
          pct=[("% of the letters", "segment_letters", "line_letters")])
    results["4 segments compose the verse line"] = (sum(test4[c]["verses"] for c in CORPORA),
                                                    sum(test4[c]["segments_spell_line"]
                                                        for c in CORPORA))

    # The same segments, now read as geometry through the two tables the offsets support. `% with a
    # span` gives the population that the second percentage is taken over. A segment whose slice
    # returns its own text is one whose characters all belong to words that the segment holds, the
    # same containment property that test 2 measures from the other side. A verse that partitions is
    # one whose segments tile its line with nothing but whitespace between them.
    table("TEST 4  the segment spans, resolved against the line", test4,
          ["segments", "segment_offset", "segment_no_offset", "segment_slice_is_segment"],
          pct=[("% with a span", "segment_offset", "segments"),
               ("% slice is the segment", "segment_slice_is_segment", "segment_offset")])
    print()
    table("TEST 4  the segment spans as a partition of the line", test4,
          ["verses", "verses_with_spans", "spans_disjoint", "gaps_are_whitespace",
           "edges_are_whitespace", "partitions_the_line"],
          pct=[("% partitioning", "partitions_the_line", "verses_with_spans")])


def test_04_segments_compose_the_verse_line():
    _mark = len(C.violations)
    run_04_segments_compose_the_verse_line()
    C.assert_own(_mark, "04_segments_compose_the_verse_line")


# TEST 5. Reconstruction of the verse line from the word (slot) tier.
#
# Method: the slot type is `word`, so the reconstruction uses the text API applied to the verse.
# The format `text-trans-full` is defined as `{voc}{trailer}`, which concatenates each word with
# the material that follows it, and the result is compared to the `line` feature of the verse. The
# comparison is made on the whole string after trimming the trailing space that the final word
# contributes, so it is exact at the level of the character and includes every space.
# `letters_only` repeats the comparison under the letters class, and `utf8_spell_line` repeats the
# exact comparison in Aramaic square script, using `text-orig-full` against `line_utf8`.
#
# What it measures: whether the published slot sequence of a verse matches the published verse
# line. This is the end-to-end statement about the dataset, and the one a reader consuming the
# corpus through T.text experiences directly.
#
# Interpretation: the second table restricts the population to the verses in which every word
# carries morphological analysis, separating the verses the decomposition can be evaluated
# against from the verses where the source material supplies no analysis. The column
# `words_with_morphology` gives the same quantity at the level of the word.
@C.once
def run_05_words_compose_the_verse_line():
    C.setup()
    globals().update(C.exports())
    test5 = defaultdict(Counter)
    line_failures = []
    for _k, _vns in verse_nodes.items():
        _r = test5[corpus_of_verse[_k]]
        line = max({F.line.v(v) or "" for v in _vns})
        line_utf8 = max({F.line_utf8.v(v) or "" for v in _vns})
        ws = [w for v in _vns for w in L.d(v, otype="word")]
        built = "".join((F.voc.v(w) or "") + (F.trailer.v(w) or "") for w in ws)
        built_utf8 = "".join((F.voc_utf8.v(w) or "") + (F.trailer.v(w) or "") for w in ws)
        analysed = all(F.source.v(w) == "word" for w in ws)
        ok = built.strip() == line
        _r["verses"] += 1
        _r["words"] += len(ws)
        _r["words_with_morphology"] += sum(1 for w in ws if F.source.v(w) == "word")
        _r["words_spell_line"] += ok
        _r["letters_only"] += letters(built) == letters(line)
        _r["utf8_spell_line"] += built_utf8.strip() == line_utf8
        _r["every_word_analysed"] += analysed
        _r["analysed_and_spelled"] += analysed and ok
        if not ok:
            line_failures.append((corpus_of_verse[_k], _k, line, built.strip()))

    table("TEST 5  the words of a verse spell the verse line, character for character", test5,
          ["verses", "words_spell_line", "letters_only", "utf8_spell_line"],
          pct=[("% exact", "words_spell_line", "verses"), ("% letters", "letters_only", "verses")])
    print()
    table("TEST 5  restricted to the verses in which every word carries morphology", test5,
          ["verses", "words", "words_with_morphology", "every_word_analysed", "analysed_and_spelled"],
          pct=[("% words", "words_with_morphology", "words"),
               ("% of those verses", "analysed_and_spelled", "every_word_analysed")])
    results["5 words compose the verse line"] = (sum(test5[c]["verses"] for c in CORPORA),
                                                 sum(test5[c]["words_spell_line"] for c in CORPORA))

    # Repeats test 5 through T.text and classifies its failures, then shows the point at which two of
    # them first diverge.
    #
    # The repetition through the text API checks the hand-written concatenation above. It covers the
    # verses that occupy a single verse node, because T.text takes one node at a time.
    #
    # The classification identifies which tier is responsible for each failure. A verse with nothing
    # published to spell it holds only words whose `source` is `none`, so the manuscript records a
    # line that the source material never analysed and never transcribed at the word tier. A verse in
    # which some word carries no morphological analysis is short by that word. A verse in which every
    # word is analysed and the reconstruction still differs represents the residue attributable to the
    # alignment.
    _agree = _differ = 0
    for _k, _vns in verse_nodes.items():
        if len(_vns) == 1:
            if T.text(_vns[0], fmt="text-trans-full").strip() == (F.line.v(_vns[0]) or ""):
                _agree += 1
            else:
                _differ += 1
    print(f"T.text(verse, fmt='text-trans-full') == line:  {_agree:,} agree, {_differ:,} differ\n")

    kinds = Counter()
    residue = []
    for _c, _k, _line, _built in line_failures:
        ws = [w for v in verse_nodes[_k] for w in L.d(v, otype="word")]
        if not _built:
            kinds["nothing published to spell it with"] += 1
        elif any(F.source.v(w) != "word" for w in ws):
            kinds["some word carries no morphology"] += 1
        else:
            kinds["every word analysed, residue of the alignment"] += 1
            residue.append((_c, _k, _line, _built))
    for kind, n in kinds.most_common():
        print(f"  {n:>5,}  {kind}")


    def first_divergence(a, b):
        i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        return i, a[max(0, i - 28):i + 28], b[max(0, i - 28):i + 28]


    print()
    for _c, _k, _line, _built in residue[:2]:
        at, la, lb = first_divergence(_line, _built)
        print(f"{_c} {_k[0]} uid {_k[1]}, first difference at character {at}")
        print(f"  line : ...{la}...")
        print(f"  words: ...{lb}...")


def test_05_words_compose_the_verse_line():
    _mark = len(C.violations)
    run_05_words_compose_the_verse_line()
    C.assert_own(_mark, "05_words_compose_the_verse_line")


# The word tier's offsets, reported here as coverage across all words, alongside the resolution
# rate for the words that carry one.
#
# A word's `start_idx` and `end_idx` are populated only where the line, sliced at those offsets,
# already returns the word's own text. Because of this, "the offsets resolve against the line" is
# true of every word that carries an offset by construction, and quoting that figure on its own
# would be quoting a tautology: 100% of a population defined as the part that passes. The number
# that carries information is how many words carry an offset at all, so both figures are printed
# together here, and the second should always be read alongside the first.
#
# The resolution rate is still worth checking, because the offset passes through several stages
# between where it is first computed and where it appears in this dataset. A fault introduced at
# any of those stages would show up here as a slice that no longer returns its word.
#
# `part` explains why a word may legitimately carry no offset. A word cut by an editorial boundary
# publishes one node per side, each holding only its own characters, so the population being
# measured is made up of word pieces, each smaller than the whole source word.
@C.once
def run_the_word_tier_offsets_resolve():
    C.setup()
    globals().update(C.exports())
    offsets = defaultdict(Counter)
    for _k, _vns in verse_nodes.items():
        _r = offsets[corpus_of_verse[_k]]
        line = max({F.line.v(v) or "" for v in _vns})
        for _w in (w for v in _vns for w in L.d(v, otype="word")):
            voc = (F.voc.v(_w) or "").strip()
            _r["words"] += 1
            _r["with_surface"] += bool(voc)
            _r["split_pieces"] += (F.part.v(_w) or 1) > 1
            a, b = F.start_idx.v(_w), F.end_idx.v(_w)
            if a is None:
                _r["no_offset"] += 1
                continue
            _r["with_offset"] += 1
            _r["slice_is_word"] += line[a - 1:b] == voc

    table("the word tier's offsets, as coverage", offsets,
          ["words", "with_surface", "split_pieces", "with_offset", "no_offset", "slice_is_word"],
          pct=[("% carrying an offset", "with_offset", "words"),
               ("% of those resolving", "slice_is_word", "with_offset")])
    results["word offsets carried by the word tier"] = (
        sum(offsets[c]["words"] for c in CORPORA),
        sum(offsets[c]["with_offset"] for c in CORPORA))
    results["word offsets that resolve, of those carried"] = (
        sum(offsets[c]["with_offset"] for c in CORPORA),
        sum(offsets[c]["slice_is_word"] for c in CORPORA))


def test_the_word_tier_offsets_resolve():
    _mark = len(C.violations)
    run_the_word_tier_offsets_resolve()
    C.assert_own(_mark, "the_word_tier_offsets_resolve")

