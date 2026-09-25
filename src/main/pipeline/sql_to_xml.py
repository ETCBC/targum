from typing import List, TYPE_CHECKING, Dict

from main.loaders.db import db

if TYPE_CHECKING:
    pass


TF_ORDER_BY = (
    "ORDER BY verse_sort NULLS LAST, verse_uid, word_group_rank, "
    "word_group_reading NULLS FIRST, word_rank NULLS LAST, (word_id)::bigint"
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
        # The ordering keys are deliberately not in COLS: that list is positionally paired with
        # tf_pipeline.TAGS and ATTRS, so adding to it would change the serialised schema. SQL is
        # happy to order by view columns that are not selected.
        query = f"SELECT {cols_string} FROM {view_name}{where_clause} {TF_ORDER_BY}"

        with db.get_cursor() as cur:
            cur.execute(query)
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, row)) for row in cur.fetchall()]
