from typing import List, TYPE_CHECKING, Dict

import db

if TYPE_CHECKING:
    pass


class XMLConversionRepository:

    def from_view(
        self,
        range_start: int,
        range_end: int,
        view_name: str,
    ) -> List[Dict]:
        from tf_pipeline import COLS

        cols_string = ", ".join(COLS)
        where_clause = f" WHERE verse_uid >= {range_start} AND verse_uid <= {range_end}"
        query = f"SELECT {cols_string} FROM {view_name}{where_clause}"

        with db.get_cursor() as cur:
            cur.execute(query)
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, row)) for row in cur.fetchall()]
