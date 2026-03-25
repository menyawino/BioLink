from sqlalchemy import text


def aligned_union_sql(db, table_names: list[str], alias: str = "registry") -> str:
    rows = db.execute(
        text(
            """
            SELECT table_name, column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = ANY(:table_names)
            ORDER BY ordinal_position
            """
        ),
        {"table_names": table_names},
    ).fetchall()

    columns_by_table: dict[str, dict[str, tuple[str, str]]] = {table_name: {} for table_name in table_names}
    ordered_columns: list[str] = []
    cast_types: dict[str, str] = {}

    for table_name, column_name, data_type, udt_name in rows:
        if column_name not in ordered_columns:
            ordered_columns.append(column_name)
        columns_by_table.setdefault(table_name, {})[column_name] = (data_type, udt_name)
        cast_types.setdefault(column_name, _sql_cast_type(data_type, udt_name))

    selects = []
    for table_name in table_names:
        parts = []
        table_columns = columns_by_table.get(table_name, {})
        for column_name in ordered_columns:
            quoted_column = _quote_identifier(column_name)
            if column_name in table_columns:
                parts.append(f"{quoted_column} AS {quoted_column}")
            else:
                parts.append(f"NULL::{cast_types[column_name]} AS {quoted_column}")
        selects.append(f"SELECT {', '.join(parts)} FROM {_quote_identifier(table_name)}")

    return f"({' UNION ALL '.join(selects)}) {_quote_identifier(alias)}"


def _sql_cast_type(data_type: str, udt_name: str) -> str:
    if data_type == "ARRAY":
        return f"{udt_name}[]"
    if data_type == "USER-DEFINED":
        return udt_name
    return data_type


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'