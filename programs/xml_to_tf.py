from io import BytesIO

from lxml import etree
from tf.core.files import initTree, unexpanduser
from tf.core.helpers import console
from tff.convert.xml import XML as XMLConvert

XNEST = "xnest"
TNEST = "tnest"
TSIB = "tsiblings"

INT_FEATURES = {
    "id",
    "rank",
    "sibling",
    "start_idx",
    "end_idx",
    "source_id",
    "parent_id",
}
NESTABLE_TAGS = {"m", "mg", "segment"}

SLOT_TAG = "m"


class XMLToTFConverter(XMLConvert):
    def __init__(self, **kwargs):
        options = dict(
            verbose=3,
            xml="latest",
            tf="0.0.1-alpha",
        )
        options.update(kwargs)

        # Pass the overridden convertTaskCustom to the parent class constructor
        if "convertTaskCustom" not in options:
            options["convertTaskCustom"] = self.convertTaskCustom

        super().__init__(**options)

    @staticmethod
    def convertTaskCustom(self):
        """
        Implementation of the 'convert' task.
        Sets up the `tf.convert.walker` machinery.
        """
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

        """
        # Format text output and define the main logical sections
        # N.B. sectionTypes and sectionFeatures must have an attribute that also matches the tag, such as <text "text"="some text">...
        # this is a weird feature of cv.walk(), but if the XML isn't formatted like this, self._checkFeatures() will fail and cause self.good = False
        # THIS MUST MATCH FOR ALL 3 SECTION FEATURES/OTYPES: that means for
        otext = {
            "fmt:text-orig-full": "{g_voc_utf8}{trailer}",
            "fmt:text-cons": "{g_cons_utf8}{trailer}",
            "fmt:lex-orig-full": "{g_lex_utf8}{trailer}",
            "fmt:text-trans-full": "{g_voc}{trailer}",
            "fmt:text-trans-cons": "{g_cons}{trailer}",
            "sectionTypes": "text,book,chapter",
            "sectionFeatures": "text,book,chapter",
        }
        there must be SQL columns such as text_text, chapter_chapter, book_book corresponding tags in XML
        """
        otext = {
            "fmt:text-orig-full": "{g_voc_utf8}{trailer}",
            "fmt:lex-orig-full": "{g_lex_utf8}{trailer}",
            "fmt:text-cons": "{g_cons_utf8}{trailer}",
            "fmt:text-trans-full": "{g_voc}{trailer}",
            "fmt:text-trans-cons": "{g_cons}{trailer}",
            "sectionTypes": "text,book,chapter",
            "sectionFeatures": "text,book,chapter",
        }

        # Retrieve configurations which could optionally be loaded from xml.yaml
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
        """
        Factory for the director function.
        Walks through the source data and yields actions to produce the TF dataset.
        """
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
            """Internal function to deal with a single element.

            Will be called recursively.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.
            xnode: object
                An LXML element node.
            """
            tag = etree.QName(xnode.tag).localname

            # Determine if we want to track siblings for this element.
            # Tracking siblings on everything is memory intensive, so we limit it.
            nestable = tag in NESTABLE_TAGS

            atts = {etree.QName(k).localname: v for (k, v) in xnode.attrib.items()}
            cur[XNEST].append((tag, atts))

            # Initialize the Node/Slot
            curNode = beforeChildren(cv, cur, xnode, tag, atts)

            if curNode is not None:
                if len(cur[TNEST]):
                    if nestable:
                        parentNode = cur[TNEST][-1]
                        cv.edge(curNode, parentNode, parent=None)

                cur[TNEST].append(curNode)

                if len(cur[TSIB]):
                    if nestable:
                        siblings = cur[TSIB][-1]
                        nSiblings = len(siblings)
                        for i, sib in enumerate(siblings):
                            cv.edge(sib, curNode, sibling=nSiblings - i)
                        siblings.append(curNode)

                cur[TSIB].append([])

            # traverse children
            for child in xnode.iterchildren(tag=etree.Element):
                walkNode(cv, cur, child)

            # terminate scope
            afterChildren(cv, cur, xnode, tag, atts)

            if curNode is not None:
                if len(cur[TNEST]):
                    cur[TNEST].pop()
                if len(cur[TSIB]):
                    cur[TSIB].pop()

            cur[XNEST].pop()
            afterTag(cv, cur, xnode, tag, atts)

        def beforeChildren(cv, cur, xnode, tag, atts):
            """Actions before dealing with the element's children.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.
            xnode: object
                An LXML element node.
            tag: string
                The tag of the LXML node.
            atts: dict
                The attributes of the LXML node, possibly renamed.

            Returns
            -------
            tuple | void
                The resulting TF node, if any, else None
            """
            if tag in PASS_THROUGH:
                return None
            curNode = None

            if tag == "m":
                # For words, assign the slot tag and extract the inner text explicitly
                if xnode.text:
                    atts["text"] = xnode.text.strip()

                curNode = cv.slot()
                cv.feature(curNode, **atts)
            else:
                # For all other tags (isolect, dialect, subtext, view, mg), create a parent node
                if tag not in PASS_THROUGH:
                    curNode = cv.node(tag)
                    if len(atts):
                        cv.feature(curNode, **atts)

            return curNode

        def afterChildren(cv, cur, xnode, tag, atts):
            if len(cur[TNEST]) and tag not in PASS_THROUGH:
                curNode = cur[TNEST][-1]
                cv.terminate(curNode)

        def afterTag(cv, cur, xnode, tag, atts):
            """Node actions after dealing with the children and after the end tag.

            This is the place where we process the `tail` of an LXML node: the
            text material after the element and before the next open/close
            tag of any element.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            cur: dict
                Various pieces of data collected during walking
                and relevant for some next steps in the walk.
            xnode: object
                An LXML element node.
            tag: string
                The tag of the LXML node.
            atts: dict
                The attributes of the LXML node, possibly renamed.
            """
            pass

        def director(cv):
            """Director function.

            Here we program a walk through the XML sources.
            At every step of the walk we fire some actions that build TF nodes
            and assign features for them.

            Because everything is rather dynamic, we generate fairly standard
            metadata for the features.

            Parameters
            ----------
            cv: object
                The convertor object, needed to issue actions.
            """
            cur = {}
            i = 0

            # The self.getXML() generator loops through the versions handled by tff.convert.xml
            for xmlFolder, xmlFiles in self.getXML():
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

                        # Reset memory stacks for every file
                        cur[XNEST] = []
                        cur[TNEST] = []
                        cur[TSIB] = []

                        walkNode(cv, cur, root)

            console("")

            # post-process metadata: register features not strictly captured in xml.yaml
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

            # # Append manual descriptions
            # cv.meta(
            #     "text",
            #     description="Literal text of the word component",
            #     valueType="str",
            # )

            if verbose == 1:
                console("source reading done")
            return True

        return director


def convert_xml_to_tf():
    converter = XMLToTFConverter()

    converter.task(check=True, verbose=True)
    converter.task(convert=True, verbose=True)
    converter.task(load=True, verbose=True)
    converter.task(app=True, verbose=True)


if __name__ == "__main__":
    convert_xml_to_tf()
