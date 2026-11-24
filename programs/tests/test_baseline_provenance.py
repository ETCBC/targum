"""Provenance, staleness and the feature inventory.

Whether the dataset describes the files it was compiled from, and whether what the
metadata promises is what ships. Everything below depends on these holding, so they run
first and a failure here means the later figures describe an outdated build."""

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


# Checks the dataset's provenance against the files it was compiled from. The dataset is stale
# unless both checks below hold.
#
#   1  The xmlVersion metadata against the newest directory under `xml/`. A dataset compiled from
#      an older XML directory than the one currently present is behind by at least that much.
#   2  The feature descriptions against `config/xml.yml`. A mismatch here means the dataset was
#      compiled before the current feature documentation was written.
#
# A failure in either check means the figures below describe an outdated build of the dataset.
@C.once
def run_the_dataset_is_current():
    C.setup()
    globals().update(C.exports())
    import re
    import yaml

    FRESH = True


    def stale(what, got, want):
        nonlocal FRESH
        FRESH = False
        print(f"  STALE  {what}\n           dataset: {got}\n           source:  {want}")


    xml_versions = sorted(p.name for p in (REPO_ROOT / "xml").iterdir() if p.is_dir())
    newest_xml = xml_versions[-1] if xml_versions else None
    print(f"xmlVersion {meta.get('xmlVersion')}  written {meta.get('dateWritten')}")
    print(f"newest xml/ {newest_xml}  (of {len(xml_versions)})")
    if newest_xml and meta.get("xmlVersion") != newest_xml:
        stale("the dataset was compiled from an older XML than xml/ holds",
              meta.get("xmlVersion"), newest_xml)

    def norm(s):
        return re.sub(r"\s+", " ", (s or "")).strip()


    for name, want in C.declared.items():
        if name not in TF_FEATURES:
            continue
        # `tf_meta` reads the header of the feature file directly. The metadata exposed by the
        # library is empty, because it serves from a binary cache that retains values and discards
        # the header block, so this
        # check would have reported all 58 descriptions as stale.
        got = tf_meta(name).get("description")
        if norm(got) != norm(want):
            stale(f"feature {name!r} carries a description config/xml.yml no longer declares",
                  norm(got)[:110], norm(want)[:110])

    counts = {t: n for t, n in ((t, len(list(F.otype.s(t)))) for t in F.otype.all)}
    print("nodes:", ", ".join(f"{t} {counts[t]:,}" for t in F.otype.all))

    print()
    print("dataset is current" if FRESH else "DATASET IS STALE, rebuild before reading on")
    assert FRESH, "stale dataset: see the report above"


def test_the_dataset_is_current():
    _mark = len(C.violations)
    run_the_dataset_is_current()
    C.assert_own(_mark, "the_dataset_is_current")


# Reconciles the feature inventory the metadata PROMISES against the features the dataset
# actually ships, and defines the soft check the new tests below report through.
#
# The staleness check above compares each `config/xml.yml` description against the dataset, but it
# skips a feature the dataset does not have (`if feat is None: continue`), so a description for a
# feature that was never emitted is never checked and never noticed. `g_lex` and `g_lex_utf8` have
# been declared since the file was written and have never been published. This check closes that
# hole from the other side.
#
# `check` is the reporting convention for every test added below. The six original tests read as
# measurements of a corpus whose figures legitimately vary by manuscript, so they assert almost
# nothing. The tests added here state invariants instead, and an invariant that fails should not
# stop the run: the whole point of running it is to get every figure in one pass. So a
# failed check is recorded and printed, the run continues, and the last stage is the gate.

# `TF.features` also holds the nine `__`-prefixed stores Text-Fabric computes for itself, and
# `otype`/`oslots` are the dataset's skeleton rather than annotations, so the shipped inventory is
# the node features plus the edge features, less those two.
@C.once
def run_the_feature_inventory_is_complete():
    C.setup()
    globals().update(C.exports())
    emitted = (set(api.Fall()) | set(api.Eall())) - {"otype", "oslots"}

    # `featureDescriptions` also documents the NODE TYPES, and a node type has no `.tf` file of
    # its own, so it is not an undelivered feature. The set of node types is derived rather than
    # listed. An earlier version held a literal pair of names, so the lexeme node type, correctly
    # described in the metadata file and the one node type this version adds, read as a description
    # that no
    # feature answers. A node type that is ALSO a feature (`text`, `book`, `chapter`, `verse`,
    # `segment`) stays in `promised`, because it does ship a file and the description is that
    # feature's. Deriving it means the next node type does not need anyone to think of it.
    NODE_TYPE_LABELS = set(F.otype.all) - emitted
    promised = set(C.declared) - NODE_TYPE_LABELS
    undelivered = sorted(promised - emitted)
    undescribed = sorted(emitted - set(C.declared))

    print(f"config/xml.yml describes {len(C.declared)} names; the dataset ships {len(emitted)} features")
    print()
    print(f"described but never emitted ({len(undelivered)}): {', '.join(undelivered) or 'none'}")
    print(f"emitted but never described ({len(undescribed)}): {', '.join(undescribed) or 'none'}")
    print()
    check("features described but not emitted", len(undelivered), 0,
          "a description in config/xml.yml that no .tf file answers; the staleness check "
          "cannot see these because it skips a feature the dataset lacks")
    check("features emitted but not described", len(undescribed), 0,
          "a published feature carrying no documented meaning")


def test_the_feature_inventory_is_complete():
    _mark = len(C.violations)
    run_the_feature_inventory_is_complete()
    C.assert_own(_mark, "the_feature_inventory_is_complete")


# Reports the feature inventory and the distribution of the three features that the tests below
# depend on. `source` determines which words carry a morphological analysis, `reading` identifies
# the readings that compete for one position, and the segment `type` feature records the editorial
# state of a run of the line.
@C.once
def run_the_feature_distribution_is_reported():
    C.setup()
    globals().update(C.exports())
    FEATURES = sorted(f for f in TF_FEATURES if not f.startswith("o") and f != "otext")
    for otype in F.otype.all:
        sample = F.otype.s(otype)[:400]
        present = sorted(f for f in FEATURES
                         if hasattr(F, f) and any(Fs(f).v(n) is not None for n in sample))
        print(f"{otype:<11} {', '.join(present)}")
    print()
    print("source     ", dict(F.source.freqList()))
    print("reading    ", dict(F.reading.freqList()))
    print("segment    ", dict(F.type.freqList()))
    print()
    for fmt in sorted(T.formats):
        print(f"  {fmt:<16} {T.text(range(1, 9), fmt=fmt)}")


def test_the_feature_distribution_is_reported():
    _mark = len(C.violations)
    run_the_feature_distribution_is_reported()
    C.assert_own(_mark, "the_feature_distribution_is_reported")

