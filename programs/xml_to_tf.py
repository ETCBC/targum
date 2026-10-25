"""
Compilation of the serialised XML corpus into a Text-Fabric dataset.

The script walks every XML document beneath ``xml/``, issues the node, slot, feature and edge
actions that build the graph, and writes the feature files beneath ``tf/``. It is invoked as a
subprocess by the serialisation pipeline and can also be run directly.

Repository location
-------------------
Text-Fabric derives every path it uses, including the metadata file, the XML and dataset
directories and the application directory, from a helper that reads the working directory and
requires it to sit beneath a conventional backend, organisation and repository path. A
repository checked out at any other depth causes that helper to return nothing and the converter
to abort before doing any work. A symbolic link alone does not resolve this, because the working
directory is reported as a physical path, so ``pin_repo_location`` exposes the repository at a
conformant path and then pins the answer the helper gives. Both bindings of that helper must be
patched, because the converter module imported the name directly.

Resumed node types
------------------
Two node types are created once and then resumed, rather than created afresh at each element
that carries them.

The first is ``lexeme``. The serialiser wraps every run of words sharing a lexeme in a
``lexeme`` element, so the same lexeme appears many thousands of times and in every manuscript.
Creating a node at each occurrence would produce one single-word lexeme node per run, which is
precisely the redundancy the tier exists to remove. The first element carrying a given key
therefore creates the node and the remainder resume it. Resuming adds a node back to the set of
embedders without creating a second one, so the word slot that follows joins the slot set of the
lexeme it belongs to. The result is 6,363 nodes with discontiguous slot sets, which is the shape
the BHSA gives its own lexeme type, and the reason ``L.u(word, otype='lexeme')`` resolves with no
edge feature of this project's own. Containment is the edge.

The key is ``rank_lex``, the position of the lexeme in the frequency list of the corpus. It is a
total ranking over 1 to 6,363 and therefore a bijection onto the lexeme nodes, it is never null
where a lexeme is present, and it is never zero. 13,568 words carry no lexeme at all, because
the structural layer holds words the source never analysed. The serialiser still emits an element
for those, carrying no attributes, and returning no node keeps them out of the graph rather than
minting a lexeme with no identity.

The second is ``text``, the manuscript. The serialiser writes one XML directory per range of
verse identifiers rather than one per manuscript, so a manuscript spanning several ranges would
otherwise open one node per directory. The identity of a manuscript is its name and not the file
it happened to be serialised into. Features are applied at creation only, which is sound because
they are constant within a manuscript, and re-applying them on resume would be an operation that
quietly concealed a divergence. Unlike the lexeme tier this node remains contiguous, which is the
purpose of the numeric directory sort in the director. ``text`` is a structure type, so a
manuscript whose slots arrived in scattered runs would be a structure node interleaved with its
siblings. The helper ``getXML`` sorts directory names as strings, which interleaves the
manuscripts, and it is library code in a pinned dependency, so the corrected sort belongs here.

Section and structure levels
----------------------------
Text-Fabric permits exactly three section levels, and this corpus has four tiers above the
segment. The three levels are ``book``, ``chapter`` and ``verse``, so that a verse can be
addressed by reference and so that a tool written against any other corpus of the same family,
each of which opens by resolving a book and chapter, resolves here as well. ``structureTypes``
carries the full hierarchy including the witness and is subject to no three-level limit.

The cost of that choice is that a section address is not unique across witnesses. Of the 5,866
distinct addresses in the corpus only 22 resolve to a single verse, and 5,844 are shared, by up
to nine verse nodes, because five witnesses translate the same Pentateuch and ``book`` names the
biblical book rather than the manuscript. Resolving a section therefore answers with one
witness's verse, and the remaining witnesses are reached through the structure or through the
``crossref`` edge. A corpus of parallel witnesses cannot have the manuscript as its first
section level and also be comparable with anything else.

Edges
-----
``parent`` joins a node to the node enclosing it, over the word, word group and segment tiers.
The lexeme tier is deliberately excluded, since it encloses words distributed across the corpus
and is enclosed by nothing, so an edge from a lexeme to whichever word group happened to be open
when it was first created would assert a containment that does not hold.

``sibling`` joins a node to each of its preceding siblings. Its tiers are deliberately narrower,
because the edge count is quadratic in the number of siblings beneath one parent, and a verse
holds 19.8 word groups on average and 347 at the extreme.

``crossref`` is the parallel witness relation. Two verses are parallel when they carry the same
canonical address, so the relation is given by the data rather than inferred, and there is no
similarity threshold and no choice of method to report. It is computed here, during the compile,
rather than supplied alongside the dataset from a stored node map. An edge feature keys on node
numbers, and node numbers do not exist until the corpus has been compiled, so any stored form
would require a further step after every rebuild and would be silently stale the moment anyone
recompiled. Built in the director it cannot be stale, because there is no state to go stale.

The label records which relation holds, and the first distinction is the one a consumer must not
collapse. ``witness`` means two manuscripts translate this verse, which is the parallel.
``view`` means one manuscript under two editorial filters, where the two views of Neofiti are a
single codex, and counting the two labels together makes the number of witnesses attesting a
verse wrong by one on every Neofiti verse. ``same_witness`` means one manuscript under one
filter holding more than one verse record at this address, which is neither.

That third label exists because the relation is total over the address, meaning every pair of
verse nodes sharing an address is joined, and 20 of the resulting ordered pairs join two nodes of
a single witness. Three addresses do this, all of them Genizah fragments. Labelling them ``view``
would be false, because they are one editorial filter. Omitting them would make the edge
under-report a consumer's own witness at those three addresses with nothing to say so, which is
the worse failure for a relation whose purpose is critical comparison. They are therefore emitted
and named, and filtering on the ``witness`` label costs a consumer nothing. Edges are emitted in
both directions, because the underlying action is directed while the relation is symmetric, and
the reported counts are therefore of ordered pairs.

Node closure
------------
``afterChildren`` closes the node that its own element opened, which is why the node is passed to
it. An earlier revision closed whatever lay on top of the node stack instead. Nothing is pushed
onto that stack when an element opens no node, so an element that opened none closed its parent.
One kind of element does that, a ``lexeme`` carrying no key, and the consequence was that 2,309
words sat in no word group at all, because nothing reopens a word group once it is closed. The
fault cost no nodes, since the group was closed rather than duplicated, so a node census agreed
on every tier while the words inside the groups did not.

Application configuration
-------------------------
The application configuration file is an output of the final task rather than an input, and
Text-Fabric rewrites it from its own defaults on every rebuild. Several authored settings live in
that file, so a rebuild reverted all of them until ``restore_app_overrides`` existed.
``APP_OVERRIDES`` holds the authored values and is their single source of truth, and
``APP_REMOVALS`` names the keys that Text-Fabric writes back and that are withheld deliberately,
being templates that dereference an identifier of the source lexicon which this dataset does not
publish. ``INT_FEATURES`` below is a fallback that is unreachable in practice, because the
converter always defines the attribute it guards and the metadata file is the source of truth. It
is deliberately not kept in step with that file, since a duplicate that drifts silently is how
integer features came to sort as strings in the first place.
"""

import os
from collections import Counter
from io import BytesIO
from pathlib import Path

import tff.convert.xml as tff_xml
from lxml import etree
from tf.core import files as tf_files
from tf.core.files import initTree, unexpanduser
from tf.core.helpers import console
from tff.convert.xml import XML as XMLConvert
from main.config.env import TF_BACKEND, TF_ORG, TF_REPO


def pin_repo_location():
    repo_root = Path(__file__).resolve().parents[1]
    link = Path.home() / TF_BACKEND / TF_ORG / TF_REPO

    if link.is_symlink() or link.exists():
        if link.resolve() != repo_root:
            raise RuntimeError(
                f"{link} already exists and does not point at {repo_root}"
            )
    else:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(repo_root, target_is_directory=True)
        console(f"linked {link} -> {repo_root}")

    location = (TF_BACKEND, TF_ORG, TF_REPO, "")
    tff_xml.getLocation = lambda targetDir=None: location
    tf_files.getLocation = lambda targetDir=None: location


XNEST = "xnest"
TNEST = "tnest"
TSIB = "tsiblings"
LEXEMES = "lexemes"

INT_FEATURES = {
    "id",
    "rank",
    "reading",
    "sibling",
    "start_idx",
    "end_idx",
    "part",
}

PARENT_EDGE_TAGS = {"word", "word_group", "segment"}
SIBLING_EDGE_TAGS = {"word", "segment"}

SLOT_TAG = "word"

LEXEME_TAG = "lexeme"
LEXEME_KEY = "rank_lex"

TEXT_TAG = "text"
TEXT_KEY = "text"
TEXTS = "texts"

CROSSREF = "crossref"
ADDRESSES = "addresses"
ADDRESS_NOW = "address_now"


def _manuscript_order(folderName):
    """Sort key that places the directories of one manuscript next to each other.

    The serialiser names a directory with a numeric prefix in the order the ranges were written,
    so the integer already carries the grouping and only the string sort loses it. A directory
    with no numeric prefix sorts after the numbered ones, by name, rather than raising.
    """
    head = folderName.split("_", 1)[0]
    return (0, int(head), folderName) if head.isdigit() else (1, 0, folderName)


class XMLToTFConverter(XMLConvert):
    def __init__(self, **kwargs):
        options = dict(
            verbose=3,
            xml="latest",
            tf="0.1",
        )
        options.update(kwargs)

        if "convertTaskCustom" not in options:
            options["convertTaskCustom"] = self.convertTaskCustom

        super().__init__(**options)

    @staticmethod
    def convertTaskCustom(self):
        """Implementation of the convert task, which sets up the walker machinery."""
        if not self.good:
            return

        verbose = self.verbose
        tfPath = self.tfPath
        xmlPath = self.xmlPath

        if verbose == 1:
            console(
                f"XML to TF converting: {unexpanduser(xmlPath)} => {unexpanduser(tfPath)}"
            )

        slotType = SLOT_TAG

        otext = {
            "fmt:text-orig-full": "{voc_utf8}{trailer}",
            "fmt:text-cons": "{cons_utf8}{trailer}",
            "fmt:text-trans-full": "{voc}{trailer}",
            "fmt:text-trans-cons": "{cons}{trailer}",
            "sectionTypes": "book,chapter,verse",
            "sectionFeatures": "book,chapter,verse",
            "structureTypes": "text,book,chapter,verse",
            "structureFeatures": "text,book,chapter,verse",
        }

        tfVersion = self.tfVersion
        xmlVersion = self.xmlVersion
        generic = self.generic
        generic["sourceFormat"] = "XML"
        generic["version"] = tfVersion
        generic["xmlVersion"] = xmlVersion

        intFeatures = self.intFeatures if hasattr(self, "intFeatures") else INT_FEATURES
        featureMeta = self.featureMeta

        initTree(tfPath, fresh=True, gentle=True)

        cv = self.getConverter()

        self.good = cv.walk(
            self.getDirector(),
            slotType,
            otext=otext,
            generic=generic,
            intFeatures=intFeatures,
            featureMeta=featureMeta,
            generateTf=True,
        )

    def getDirector(self):
        """Factory for the director function that walks the sources and yields actions."""
        verbose = self.verbose
        xmlPath = self.xmlPath
        featureMeta = self.featureMeta
        transform = self.transform

        PASS_THROUGH = set("""
            xml
            """.strip().split())

        transformFunc = (
            (lambda x: BytesIO(x.encode("utf-8")))
            if transform is None
            else (lambda x: BytesIO(transform(x).encode("utf-8")))
        )

        parser = self.getParser()

        def walkNode(cv, cur, xnode):
            """Deal with a single element, recursively."""
            tag = etree.QName(xnode.tag).localname

            wants_parent_edge = tag in PARENT_EDGE_TAGS
            wants_sibling_edge = tag in SIBLING_EDGE_TAGS

            atts = {etree.QName(k).localname: v for (k, v) in xnode.attrib.items()}
            cur[XNEST].append((tag, atts))

            curNode = beforeChildren(cv, cur, xnode, tag, atts)

            if curNode is not None:
                if len(cur[TNEST]):
                    if wants_parent_edge:
                        parentNode = cur[TNEST][-1]
                        cv.edge(curNode, parentNode, parent=None)

                cur[TNEST].append(curNode)

                if len(cur[TSIB]):
                    if wants_sibling_edge:
                        siblings = cur[TSIB][-1]
                        nSiblings = len(siblings)
                        for i, sib in enumerate(siblings):
                            cv.edge(sib, curNode, sibling=nSiblings - i)
                        siblings.append(curNode)

                cur[TSIB].append([])

            for child in xnode.iterchildren(tag=etree.Element):
                walkNode(cv, cur, child)

            afterChildren(cv, cur, xnode, tag, atts, curNode)

            if curNode is not None:
                if len(cur[TNEST]):
                    cur[TNEST].pop()
                if len(cur[TSIB]):
                    cur[TSIB].pop()

            cur[XNEST].pop()
            afterTag(cv, cur, xnode, tag, atts)

        def beforeChildren(cv, cur, xnode, tag, atts):
            """Open the node for this element, if it takes one, and return it."""
            if tag in PASS_THROUGH:
                return None
            curNode = None

            if tag == LEXEME_TAG:
                key = atts.get(LEXEME_KEY)
                if not key:
                    return None
                known = cur.setdefault(LEXEMES, {})
                curNode = known.get(key)
                if curNode is None:
                    curNode = cv.node(tag)
                    cv.feature(curNode, **atts)
                    known[key] = curNode
                else:
                    cv.resume(curNode)
                return curNode

            if tag == TEXT_TAG:
                key = atts.get(TEXT_KEY)
                if not key:
                    curNode = cv.node(tag)
                    if len(atts):
                        cv.feature(curNode, **atts)
                    return curNode
                known = cur.setdefault(TEXTS, {})
                curNode = known.get(key)
                if curNode is None:
                    curNode = cv.node(tag)
                    cv.feature(curNode, **atts)
                    known[key] = curNode
                else:
                    cv.resume(curNode)
                cur[ADDRESS_NOW]["manuscript"] = atts.get("manuscript", key)
                cur[ADDRESS_NOW]["view"] = atts.get("view")
                return curNode

            if tag == SLOT_TAG:
                curNode = cv.slot()
                cv.feature(curNode, **atts)
            else:
                if tag not in PASS_THROUGH:
                    curNode = cv.node(tag)
                    if len(atts):
                        cv.feature(curNode, **atts)

            if tag == "book":
                cur[ADDRESS_NOW]["book"] = atts.get("book")
            elif tag == "chapter":
                cur[ADDRESS_NOW]["chapter"] = atts.get("chapter")
            elif tag == "verse" and curNode is not None:
                here = cur[ADDRESS_NOW]
                key = (here.get("book"), here.get("chapter"), atts.get("verse"))
                cur[ADDRESSES].setdefault(key, []).append(
                    (here.get("manuscript"), here.get("view"), curNode)
                )

            return curNode

        def afterChildren(cv, cur, xnode, tag, atts, curNode):
            """Close the node that this element opened, and no other."""
            if curNode is not None:
                cv.terminate(curNode)

        def afterTag(cv, cur, xnode, tag, atts):
            """Deal with the material following an element and before the next tag."""
            pass

        def director(cv):
            """Walk the XML sources, firing the actions that build the dataset."""
            cur = {}
            i = 0
            cur[LEXEMES] = {}
            cur[TEXTS] = {}
            cur[ADDRESSES] = {}
            cur[ADDRESS_NOW] = {}

            for xmlFolder, xmlFiles in sorted(
                self.getXML(), key=lambda folderAndFiles: _manuscript_order(folderAndFiles[0])
            ):
                for xmlFile in xmlFiles:
                    i += 1
                    console(f"\r{i:>4} {xmlFile:<50}", newline=False)

                    with open(
                        f"{xmlPath}/{xmlFolder}/{xmlFile}", encoding="utf8"
                    ) as fh:
                        text = fh.read()
                        text_bytes = transformFunc(text)

                        tree = etree.parse(text_bytes, parser)
                        root = tree.getroot()

                        cur[XNEST] = []
                        cur[TNEST] = []
                        cur[TSIB] = []

                        walkNode(cv, cur, root)

            console("")

            nEdges = Counter()
            for witnesses in cur[ADDRESSES].values():
                if len(witnesses) < 2:
                    continue
                for i, (msA, viewA, nodeA) in enumerate(witnesses):
                    for msB, viewB, nodeB in witnesses[i + 1:]:
                        if msA != msB:
                            relation = "witness"
                        elif viewA != viewB:
                            relation = "view"
                        else:
                            relation = "same_witness"
                        cv.edge(nodeA, nodeB, crossref=relation)
                        cv.edge(nodeB, nodeA, crossref=relation)
                        nEdges[relation] += 2
            console(
                f"crossref: {sum(nEdges.values()):,} ordered edges over "
                f"{sum(1 for w in cur[ADDRESSES].values() if len(w) > 1):,} shared addresses ("
                + ", ".join(f"{n:,} {r}" for r, n in sorted(nEdges.items())) + ")"
            )

            for fName in featureMeta:
                if not cv.occurs(fName):
                    cv.meta(fName)
            for fName in cv.features():
                if fName not in featureMeta:
                    cv.meta(
                        fName,
                        description=f"Auto-extracted XML attribute {fName}",
                        valueType="str",
                    )

            if verbose == 1:
                console("source reading done")
            return True

        return director


APP_OVERRIDES = {
    ("writing",): "hbo",
    ("typeDisplay", "lexeme"): {
        "lexOcc": "word",
        "template": "{lex}",
        "features": "lex lex0 lex_utf8 freq_lex rank_lex",
    },
    ("docs", "featureBase"): "{docBase}/transcription.md#<feature>",
    ("docs", "docPage"): "about",
    ("docs", "featurePage"): "transcription",
    ("provenanceSpec", "doi"): "10.5281/zenodo.21925395",
    ("provenanceSpec", "webBase"): "https://github.com/ETCBC/targum",
    ("provenanceSpec", "webUrl"): "{webBase}/tree/{branch}#<1>-<2>-<3>",
    ("provenanceSpec", "backend"): "github",
    ("provenanceSpec", "org"): "sfir1",
    ("provenanceSpec", "repo"): "dissertation",
    ("typeDisplay", "segment"): {
        "template": "{type}",
        "features": "type start_idx end_idx",
    },
    ("typeDisplay", "word_group"): {
        "template": "{g_voc}",
        "features": "reading rank",
    },
}

APP_REMOVALS = [("provenanceSpec", "webUrlLex"), ("provenanceSpec", "webLexId")]


def restore_app_overrides():
    """Re-apply the authored application settings that the final task overwrites."""
    import yaml

    from main.config.env import BASE_DIR

    path = os.path.join(str(BASE_DIR), "app", "config.yaml")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}

    changed = []
    for keys, value in APP_OVERRIDES.items():
        node = config
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        if node.get(keys[-1]) != value:
            node[keys[-1]] = value
            changed.append(".".join(keys))
    for keys in APP_REMOVALS:
        node = config
        for k in keys[:-1]:
            node = node.get(k, {})
        if isinstance(node, dict) and keys[-1] in node:
            del node[keys[-1]]
            changed.append("-" + ".".join(keys))

    if changed:
        with open(path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(config, fh, sort_keys=True, allow_unicode=True,
                           default_flow_style=False)
        print("restored app/config.yaml: %s" % ", ".join(changed))
    return changed


def convert_xml_to_tf():
    pin_repo_location()
    converter = XMLToTFConverter()

    converter.task(check=True, verbose=True)
    converter.task(convert=True, verbose=True)
    converter.task(load=True, verbose=True)
    converter.task(app=True, verbose=True)
    restore_app_overrides()


if __name__ == "__main__":
    convert_xml_to_tf()
