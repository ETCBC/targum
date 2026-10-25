"""
Retrieval of corpus rows from the relational publication views, in publication order.

Two access paths are provided. ``from_view`` reads a publication view and projects exactly the
columns named in the published schema, which is the path the serialiser uses.
``from_materialized_view`` reads an intermediate materialised view in its own stored order and
exists for inspection of the layer beneath.

The publication order
---------------------
``TF_ORDER_BY`` fixes the order in which rows are serialised, and therefore fixes the nesting
of the XML. The serialiser opens a new element whenever the attributes of a tier change between
consecutive rows, so a tier is only safe to nest if its rows are contiguous under this order.
The keys are, in sequence:

``verse_sort``
    The position of the verse within its manuscript. This column is carried by the publication
    view for the ordering clause alone and is published as no feature.
``verse_uid``
    The verse identifier, which makes the ordering of verses total.
``word_group_rank``
    The word group within the verse. The value is dense over 0 to n-1 within every verse and is
    never null.
``word_group_reading``
    The base reading, ordered before the variant readings that are printed after it. Each
    group restarts its internal ranking at zero, so without this key the competing readings of
    one word group interleave. Measured across the corpus, 1,836 of the 6,249 word groups that
    carry two readings were affected.
``word_rank``
    The established order of words inside one word group. A null value means that no candidate
    order reproduced the surface form, so nulls sort last and those groups retain the order in
    which they were recorded.
``word_part``
    Which part of a word this row is, where an editorial boundary divides one lexical entry in
    two. The parts share every key above, so without this key their order would fall to the
    surrogate key and the two halves of a word could be serialised in reverse. The parts also
    nest beneath different segments, so such a reversal would reorder the segment tier as well.
``word_id``
    The surrogate key, which makes the ordering total.
``word_piece``
    Which whitespace-delimited piece of a lexical entry this row is. Two pieces of one entry
    share every key above, including ``word_part``, so without this key the pieces of a
    multi-word entry can be serialised in reverse and the published line is spelled backwards.
    It is the final key here for the same reason that it is the final key of the materialised
    view and of the running character offset: those three orders describe one string and must
    move together.

An earlier revision ordered on the positional indices of the source edition instead. Those
indices are null on every row that the structural layer supplies and the source edition never
indexed, with the result that such rows sorted to the end of a text and nested beneath the
wrong verse. The keys above are complete and are null only where a documented fallback applies.

Ordering on ``verse_uid`` alone would be equivalent for four of the five manuscripts and wrong
for the fragment targums, whose verse identifiers do not run in biblical sequence. 1,518 of
their 1,525 verses sort differently under the two clauses.

The ordering keys are deliberately absent from the published column list. That list is paired
positionally with the element and attribute names of the published schema, so extending it
would change the serialised dataset. SQL permits ordering by columns that are not selected.
"""

from typing import List, Dict

from main.loaders.db import db

TF_ORDER_BY = (
    "ORDER BY verse_sort NULLS LAST, verse_uid, word_group_rank, "
    "word_group_reading NULLS FIRST, word_rank NULLS LAST, word_part, (word_id)::bigint, "
    "word_piece"
)


class XMLConversionRepository:

    def from_materialized_view(
        self,
        range_start: int,
        range_end: int,
        view_name: str,
    ) -> List[Dict]:
        if not (range_start and range_end):
            return [{}]

        where_clause = f" WHERE view_id >= {range_start} AND view_id <= {range_end}"

        query = (
            "select * from " + view_name + where_clause + " order by m_uid::bigint asc"
        )

        with db.get_cursor() as cur:
            cur.execute(query)
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, row)) for row in cur.fetchall()]

    def from_view(
        self,
        range_start: int,
        range_end: int,
        view_name: str,
    ) -> List[Dict]:
        from main.pipeline.tf_pipeline import COLS

        cols_string = ", ".join(COLS)
        where_clause = f" WHERE verse_uid >= {range_start} AND verse_uid <= {range_end}"
        query = f"SELECT {cols_string} FROM {view_name}{where_clause} {TF_ORDER_BY}"

        with db.get_cursor() as cur:
            cur.execute(query)
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, row)) for row in cur.fetchall()]
