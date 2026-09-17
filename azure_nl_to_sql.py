"""
Core engine: natural language question -> SQL -> execution -> plain-English answer.

Built on AZURE OPENAI SERVICE rather than a direct model API, so the stack is
fully Microsoft-native: Azure OpenAI for the LLM, SQLite locally (swap to
Azure SQL Database for a production deployment -- see README), and the whole
thing is deployable to Azure App Service / Azure Container Apps.

Requires these environment variables:
    AZURE_OPENAI_ENDPOINT      e.g. https://your-resource.openai.azure.com/
    AZURE_OPENAI_API_KEY
    AZURE_OPENAI_DEPLOYMENT    the deployment name you gave your GPT-4o model in Azure AI Studio
    AZURE_OPENAI_API_VERSION   e.g. 2024-10-21

Install deps:  pip install openai
"""
import os
import sqlite3
import json

from openai import AzureOpenAI

from schema import get_schema_description
from guardrails import validate_sql, UnsafeSQLError

DB_PATH = "hospital.db"

SQL_SYSTEM_PROMPT = """You are a SQL generator for a hospital operations SQLite database.

Given the schema below and a user's natural language question, output ONLY a single
valid, read-only SQLite SELECT statement that answers the question. No explanation,
no markdown code fences, no comments — just the raw SQL.

Rules:
- Only use tables/columns that exist in the schema.
- Never write INSERT, UPDATE, DELETE, DROP, ALTER, or any statement other than SELECT.
- Only one statement, no trailing semicolon needed.
- Use JOINs where the question spans multiple tables.
- Prefer explicit column names over SELECT *.

SCHEMA:
{schema}
"""

EXPLAIN_SYSTEM_PROMPT = """You are a healthcare operations analyst. Given a user's
question, the SQL query that was run, and the resulting data, write a concise
2-4 sentence plain-English business answer. Reference concrete numbers from the
result. Do not mention SQL or databases in your answer — write as if briefing
a hospital administrator."""


class NLToSQLAssistant:
    def __init__(
        self,
        azure_endpoint: str = None,
        api_key: str = None,
        deployment: str = None,
        api_version: str = None,
        db_path: str = DB_PATH,
    ):
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT"),
            api_key=api_key or os.environ.get("AZURE_OPENAI_API_KEY"),
            api_version=api_version or os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
        self.deployment = deployment or os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        self.db_path = db_path
        self.schema = get_schema_description(db_path)

    def generate_sql(self, question: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.deployment,
            max_tokens=500,
            temperature=0,
            messages=[
                {"role": "system", "content": SQL_SYSTEM_PROMPT.format(schema=self.schema)},
                {"role": "user", "content": question},
            ],
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```sql", "").replace("```", "").strip()
        return raw

    def execute_sql(self, sql: str):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def explain(self, question: str, sql: str, rows: list) -> str:
        payload = f"Question: {question}\nSQL: {sql}\nResult (first 20 rows): {json.dumps(rows[:20], default=str)}"
        resp = self.client.chat.completions.create(
            model=self.deployment,
            max_tokens=400,
            temperature=0.3,
            messages=[
                {"role": "system", "content": EXPLAIN_SYSTEM_PROMPT},
                {"role": "user", "content": payload},
            ],
        )
        return resp.choices[0].message.content.strip()

    def ask(self, question: str) -> dict:
        sql = self.generate_sql(question)
        try:
            safe_sql = validate_sql(sql)
        except UnsafeSQLError as e:
            return {"question": question, "sql": sql, "error": f"Blocked unsafe SQL: {e}", "rows": None, "answer": None}

        try:
            rows = self.execute_sql(safe_sql)
        except sqlite3.Error as e:
            return {"question": question, "sql": safe_sql, "error": f"SQL execution failed: {e}", "rows": None, "answer": None}

        answer = self.explain(question, safe_sql, rows)
        return {"question": question, "sql": safe_sql, "error": None, "rows": rows, "answer": answer}


if __name__ == "__main__":
    assistant = NLToSQLAssistant()
    result = assistant.ask("Which city has the highest number of patients?")
    print(json.dumps(result, indent=2, default=str))
