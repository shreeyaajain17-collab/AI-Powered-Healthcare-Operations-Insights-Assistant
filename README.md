# AI-Powered Healthcare Operations & Insights Assistant

A natural-language-to-SQL analytics assistant built on top of the Hospital
Operations & Patient Analytics database (7 tables, 1,700+ records), powered
by **Azure OpenAI Service**. Ask a business question in plain English; the
system converts it to SQL, runs it safely against the database, and explains
the result in business language.

## Why Azure OpenAI (not a direct model API)

This was built deliberately on the Microsoft AI stack rather than calling a
model API directly, since the goal is a project that demonstrates the same
tools used in Azure AI-based production systems:
- **Azure OpenAI Service** for the LLM calls (`azure_nl_to_sql.py`)
- **Azure AI Studio** deployment naming/versioning conventions (deployment
  name + API version, not a hardcoded model string)
- A clear, documented upgrade path to **Azure SQL Database** in place of
  SQLite, and to **Azure App Service / Azure Container Apps** for hosting
  (see "Deploying on Azure" below)

## Architecture

```
User question
     |
     v
[schema.py]        --> extracts live table/column/FK info from hospital.db
     |
     v
[azure_nl_to_sql.py] --> Azure OpenAI (GPT-4o deployment) generates SQL
                          grounded in the real schema
     |
     v
[guardrails.py]     --> validates: single statement, SELECT/WITH only,
                         no INSERT/UPDATE/DELETE/DROP/ALTER etc.
     |
     v
SQLite / Azure SQL execution --> real query results
     |
     v
[azure_nl_to_sql.py] --> Azure OpenAI explains the result in plain
                          business language
     |
     v
Answer + SQL + data table shown in Streamlit UI
```

## Setup

1. Create an Azure OpenAI resource in Azure AI Studio and deploy a GPT-4o
   (or GPT-4o-mini) model. Note the deployment name.
2. Install dependencies:

```bash
pip install openai streamlit pandas
```

3. Set environment variables:

```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your_key_here"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"          # your deployment name, not the base model name
export AZURE_OPENAI_API_VERSION="2024-10-21"
```

## Run the app

```bash
streamlit run app.py
```

## Run the evaluation

```bash
python run_eval.py
```

This runs 25 hand-written test questions against the assistant and reports
accuracy by **execution match** — the generated SQL is scored correct if it
returns the same data as a hand-written reference query, not if the SQL text
matches exactly (two different but equally valid queries should both pass).
Results are saved to `eval_results.json` for review.

## Safety

All generated SQL passes through `guardrails.py` before execution:
- Only a single `SELECT`/`WITH ... SELECT` statement is allowed
- Statement-stacking (`SELECT ...; DROP TABLE ...`) is blocked
- Comment-based obfuscation of blocked keywords is stripped and checked
- Any `INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/PRAGMA/ATTACH` etc. is rejected
  before it reaches the database

## Deploying on Azure (path to a full Microsoft-stack project)

If you want to take this further for interviews:
- **Database**: migrate `hospital.db` to **Azure SQL Database**. The only
  code change needed is the connection in `execute_sql()` — swap `sqlite3`
  for `pyodbc`/`pymssql` and point at your Azure SQL connection string.
  `schema.py` would need its `PRAGMA` calls swapped for `INFORMATION_SCHEMA`
  queries, since PRAGMA is SQLite-specific.
- **Hosting**: deploy `app.py` to **Azure App Service** (Python web app) or
  containerize it and run on **Azure Container Apps**.
- **Orchestration (optional, bigger lift)**: replace the direct
  `chat.completions.create` calls in `azure_nl_to_sql.py` with **Semantic
  Kernel** (Microsoft's open-source LLM orchestration framework) — it adds
  plugin-style function calling and planning, which is closer to how
  production Azure AI agents are actually built, and is a stronger signal
  in an interview than raw API calls.

## Files

| File | Purpose |
|---|---|
| `schema.py` | Extracts schema (tables, columns, types, FKs) for the prompt |
| `azure_nl_to_sql.py` | Core pipeline: question -> SQL -> execute -> explain, via Azure OpenAI |
| `guardrails.py` | SQL safety validation |
| `eval_questions.json` | 25-question evaluation set with reference SQL |
| `run_eval.py` | Evaluation harness, reports accuracy % |
| `app.py` | Streamlit front end |
| `hospital.db` | SQLite database (Patients, Doctors, Appointments, Treatments, Billing, Medications, Departments) |

## Resume bullet

> Built a natural-language-to-SQL analytics assistant on a 7-table hospital
> operations database using Azure OpenAI Service (GPT-4o), translating
> business questions into schema-grounded, validated SQL and generating
> plain-language result summaries; implemented guardrails blocking non-read
> SQL operations and evaluated the system on a 25-question test set,
> reporting execution-match accuracy.

Fill in the actual accuracy % after running `run_eval.py` with your Azure
OpenAI credentials — don't put a number on the resume you haven't actually
measured.
