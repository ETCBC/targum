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
