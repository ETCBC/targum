"""The section tier, the parallel-witness edge, and the key the whole edition is addressed
by.

Where each verse sits, how a verse reaches the other witnesses to the same address, and
whether the address itself is sound. The last of the three is the gate that the earlier
versions of this suite lacked: a line record keyed on less than the full address
collides silently, and one mis-keyed component publishes a transcription at an address
it does not belong to, duplicates the enclosing chapter, and drops references entirely."""

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


# TEST 10. The section census, and the two places the corpus admits it does not know where it is.
#
# The method is to walk the section tiers, which are `book`, `chapter` and `verse`,
# and count the chapter nodes whose `chapter` is the string "0", the verse nodes carrying no
# `verse`, and the material each of those holds.
#
# Chapter 0 means "no chapter could be derived". `src/main/domain/subtext.py:40-67` initialises
# `chapter` to 0 and returns it when the scraped subtext name matches none of its three regexes;
# the view layer then keeps the 0 on purpose, because Text-Fabric requires a value and not a null
# on a section feature, and a verse whose section is absent cannot be addressed at all. Both
# cases are unlocalised fragments, namely a leaf of `fragment_targum_p` and one of
# `fragment_targum_v`
# whose heading names the book but no chapter.
#
# This has been restated. The verses with no verse number were the same problem one tier down,
# and this
# measurement pinned them at nine, "confined to the same two manuscripts". Both halves of that have
# changed, and in opposite directions:
#
#   The count of verse nodes carrying no verse number is now zero, and that follows from the
#   section model rather than from a repair. Making the verse a section level is what allows a
#   section address to resolve, and a section address may not be null, so the null became a
#   SENTINEL: 0, or 0 and -2 where one chapter holds two of them, since two verses may not
#   share one address. Nothing was localised; the unknown is now written down instead of
#   left absent, which is why the check below is an invariant and the sentinel count beside
#   it is the documented ceiling that replaces the old 9.
#
#   The sentinel steps by TWO, and that is the one thing here that is not about this corpus.
#   context-fabric compiles an int feature into an array whose own missing-value sentinel IS
#   -1 (`cfabric.io.compiler._check_sentinel_collision` says so and warns), so a published -1
#   loads back as None. Measured on the build before this one: node 566613,
#   `fragment_targum_v` at Deuteronomy 28, carried `verse` -1, `text-fabric` read it -1 and
#   the reading client returned a null, and it was the only such value in any integer feature.
#   `-1` is therefore reserved, the sentinel descends 0, -2, -4, and the last check in this
#   measurement is the guard. That check reads the shipped `.tf` files and not the loaded API,
#   because under cfabric a published -1 arrives as None and asking the API whether anything
#   carries -1 would answer no on exactly the fault it exists to catch.
#
#   The population is 11, not 9, and it spans THREE manuscripts rather than two. Nine are in
#   `fragment_targum_p` and `fragment_targum_v` as the old note said; the other two are
#   Cairo Genizah fragments, `_g` at Exodus 15 and `_t` at Deuteronomy 34, and they are the
#   two largest of the eleven at 42 and 148 words. `config/xml.yml` still described this
#   population as "nine `frag_targ` verses" and is corrected with this measurement.
#
# What it measures: the size of the undetermined population, asserted as a documented CEILING.
# This test PASSES today. It is here as the regression guard: an unlocalised fragment is a
# property of the source, so the figure may legitimately be explained, but it must never grow
# silently, and zero is not the target, because a chapter 0 that became chapter 1 would be a
# fabrication.
#
# `chapter` and `verse` are published with `valueType=str` and are absent from `config/xml.yml`'s
# `intFeatures`, so a consumer sorting the 51 distinct chapter values lexically puts "10" before
# "2". The last two checks are that contract, and they fail until those two names are added.
@C.once
def run_10_sections_are_determined():
    C.setup()
    globals().update(C.exports())
    test10 = defaultdict(Counter)
    for _t in F.otype.s("text"):
        _r = test10[corpus_of(_t)]
        _r["texts"] += 1
        for _b in L.d(_t, otype="book"):
            _r["books"] += 1
        for _c in L.d(_t, otype="chapter"):
            _r["chapters"] += 1
            if F.chapter.v(_c) in ("0", 0):
                _r["chapter_0"] += 1
                _r["verses_in_chapter_0"] += len(L.d(_c, otype="verse"))
                _r["words_in_chapter_0"] += len(L.d(_c, otype="word"))
        for _v in L.d(_t, otype="verse"):
            _r["verses"] += 1
            _ch = L.u(_v, otype="chapter")
            _located = F.verse.v(_v) is not None and not (
                _ch and F.chapter.v(_ch[0]) in ("0", 0))
            _r["located"] += _located
            if F.verse.v(_v) is None:
                _r["no_verse"] += 1
                _r["words_in_no_verse"] += len(L.d(_v, otype="word"))

    table("TEST 10  the section census", test10,
          ["texts", "books", "chapters", "verses", "chapter_0", "verses_in_chapter_0",
           "words_in_chapter_0", "no_verse", "words_in_no_verse", "located"],
          pct=[("% located", "located", "verses")])
    print()
    for _t in F.otype.s("chapter"):
        if F.chapter.v(_t) in ("0", 0):
            _b, _x = L.u(_t, otype="book"), L.u(_t, otype="text")
            print(f"  chapter 0: {F.text.v(_x[0])} {F.book.v(_b[0])}, "
                  f"{len(L.d(_t, otype='verse'))} verse, {len(L.d(_t, otype='word'))} words")
    print()

    _t10 = Counter()
    for _c in CORPORA:
        _t10.update(test10[_c])
    check("chapter nodes at chapter 0", _t10["chapter_0"], 2,
          "an unlocalised fragment whose heading names the book but no chapter; TF needs a "
          "value and not a null on a section feature, so the 0 is kept deliberately")
    check("words under chapter 0", _t10["words_in_chapter_0"], 13)
    check("verse nodes carrying no `verse`", _t10["no_verse"], 0,
          "the verse is a section level and a section address cannot be null, so the nine "
          "nulls became sentinels. An invariant since: a verse node with no `verse` is one that "
          "cannot be addressed at all")
    # The sentinel population replaces the old count of 9 as the documented ceiling. Asserted
    # here rather than merely reported, because it is the figure that must never grow silently. A
    # verse to which the source gives no number is a property of that source, and inventing one would
    # be a
    # fabrication exactly as a chapter 0 becoming chapter 1 would be.
    def _verse_number(v):
        """`verse` as an int, with a missing value folded in as a sentinel rather than raised on.

        The check above asserts that no verse node is missing `verse`, so this cannot mask a null in
        the data. It exists because cfabric returns None for a published -1, and a bare
        converting the value then raises in the middle of a census, which is how the
        collision documented above was found.
        """
        n = F.verse.v(v)
        return 0 if n is None else int(n)


    C.SHARED["verse_number"] = _verse_number
    _sentinel = [_v for _v in F.otype.s("verse") if _verse_number(_v) <= 0]
    check("verse nodes publishing a sentinel verse number", len(_sentinel), 11,
          "0, or 0 and -2 where one chapter holds two: nine in the two fragment_targum manuscripts "
          "and two in the Cairo Genizah fragments `_g` (Exodus 15) and `_t` (Deuteronomy 34)")
    print(f"  sentinel verse numbers published: "
          f"{dict(Counter(sorted(_verse_number(_v) for _v in _sentinel)))}")


    def tf_value_occurrences(feature, wanted):
        """Count occurrences of one literal value in a shipped `.tf` node feature file.

        Read from the file, not through the API. A `.tf` node feature line is `<spec>\t<value>` or a
        bare `<value>` continuing the previous spec, after an `@`-header terminated by the first line
        that does not start with `@`.
        """
        path = TF_DIR / f"{feature}.tf"
        if not path.exists():
            return None
        n, in_header = 0, True
        with path.open(encoding="utf8") as fh:
            for line in fh:
                if in_header:
                    if line.startswith("@"):
                        continue
                    in_header = False
                    continue                      # the blank line that closes the header
                if line.rstrip("\n").rsplit("\t", 1)[-1] == wanted:
                    n += 1
        return n


    INT_FEATURES = yaml.safe_load((REPO_ROOT / "config/xml.yml").read_text())["intFeatures"]
    _reserved = {_f: tf_value_occurrences(_f, "-1") for _f in INT_FEATURES}
    _reserved = {_f: _n for _f, _n in _reserved.items() if _n}
    check("int-feature occurrences carrying the reserved -1", sum(_reserved.values()), 0,
          "-1 is context-fabric's missing-value sentinel for an int feature, so a published -1 "
          "loads back as None and `F.<f>.v(n) <= 0` raises instead of answering: "
          + (", ".join(f"{_f}={_n}" for _f, _n in _reserved.items()) or "none"))
    print(f"  int features scanned for the reserved -1: {len(INT_FEATURES)}")
    check("chapter nodes in total", _t10["chapters"], 1210,
          "the section tier itself; a change here is a change in what the corpus publishes. Every "
          "chapter path now carries exactly one node, so this is also a count of chapters")

    # The manuscript tier, and the two numbers that must not be confused with each other.
    #
    # `text` names the manuscript everywhere EXCEPT Neofiti, where `neofiti_base` and `neofiti_full`
    # are two views of one codex, so the corpus has 46 `text` values over 45 manuscripts, and
    # `manuscript` is the feature that states it. It is the one fact in the parallel witness relation
    # that nothing else published can supply: two verses are parallel iff they share
    # `(book, chapter, verse)`, which IS derivable, but telling a parallel (two manuscripts translate
    # this verse) from a view (one manuscript under two editorial filters) is not. Derived without it
    # the relation splits 49,384 witness / 20 view against the true 37,658 / 11,654.
    #
    # `text` node count is 46 rather than 68 because the tier is resumed. The serialiser writes one
    # XML
    # folder per verse-id RANGE, and six manuscripts span several, so the walk used to open a node per
    # folder. Both numbers are asserted, because the failure mode they guard against is each other.
    _texts = list(F.otype.s("text"))
    _manuscripts = {F.manuscript.v(_t) for _t in _texts}
    _names = {F.text.v(_t) for _t in _texts}
    check("`text` nodes", len(_texts), 47,
          "one per manuscript name rather than one per directory, which was 68 before the tier "
          "was resumed")
    check("distinct `text` names", len(_names), 47,
          "one node each, so iterating `F.otype.s('text')` no longer over-counts a manuscript")
    check("distinct manuscripts", len(_manuscripts), 46,
          "47 names, 46 manuscripts; the single collapse is Neofiti 1, whose two corpora are two "
          "view types of one codex")
    check("text nodes with no `manuscript`", sum(1 for _t in _texts if F.manuscript.v(_t) is None), 0)
    _neofiti = {F.manuscript.v(_t) for _t in _texts if F.text.v(_t).startswith("neofiti")}
    check("the Neofiti views that resolve to one codex", len(_neofiti), 1,
          "`neofiti_base` and `neofiti_full` must share one `manuscript` value, which is what makes "
          "a witness count right")
    for _f in ("chapter", "verse"):
        _vt = tf_meta(_f).get("valueType")
        _n = len({Fs(_f).v(_n) for _n in F.otype.s(_f)} - {None})
        print(f"  {'ok  ' if _vt == 'int' else 'FAIL'}  {('`' + _f + '` valueType'):<46} "
              f"{_vt:>9}" + ("" if _vt == "int" else "  expected int"))
        if _vt != "int":
            violations.append((f"`{_f}` valueType", _vt, "int",
                               f"absent from config/xml.yml intFeatures, so a consumer sorting "
                               f"the {_n} distinct `{_f}` values gets them lexically, "
                               '"10" before "2"'))

    results["10 sections are determined"] = (
        sum(test10[c]["verses"] for c in CORPORA), sum(test10[c]["located"] for c in CORPORA))


def test_10_sections_are_determined():
    _mark = len(C.violations)
    run_10_sections_are_determined()
    C.assert_own(_mark, "10_sections_are_determined")


# TEST 14. The parallel witness edge, and the five properties that make it a relation rather
# than a list of pairs.
#
# The relation was first published as a set of database views and a keyed table, and an edge
# feature had to wait for a rebuild, because an edge keys on node numbers and node numbers do not
# exist until the corpus has been compiled. That rebuild has happened, so the relation is now a
# feature of the core data:
#
#     E.crossref.f(verse)  ->  ((other_verse, 'witness' | 'view' | 'same_witness'), ...)
#
# The application configuration registers no additional modules as a consequence. An earlier plan
# would have shipped this as a separate module with its own directory and identifier, and
# registering one now would direct a consumer to a second artefact for a feature they already
# hold.
#
# The method is to walk every verse node, read its edges, and assert five properties. The keyed
# table remains the citable statement of the relation, because it is keyed on the address and
# therefore survives a recompile, and a verification mode compares the two. This measurement asserts the
# edge against the corpus it ships in, which is the question a consumer of the edge actually has.
#
#   1  Symmetry. The edge is emitted in both directions, so every edge has its reverse carrying
#      the same label. Without that property the edge answers from one side only and a consumer
#      has to know which side they are on.
#
#   2  The address, in both directions. Two verses are parallel when they carry the same book,
#      chapter and verse, so no edge may join two addresses and no two nodes at one address may
#      be left unjoined. The second half is what makes the edge the address relation itself
#      rather than a subset of it.
#
#   3  The label, which has three values rather than two.
#        `witness`       the manuscripts differ, and this is the parallel.
#        `view`          one manuscript under two views, which is Neofiti 1 and nothing else.
#        `same_witness`  one manuscript under one view, twice at one address.
#      This is what the manuscript feature is published for. Collapsing `witness` and `view`
#      makes the number of witnesses attesting a verse wrong by one on all 5,827 Neofiti
#      addresses. The third label is the price of the second property being total. It counted 20
#      ordered pairs while three Genizah addresses held more than one verse record of one
#      fragment, and it counts none now that the line coordinate carries its chapter. Naming
#      that case was preferred to labelling it `view`, which would be false, and to omitting it,
#      which would make the edge under-report a consumer's own witness with nothing to say so. The
#      keyed table does not face the question, because it is keyed on the manuscript and view and
#      so excludes the pair rather than naming it.
#
#   4  NO SELF-EDGE, and both endpoints on the `verse` tier.
#
#   5  NO OTHER LABEL. Those three exhaust the relation; a fourth value would be a fourth kind
#      of thing that nothing documents.
#
# What it measures: whether a consumer can trust the edge INSTEAD of re-deriving the relation
# from the address. If any check here fails they cannot, and the CSV is the fallback.
@C.once
def run_14_the_crossref_edge_is_the_address_relation():
    C.setup()
    globals().update(C.exports())
    _addr, _ms = {}, {}
    for _v in F.otype.s("verse"):
        _t = L.u(_v, otype="text")[0]
        _addr[_v] = (F.book.v(L.u(_v, otype="book")[0]),
                     F.chapter.v(L.u(_v, otype="chapter")[0]),
                     C.SHARED["verse_number"](_v))
        _ms[_v] = (F.manuscript.v(_t), F.view.v(_t))

    _at = defaultdict(list)
    for _v, _a in _addr.items():
        _at[_a].append(_v)

    RELATIONS = ("witness", "view", "same_witness")
    _edges, _rel = {}, Counter()
    for _v in F.otype.s("verse"):
        for _o, _r in E.crossref.f(_v) or ():
            _edges[(_v, _o)] = _r
            _rel[_r] += 1


    def _faults(a, b, r):
        """Which of the five properties this one ordered edge breaks."""
        out = []
        if _edges.get((b, a)) != r:
            out.append("asymmetric")
        if _addr.get(b) != _addr[a]:
            out.append("off-address")
        if r != ("witness" if _ms[b][0] != _ms[a][0]
                 else "view" if _ms[b][1] != _ms[a][1] else "same_witness"):
            out.append("mislabelled")
        if a == b:
            out.append("self")
        if F.otype.v(b) != "verse":
            out.append("off-tier")
        if r not in RELATIONS:
            out.append("unknown-relation")
        return out


    _broken = Counter()
    _good = 0
    for (_a, _b), _r in _edges.items():
        _f = _faults(_a, _b, _r)
        if _f:
            _broken.update(_f)
        else:
            _good += 1

    # The other direction of property 2: what the address relation REQUIRES.
    _required = sum(len(_n) * (len(_n) - 1) for _n in _at.values())
    _isolated = [_a for _a, _n in _at.items() if len(_n) == 1]
    _shared = len(_at) - len(_isolated)
    _by_witness = Counter(len({_ms[_v][0] for _v in _n}) for _n in _at.values())

    print("TEST 14  the parallel-witness edge")
    print(f"  {'ordered pairs in the edge':<48} {len(_edges):>9,}")
    print(f"  {'  witness (two manuscripts, the parallel)':<48} {_rel['witness']:>9,}")
    print(f"  {'  view (one manuscript, two view types)':<48} {_rel['view']:>9,}")
    print(f"  {'  same_witness (one manuscript, one view)':<48} {_rel['same_witness']:>9,}")
    print(f"  {'ordered pairs the address relation requires':<48} {_required:>9,}")
    print(f"  {'canonical addresses':<48} {len(_at):>9,}")
    print(f"  {'  with more than one verse node':<48} {_shared:>9,}")
    print(f"  {'  attested once, so carrying no edge':<48} {len(_isolated):>9,}")
    print(f"  {'verse nodes':<48} {len(_addr):>9,}")
    print()
    print("  addresses by the number of MANUSCRIPTS that attest them")
    for _n in sorted(_by_witness, reverse=True):
        print(f"    {_n:>2} manuscript(s)  {_by_witness[_n]:>6,}")
    print()

    check("crossref edges breaking any of the five properties", sum(_broken.values()), 0,
          "by fault: " + (", ".join(f"{_k}={_v:,}" for _k, _v in sorted(_broken.items()))
                          or "none"))
    check("ordered pairs the address relation requires but the edge omits",
          _required - len(_edges), 0,
          "the edge must BE the address relation, not a subset of it: every pair of verse nodes "
          "sharing `(book, chapter, verse)` is joined, in both directions")
    check("crossref relation values outside the documented three",
          len(set(_rel) - set(RELATIONS)), 0,
          "found: " + (", ".join(sorted(set(_rel) - set(RELATIONS))) or "none"))
    check("`same_witness` ordered pairs", _rel["same_witness"], 0,
          "no address holds more than one verse record of one manuscript under one view. Three "
          "Genizah addresses did so while the line coordinate carried no chapter. The label is kept "
          "in the documented set because the builder can still emit it, so a non-zero value here "
          "means a manuscript has regained a second record at one address")
    check("addresses attested by exactly one verse node", len(_isolated), 13,
          "a verse no other manuscript transmits and Neofiti does not hold twice, so it has no "
          "parallel to point at. Eleven of the thirteen carry the degenerate verse sentinel, which "
          "has no verse number to match on and so cannot have a parallel by construction. Reported "
          "as a ceiling: it fell from 22 as further line references were published")

    # Four ways to use the edge, each answering a question the corpus could not answer before it.
    print("  worked examples")
    _ex = T.nodeFromSection(("Genesis", 44, 18))
    if _ex is not None:
        _them = E.crossref.f(_ex) or ()
        print(f"    1  witnesses to Genesis 44:18 from {_ms[_ex][0]}: "
              f"{len({_ms[_o][0] for _o, _r in _them if _r == 'witness'})} other manuscript(s)")
        for _o, _r in sorted(_them, key=lambda p: _ms[p[0]]):
            print(f"         {_r:<8} {_ms[_o][0]:<22} {len(L.d(_o, otype='word')):>4} words")

    # 2. The most widely attested addresses, where a critical apparatus has the most to compare.
    _deep = sorted(_at.items(), key=lambda kv: -len({_ms[_v][0] for _v in kv[1]}))[:3]
    print(f"    2  the three most widely attested addresses")
    for _a, _n in _deep:
        print(f"         {_a[0]} {_a[1]}:{_a[2]:<4} "
              f"{len({_ms[_v][0] for _v in _n})} manuscripts, {len(_n)} verse nodes")

    # 3. The `view` edges on their own: one codex read two ways, which is a different question.
    _views = {_a for (_a, _b), _r in _edges.items() if _r == "view"}
    print(f"    3  verse nodes with a `view` edge (Neofiti base vs full): {len(_views):,}")

    # 4. Length disagreement between witnesses, the cheapest signal that a reading diverges.
    _spread = []
    for _a, _n in _at.items():
        if len({_ms[_v][0] for _v in _n}) < 3:
            continue
        _w = [len(L.d(_v, otype="word")) for _v in _n]
        _spread.append((max(_w) - min(_w), _a, min(_w), max(_w), len(_n)))
    _spread.sort(reverse=True)
    print(f"    4  widest word-count spread among 3+ manuscript addresses")
    for _d, _a, _lo, _hi, _k in _spread[:3]:
        print(f"         {_a[0]} {_a[1]}:{_a[2]:<4} {_lo:>4} to {_hi:<4} words "
              f"across {_k} verse nodes (spread {_d})")

    results["14 the crossref edge is the address relation"] = (_required, _good)


def test_14_the_crossref_edge_is_the_address_relation():
    _mark = len(C.violations)
    run_14_the_crossref_edge_is_the_address_relation()
    C.assert_own(_mark, "14_the_crossref_edge_is_the_address_relation")


# TEST 15. The publication key, and the two defects a shorter key was able to hide.
#
# A verse is addressed by book, chapter and verse, and the identity of a line record has to be
# keyed on all three. A key built on the verse number alone cannot distinguish two references in
# one manuscript that share it, and the collision is silent rather than noisy: the reference the
# source prints first keeps the record, the second loses its transcription, and the morphology
# fetched for the second is attached to the first. One mis-keyed component therefore produces
# three distinct faults at once, a line published at an address it does not transcribe, a chapter
# that opens and closes repeatedly because the chapter of a word no longer follows from the
# chapter of its line, and a body of references absent from the dataset with nothing recording
# that they are missing.
#
# This test is the gate that the earlier versions of this suite lacked. None of the six
# original tests could see any of the three faults, because each of them measures a corpus
# against itself and a collision is consistent with itself by construction.
#
# Two invariants, and they are independent.
#
#   1  NO TRANSCRIPTION AT TWO ADDRESSES. Where one manuscript holds two addresses whose verse
#      nodes INTERLEAVE in publication order and whose `line` values are identical, the later
#      address is carrying the earlier one's transcription. Interleaving is the discriminating
#      part. Two shortcuts look simpler and neither works. The first is `uid`, which would answer
#      the question directly by naming the line record, but it is a word-level feature, so it is
#      None on every verse node and a test grouping verses by it collapses each manuscript into
#      one group. The second is the `line` string on its own, which cannot separate a copied line
#      from a repeated one: formulaic repetition is pervasive, and the line meaning "and the Lord
#      spoke to Moses saying" recurs verbatim at 70 addresses in Pseudo-Jonathan alone.
#
#   2  COVERAGE, STATED AS WHAT THE KEY RESCUES. The dataset cannot be compared against the
#      source's own list of references without the source, which this suite deliberately does
#      not reach. The equivalent statement it can make on its own is how many addresses a shorter
#      key could not have published. Counting within each manuscript, the Genizah material holds
#      1,215 addresses over 560 distinct verse numbers, so 655 of them exist only because the key
#      carries the chapter. If the chapter were ever dropped from the key again, those 655 would
#      collapse into the 560 and this figure would fall to zero, which is what makes it a gate
#      rather than a description. A further 8 need the book as well, because a manuscript can hold
#      the same chapter and verse of two different books.
#
# The table reads the same way for every corpus, and the figures outside the Genizah material are
# large and uninteresting: a manuscript spanning five books repeats most verse numbers many times
# over, so almost every address there needs more than the verse number. The column is diagnostic
# only where a key was once built from the verse alone.
@C.once
def run_15_the_publication_key():
    C.setup()
    globals().update(C.exports())
    test15 = defaultdict(Counter)
    _interleaved = []

    for _name in sorted({F.text.v(_t) for _t in F.otype.s("text")}):
        _tn = next(_t for _t in F.otype.s("text") if F.text.v(_t) == _name)
        _addrs = defaultdict(list)
        for _v in L.d(_tn, otype="verse"):
            _addrs[(F.book.v(L.u(_v, otype="book")[0]),
                    F.chapter.v(L.u(_v, otype="chapter")[0]), F.verse.v(_v))].append(_v)

        # Invariant 1, within this manuscript, in publication order.
        _items = sorted(((_a, min(_ns), max(_ns), _ns) for _a, _ns in _addrs.items()),
                        key=lambda _x: _x[1])
        for _x, _y in zip(_items, _items[1:]):
            if _y[1] < _x[2] and {F.line.v(_n) for _n in _x[3]} == {F.line.v(_n) for _n in _y[3]}:
                _interleaved.append((_name, _y[0]))

        _r = test15[corpus_of(_tn)]
        _r["manuscripts"] += 1
        _r["addresses"] += len(_addrs)
        _r["verse_nodes"] += sum(len(_ns) for _ns in _addrs.values())
        _r["distinct verse"] += len({_a[2] for _a in _addrs})
        _r["needs the chapter"] += len(_addrs) - len({_a[2] for _a in _addrs})
        _r["needs the book"] += len(_addrs) - len({(_a[1], _a[2]) for _a in _addrs})

    table("TEST 15  what each component of the address rescues", test15,
          ["manuscripts", "addresses", "verse_nodes", "distinct verse",
           "needs the chapter", "needs the book"],
          pct=[("% needing the chapter", "needs the chapter", "addresses")])
    print()
    if _interleaved:
        for _name, _a in _interleaved[:10]:
            print(f"    interleaved  {_name}  {_a[0]} {_a[1]}:{_a[2]}")
        print()

    _t15 = Counter()
    for _c in CORPORA:
        _t15.update(test15[_c])

    check("addresses whose nodes interleave and share a `line`", len(_interleaved), 0,
          "one manuscript publishing one transcription at two addresses. The later address is the "
          "spurious one, and its words are a fragment of the analysis of a verse it does not hold")
    check("verse nodes beyond one per address", _t15["verse_nodes"] - _t15["addresses"], 0,
          "an address is published as a single node, so a section walk cannot miss part of a verse "
          "and a count of verse nodes is a count of verses")
    check("Genizah addresses a verse-only key could not publish",
          test15["cairo_genizah"]["needs the chapter"], 655,
          "the coverage gate. These exist only because the line key carries the chapter, so a "
          "regression in the key drives this to 0 rather than raising anything of its own")
    check("Genizah addresses a chapter-and-verse key could not publish",
          test15["cairo_genizah"]["needs the book"], 8,
          "one manuscript holding the same chapter and verse of two different books, so the book "
          "is load-bearing in the key and not merely a label")

    results["15 the publication key"] = (_t15["addresses"], _t15["addresses"] - len(_interleaved))


def test_15_the_publication_key():
    _mark = len(C.violations)
    run_15_the_publication_key()
    C.assert_own(_mark, "15_the_publication_key")

