import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List, Optional
from xml.dom import minidom

from main.config import XML_DIR, PROGRAMS_DIR
from main.pipeline.sql_to_xml import XMLConversionRepository

# text > book > chapter > verse > segment > word_group > word.
#
# `word_group` is the one space-delimited unit of the line together with the readings
# that compete for its position. `config/xml.yml` has carried a declaration for this node type
# word is the Text-Fabric slot.
HIERARCHY = [
    "text",
    "book",
    "chapter",
    "verse",
    "segment",
    "word_group",
    "word",
]

# One row per emitted XML attribute: (tag, attribute, view column). TAGS, ATTRS and COLS are
# the three columns of this table, kept as separate lists because `_build_schema` pairs them by
# position and `sql_to_xml.from_view` builds its SELECT from COLS.
#
SCHEMA_ROWS = [
    ("word_group", "id", "word_group_id"),
    ("word_group", "rank", "word_group_rank"),
    ("word_group", "reading", "word_group_reading"),
    ("word_group", "g_voc", "word_group_voc"),
    ("word_group", "g_cons", "word_group_cons"),
    ("word_group", "g_voc_utf8", "word_group_voc_utf8"),
    ("word_group", "g_cons_utf8", "word_group_cons_utf8"),
    ("word", "id", "word_id"),
    ("word", "source", "word_source"),
    ("word", "trailer", "word_trailer"),
    ("word", "uid", "word_uid"),
    ("word", "lex", "word_lex"),
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
    ("segment", "id", "segment_id"),
    ("segment", "start_idx", "segment_start_idx"),
    ("segment", "end_idx", "segment_end_idx"),
    ("segment", "type", "segment_type"),
    ("segment", "rank", "segment_rank"),
    ("segment", "segment", "segment_segment"),
    ("segment", "segment_utf8", "segment_segment_utf8"),
    ("verse", "verse", "verse_verse"),
    ("verse", "uid", "verse_uid"),
    ("verse", "line", "verse_line"),
    ("verse", "line_utf8", "verse_line_utf8"),
    ("chapter", "chapter", "chapter_chapter"),
    ("book", "book", "book_book"),
    ("book", "id", "book_id"),
    ("text", "text", "text_text"),
    ("text", "view", "text_view"),
]

TAGS = [row[0] for row in SCHEMA_ROWS]
ATTRS = [row[1] for row in SCHEMA_ROWS]
COLS = [row[2] for row in SCHEMA_ROWS]


class TFPipeline:
    """
    Converts processed text data with intermediate representations in SQL into Text-Fabric (TF) graphs.

    Manages the generation of well-formed XML documents mapped to the specific
    structural hierarchy. It handles file I/O operations for the XML output and
    orchestrates the execution of external subprocess scripts (e.g., `xml_to_tf.py`) to
    compile the raw XML into a fully functional Text-Fabric dataset.
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
        # Note: If generating many XMLs sequentially, you may want to move
        # _convert_xml_to_tf() outside this method so it only runs once at the end.
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

                    if level == "word" and "cons_utf8" in level_attrs:
                        new_el.text = level_attrs["cons_utf8"]

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
            result = subprocess.run(
                [sys.executable, script_name],
                cwd=PROGRAMS_DIR,
                check=True,
                text=True,
            )
            if result.stdout:
                print("Output:\n", result.stdout)

        except subprocess.CalledProcessError as e:
            print(f"An error occurred while running {script_name}.")
            print(f"Error output:\n{e.stderr}")
            raise


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
