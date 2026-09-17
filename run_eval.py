"""
Runs the evaluation set against the assistant and reports accuracy.

Accuracy is measured by EXECUTION MATCH, not exact SQL text match: the
generated SQL is considered correct if running it returns the same result
as running the hand-written expected SQL. This is the right standard because
two syntactically different SQL statements (e.g. different JOIN order, or
COUNT(*) vs COUNT(id)) can be equally correct.

Usage:  python run_eval.py
Requires AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT to be set.
"""
import json
import sqlite3

from azure_nl_to_sql import NLToSQLAssistant
from guardrails import validate_sql, UnsafeSQLError

DB_PATH = "hospital.db"


def run_query(db_path, sql):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows


def results_match(a, b):
    # Compare as sets of tuples so row order/column order differences don't
    # falsely fail a correct answer. Round floats to avoid float-precision mismatches.
    def norm(rows):
        out = set()
        for row in rows:
            norm_row = tuple(round(v, 2) if isinstance(v, float) else v for v in row)
            out.add(norm_row)
        return out

    return norm(a) == norm(b)


def main():
    with open("eval_questions.json") as f:
        eval_set = json.load(f)

    assistant = NLToSQLAssistant(db_path=DB_PATH)

    correct = 0
    blocked = 0
    failed = 0
    results_log = []

    for item in eval_set:
        question = item["question"]
        expected_sql = item["expected_sql"]

        try:
            expected_rows = run_query(DB_PATH, expected_sql)
        except sqlite3.Error as e:
            print(f"SKIP (bad expected SQL) - {question}: {e}")
            continue

        generated_sql = assistant.generate_sql(question)

        try:
            safe_sql = validate_sql(generated_sql)
        except UnsafeSQLError as e:
            blocked += 1
            results_log.append({"question": question, "status": "BLOCKED", "sql": generated_sql, "reason": str(e)})
            print(f"BLOCKED - {question}\n  -> {e}")
            continue

        try:
            actual_rows = run_query(DB_PATH, safe_sql)
        except sqlite3.Error as e:
            failed += 1
            results_log.append({"question": question, "status": "EXEC_ERROR", "sql": safe_sql, "reason": str(e)})
            print(f"EXEC ERROR - {question}\n  SQL: {safe_sql}\n  -> {e}")
            continue

        if results_match(expected_rows, actual_rows):
            correct += 1
            results_log.append({"question": question, "status": "CORRECT", "sql": safe_sql})
            print(f"CORRECT - {question}")
        else:
            failed += 1
            results_log.append({
                "question": question, "status": "WRONG", "sql": safe_sql,
                "expected_sql": expected_sql, "expected": expected_rows[:3], "got": actual_rows[:3],
            })
            print(f"WRONG - {question}\n  Generated: {safe_sql}\n  Expected SQL: {expected_sql}")

    total = len(eval_set)
    print("\n" + "=" * 50)
    print(f"ACCURACY: {correct}/{total} = {100*correct/total:.1f}%")
    print(f"Blocked (unsafe SQL caught): {blocked}")
    print(f"Failed (wrong result or execution error): {failed}")

    with open("eval_results.json", "w") as f:
        json.dump(results_log, f, indent=2, default=str)
    print("\nFull results saved to eval_results.json")


if __name__ == "__main__":
    main()
