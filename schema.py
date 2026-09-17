"""
Extracts the database schema (tables, columns, types, foreign keys) and formats
it as a compact text block the LLM can use to ground its SQL generation.
"""
import sqlite3


def get_schema_description(db_path: str = "hospital.db") -> str:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cur.fetchall()]

    lines = []
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = cur.fetchall()  # cid, name, type, notnull, dflt_value, pk
        col_descs = []
        for c in cols:
            col_name, col_type, is_pk = c[1], c[2], c[5]
            marker = " [PK]" if is_pk else ""
            col_descs.append(f"{col_name} {col_type}{marker}")

        cur.execute(f"PRAGMA foreign_key_list({table})")
        fks = cur.fetchall()
        fk_descs = [f"{fk[3]} -> {fk[2]}.{fk[4]}" for fk in fks]

        block = f"TABLE {table} ({', '.join(col_descs)})"
        if fk_descs:
            block += f"\n  Foreign keys: {'; '.join(fk_descs)}"
        lines.append(block)

    conn.close()
    return "\n".join(lines)


if __name__ == "__main__":
    print(get_schema_description())
