"""
Serialisation of the corpus from its relational form into XML and then into Text-Fabric.

This module reads one publication view per manuscript, writes an XML tree per view beneath
``xml/``, and invokes ``programs/xml_to_tf.py`` to compile those trees into a Text-Fabric
dataset beneath ``tf/``. The relational database is the source of truth, and both serialised
forms are regenerated from it rather than edited in place.

Node hierarchy
--------------
The serialised tree nests as text, book, chapter, verse, segment, word_group, lexeme, word.
A ``word`` is the Text-Fabric slot. A ``word_group`` is one space-delimited unit of the line
together with any readings that compete for its position.

``lexeme`` is the only level in that list which does not assert containment. A lexeme is not
located inside a verse, because its occurrences are distributed across the whole corpus. The
nesting is a serialisation convenience: each word is wrapped in a ``lexeme`` element carrying
the lexical attributes, and the compiler builds a single Text-Fabric node from all elements
belonging to one lexeme by resuming a node it has already opened rather than opening a second
one. The resulting graph holds 6,363 lexeme nodes with discontiguous slot sets, while the XML
remains a tree, which is the only shape that both ``generate_xml`` below and the compiler are
able to traverse. The level sits immediately above ``word`` so that each element encloses
exactly the words of which it is the lexeme. Placed any higher, it would enclose words
belonging to other lexemes.

The published schema
--------------------
``SCHEMA_ROWS`` holds one row per emitted XML attribute, as a triple of element name, attribute
name and source column. ``TAGS``, ``ATTRS`` and ``COLS`` are its three columns, held as
separate lists because ``_build_schema`` pairs them by position and ``sql_to_xml.from_view``
builds its SELECT clause from ``COLS``. The table is therefore the publication boundary of the
dataset. A column that exists in the underlying view but has no row here is read by the
ordering clause or by the internal consistency checks, and is withheld deliberately.

Two classes of column are withheld. The first is the surrogate keys of the relational model,
whose values carry no meaning outside it. Verse identifiers in particular are not unique across
the three underlying table families, so a consumer joining on one without also knowing its
family would silently read an unrelated row. The canonical address of a verse and the ``uid``
of a word are published as the identities instead. The second is any attribute whose value a
consumer can recompute from the rest of the dataset, or whose value does not vary.

``generate_xml`` identifies a node by the string form of its attribute dictionary and opens a
new element whenever that value changes between consecutive rows. The set of published
attributes is consequently load bearing for the node counts, and every removal from this table
was measured against the tiers it could cause to collapse. Under the present schema the dataset
holds 496,532 word, 368,322 word_group and 6,363 lexeme nodes. The lexeme tier is keyed by
``rank_lex``, a total ranking over 1 to 6,363 and therefore a bijection onto the lexeme nodes.

Elements carry attributes only and never character data. Text content is published through the
named attributes of each tier, so the consonantal and vocalised forms of a word are read from
``cons``, ``cons_utf8``, ``voc`` and ``voc_utf8`` rather than from the element body.

``convert_xml_to_tf`` runs the compiler as a subprocess from the ``programs/`` directory and
passes the source root on ``PYTHONPATH`` explicitly, so that the step behaves identically
however the pipeline was launched.
"""

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List, Optional
from xml.dom import minidom

from main.config import XML_DIR, PROGRAMS_DIR, BASE_DIR
from main.loaders.sql_to_xml import XMLConversionRepository

HIERARCHY = [
    "text",
    "book",
    "chapter",
    "verse",
    "segment",
    "word_group",
    "lexeme",
    "word",
]

SCHEMA_ROWS = [
    ("word_group", "id", "word_group_id"),
    ("word_group", "rank", "word_group_rank"),
    ("word_group", "reading", "word_group_reading"),
    ("word_group", "g_voc", "word_group_voc"),
    ("word_group", "g_cons", "word_group_cons"),
    ("word_group", "g_voc_utf8", "word_group_voc_utf8"),
    ("word_group", "g_cons_utf8", "word_group_cons_utf8"),
    ("word", "source", "word_source"),
    ("word", "part", "word_part"),
    ("word", "trailer", "word_trailer"),
    ("word", "start_idx", "word_start_idx"),
    ("word", "end_idx", "word_end_idx"),
    ("word", "uid", "word_uid"),
    ("word", "lex", "word_lex"),
    ("word", "lex0", "word_lex0"),
    ("word", "lex_utf8", "word_lex_utf8"),
    ("word", "cons", "word_cons"),
    ("word", "voc", "word_voc"),
    ("word", "cons_utf8", "word_cons_utf8"),
    ("word", "voc_utf8", "word_voc_utf8"),
    ("word", "root", "word_root"),
    ("word", "gn", "word_gn"),
    ("word", "vs", "word_vs"),
    ("word", "sp", "word_sp"),
    ("word", "st", "word_st"),
    ("word", "nu", "word_nu"),
    ("word", "gloss", "word_gloss"),
    ("word", "definition", "word_definition"),
    ("word", "description", "word_description"),
    ("lexeme", "lex", "lexeme_lex"),
    ("lexeme", "lex0", "lexeme_lex0"),
    ("lexeme", "lex_utf8", "lexeme_lex_utf8"),
    ("lexeme", "freq_lex", "lexeme_freq_lex"),
    ("lexeme", "rank_lex", "lexeme_rank_lex"),
    ("segment", "id", "segment_id"),
    ("segment", "start_idx", "segment_start_idx"),
    ("segment", "end_idx", "segment_end_idx"),
    ("segment", "type", "segment_type"),
    ("segment", "rank", "segment_rank"),
    ("segment", "segment", "segment_segment"),
    ("segment", "segment_utf8", "segment_segment_utf8"),
    ("verse", "verse", "verse_verse"),
    ("verse", "line", "verse_line"),
    ("verse", "line_utf8", "verse_line_utf8"),
    ("chapter", "chapter", "chapter_chapter"),
    ("book", "book", "book_book"),
    ("book", "id", "book_id"),
    ("text", "text", "text_text"),
    ("text", "manuscript", "text_manuscript"),
    ("text", "view", "text_view"),
]


TAGS = [row[0] for row in SCHEMA_ROWS]
ATTRS = [row[1] for row in SCHEMA_ROWS]
COLS = [row[2] for row in SCHEMA_ROWS]


class TFPipeline:
    """Convert the relational representation of the corpus into a Text-Fabric dataset.

    One instance serialises a range of a single publication view into a well formed XML
    document that follows the node hierarchy declared above, writes that document beneath
    ``xml/``, and then invokes the compiler that produces the Text-Fabric feature files.
    """

    COUNTER = 1

    def __init__(
        self,
        range_start: int,
        range_end: int,
        file_suffix: Optional[str] = None,
    ):
        self.schema = self._build_schema()
        self.range_start = range_start
        self.range_end = range_end
        self.file_suffix = file_suffix
        self.xml_conversion_repo = XMLConversionRepository()

    def from_view(self, view_name: str) -> None:
        data_rows = self.xml_conversion_repo.from_view(
            self.range_start, self.range_end, view_name
        )
        print(f"{len(data_rows)} rows fetched for {view_name}. Generating XML")
        self.generate_xml(data_rows)
        print("XML generated, converting to TF")

    def _build_schema(self) -> Dict[str, Any]:
        schema = {}
        for i in range(len(TAGS)):
            tag, attr, sp, col = TAGS[i], ATTRS[i], "", COLS[i]
            if tag not in schema:
                schema[tag] = {}
            if attr not in schema[tag]:
                schema[tag][attr] = []

            schema[tag][attr].append({"sp": sp, "col_name": col})

        for tag in schema:
            for attr in schema[tag]:
                schema[tag][attr] = sorted(
                    schema[tag][attr],
                    key=lambda x: int(x["sp"]) if x["sp"] else 0,
                )
        return schema

    def _extract_attrs(self, tag: str, row_dict: Dict[str, Any]) -> Dict[str, str]:
        res = {}
        for attr, parts in self.schema.get(tag, {}).items():
            vals = []
            for p in parts:
                val = row_dict.get(p["col_name"])
                if val is not None:
                    if attr == "trailer":
                        vals.append(val)
                    else:
                        clean_val = str(val).strip()
                        if clean_val:
                            vals.append(clean_val)

            if vals:
                res[attr] = ",".join(vals)
        return res

    def _get_xml_file_path(self, row):
        tentative_str = str(row.get("text_text") or "").replace(" ", "_")
        return str(TFPipeline.COUNTER) + "_" + tentative_str

    def generate_xml(self, data_rows: List[Dict]) -> str | None:
        root = None
        current_nodes = {level: None for level in HIERARCHY}
        current_identifiers = {level: None for level in HIERARCHY}
        just_created = {level: False for level in HIERARCHY}

        for row in data_rows:
            for level_idx, level in enumerate(HIERARCHY):
                level_attrs = self._extract_attrs(level, row)
                is_new = False
                identifier = str(level_attrs)

                parent_changed = False
                if level_idx > 0:
                    parent_level = HIERARCHY[level_idx - 1]
                    parent_changed = just_created[parent_level]

                if current_identifiers[level] != identifier or parent_changed:
                    is_new = True

                just_created[level] = is_new

                if is_new:
                    new_el = ET.Element(level, level_attrs)


                    for child_level in HIERARCHY[level_idx + 1 :]:
                        current_identifiers[child_level] = None

                    if level_idx == 0:
                        if root is None:
                            root = new_el
                    else:
                        parent_node = current_nodes[HIERARCHY[level_idx - 1]]
                        if parent_node is not None:
                            parent_node.append(new_el)

                    current_nodes[level] = new_el
                    current_identifiers[level] = identifier

        if root is not None:

            xmlstr = minidom.parseString(
                ET.tostring(root, encoding="utf-8")
            ).toprettyxml(indent="    ")
            xml_file_name = self._get_xml_file_path(data_rows[0])
            self._write_out_xml(xmlstr, xml_file_name)
            print(f"Successfully generated {xml_file_name}")
            TFPipeline.COUNTER += 1
        else:
            print("No data matched the provided query bounds.")

    def _write_out_xml(self, xmlstr: str, xml_file_name: str):
        xml_cleaned = "\n".join([line for line in xmlstr.split("\n") if line.strip()])
        today_str = datetime.now().strftime("%Y-%m-%d")
        output_folder = os.path.join(XML_DIR, today_str, xml_file_name)
        os.makedirs(output_folder, exist_ok=True)

        output_xml_path = os.path.join(output_folder, f"{xml_file_name}.xml")
        with open(output_xml_path, "w", encoding="utf-8") as f:
            f.write(xml_cleaned)

    @staticmethod
    def convert_xml_to_tf():
        script_name = "xml_to_tf.py"
        try:
            print(
                f"Attempting to executing {script_name} within context: {PROGRAMS_DIR}"
            )
            env = dict(os.environ)
            src_dir = str(BASE_DIR / "src")
            existing = env.get("PYTHONPATH")
            env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{existing}" if existing else src_dir
            result = subprocess.run(
                [sys.executable, script_name],
                cwd=PROGRAMS_DIR,
                check=True,
                text=True,
                env=env,
            )
            if result.stdout:
                print("Output:\n", result.stdout)

            TFPipeline.invalidate_corpus_caches()

        except subprocess.CalledProcessError as e:
            print(f"An error occurred while running {script_name}.")
            print(f"Error output:\n{e.stderr}")
            raise

    @staticmethod
    def invalidate_corpus_caches() -> List[str]:
        """Delete the binary index that reading clients cache inside each corpus directory.

        The index is keyed on the name of the corpus and holds no staleness check against the
        feature files beside it, so a rebuild would otherwise leave it answering for the
        previous version of the dataset. The cache lives on disk rather than in a running
        process, so restarting a client does not clear it. Invalidation therefore belongs in
        the step that produces a new dataset.

        Only a directory named exactly ``.cfm`` immediately below a version directory of
        ``tf/`` is removed. The feature sources and the binary cache that the compiler itself
        rebuilds are left untouched. Removal is attempted rather than required, so a cache that
        cannot be deleted is reported without failing a compile that has already succeeded.
        """
        removed: List[str] = []
        tf_root = BASE_DIR / "tf"
        if not tf_root.is_dir():
            return removed
        for version in sorted(tf_root.iterdir()):
            cache = version / ".cfm"
            if version.is_dir() and cache.is_dir():
                shutil.rmtree(cache, ignore_errors=True)
                if cache.exists():
                    print(f"could not remove the stale corpus index at {cache}")
                else:
                    removed.append(str(cache))
                    print(f"removed the stale corpus index at {cache}")
        return removed


if __name__ == "__main__":
    psj_view_ids = [
        (3065, 4594),
        (4595, 5803),
        (5804, 6654),
        (6655, 7936),
        (7937, 8895),
    ]
    for start_id, end_id in psj_view_ids:
        print(f"\n--- Processing range: {start_id} to {end_id} ---")
        tf_pipeline = TFPipeline(range_start=start_id, range_end=end_id)
        tf_pipeline.from_view("psj_tf")

    fg_view_id_ranges = [
        (275, 485),  # Fragment Targum P Genesis
        (486, 665),  # Fragment Targum P Exodus
        (666, 698),  # Fragment Targum P Leviticus
        (732, 823),  # Fragment Targum P Numbers
        (824, 901),  # Fragment Targum P Deuteronomy
        (902, 905),  # Fragment Targum Pa Exodus
        (906, 1155),  # Fragment Targum V Genesis
        (1156, 1364),  # Fragment Targum V Exodus
        (1365, 1444),  # Fragment Targum V Leviticus
        (1445, 1607),  # Fragment Targum V Numbers
        (1608, 1826),  # Fragment Targum V Deuteronomy
        (18099, 18099),  # Fragment Targum N Genesis
        (18100, 18100),  # Fragment Targum N Leviticus
        (18101, 18105),  # Fragment Targum N Deuteronomy
    ]
    for start_id, end_id in fg_view_id_ranges:
        print(f"\n--- Processing range: {start_id} to {end_id} ---")
        tf_pipeline = TFPipeline(range_start=start_id, range_end=end_id)
        tf_pipeline.from_view("frag_targ_tf")

    cg_view_ids = [
        (1827, 1901),
        (1902, 1929),
        (1930, 1990),
        (1991, 2202),
        (2203, 2482),
        (2483, 2601),
        (2602, 2609),
        (2610, 2612),
        (2613, 2628),
        (2629, 2633),
        (2634, 2647),
        (2648, 2662),
        (2663, 2676),
        (2677, 2713),
        (2714, 2755),
        (2756, 2863),
        (2864, 2866),
        (2867, 2871),
        (2872, 2910),
        (2911, 2931),
        (2933, 2938),
        (2939, 2939),
        (2941, 2945),
        (2947, 2959),
        (2961, 2972),
        (2973, 2987),
        (2988, 2988),
        (2989, 2989),
        (2990, 2994),
        (2995, 2995),
        (2996, 2996),
        (2997, 3003),
        (3004, 3029),
        (3030, 3031),
        (3032, 3056),
        (3057, 3058),
        (3059, 3059),
        (3060, 3061),
        (3062, 3064),
    ]

    for start_id, end_id in cg_view_ids:
        print(f"\n--- Processing range: {start_id} to {end_id} ---")
        tf_pipeline = TFPipeline(range_start=start_id, range_end=end_id)
        tf_pipeline.from_view("cairo_genizah_tf")

    neofiti_base_raw_id = [
        (1, 1524),
        (1525, 2737),
        (2738, 3596),
        (3597, 4884),
        (4885, 5843),
    ]
    for start_id, end_id in neofiti_base_raw_id:
        print(f"\n--- Processing range: {start_id} to {end_id} ---")
        tf_pipeline = TFPipeline(
            range_start=start_id, range_end=end_id, file_suffix="_BASE_RAW"
        )
        tf_pipeline.from_view("neofiti_base_raw_tf")

    neofiti_full_ids = [
        (12248, 13771),
        (13772, 14984),
        (14985, 15843),
        (15844, 17132),
        (17133, 18091),
    ]
    for start_id, end_id in neofiti_full_ids:
        print(f"\n--- Processing range: {start_id} to {end_id} ---")
        tf_pipeline = TFPipeline(
            range_start=start_id, range_end=end_id, file_suffix="_FULL_TEXT"
        )
        tf_pipeline.from_view("neofiti_full_tf")

    TFPipeline.convert_xml_to_tf()
