from typing import List, TYPE_CHECKING, Dict

from main.loaders.db import db

if TYPE_CHECKING:
    pass


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
        query = f"SELECT {cols_string} FROM {view_name}{where_clause}"

        with db.get_cursor() as cur:
            cur.execute(query)
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, row)) for row in cur.fetchall()]
