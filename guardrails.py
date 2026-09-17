"""
Safety guardrails for LLM-generated SQL.

The rule: only a single, read-only SELECT statement is allowed to execute.
Anything else (INSERT/UPDATE/DELETE/DROP/ALTER/ATTACH/PRAGMA, multiple
statements, comment-based obfuscation) is rejected before it ever touches
the database.
"""
import re

BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE",
    "TRUNCATE", "ATTACH", "DETACH", "PRAGMA", "VACUUM", "GRANT", "REVOKE",
]


class UnsafeSQLError(Exception):
    pass


def validate_sql(sql: str) -> str:
    """Returns the cleaned SQL if safe, else raises UnsafeSQLError."""
    cleaned = sql.strip().rstrip(";")

    # Strip SQL comments before inspecting, so `SELECT 1; -- DROP TABLE x` can't hide intent
    no_comments = re.sub(r"--.*?$", "", cleaned, flags=re.MULTILINE)
    no_comments = re.sub(r"/\*.*?\*/", "", no_comments, flags=re.DOTALL)

    # Must be exactly one statement
    if ";" in no_comments.strip():
        raise UnsafeSQLError("Multiple SQL statements are not allowed.")

    stripped = no_comments.strip()
    if not re.match(r"^\s*(SELECT|WITH)\b", stripped, flags=re.IGNORECASE):
        raise UnsafeSQLError("Only SELECT (or WITH ... SELECT) statements are allowed.")

    upper = stripped.upper()
    for kw in BLOCKED_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper):
            raise UnsafeSQLError(f"Blocked keyword detected: {kw}")

    return cleaned


if __name__ == "__main__":
    tests = [
        "SELECT * FROM Patients",
        "SELECT * FROM Patients; DROP TABLE Patients;",
        "DELETE FROM Billing",
        "WITH t AS (SELECT * FROM Treatments) SELECT * FROM t",
        "SELECT * FROM Patients -- ; DROP TABLE Patients",
    ]
    for t in tests:
        try:
            print("OK  :", validate_sql(t))
        except UnsafeSQLError as e:
            print("BLOCK:", t, "->", e)
