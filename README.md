# 🤖 AI-Powered Healthcare Operations & Insights Assistant

An AI-assisted healthcare analytics prototype designed to help users interact with structured hospital data using natural-language questions.

The project combines **SQL-based healthcare analytics** with an **AI assistant concept** that can translate business questions into data-driven insights, making healthcare operational data easier to explore for non-technical users.

> **Project Status:** Prototype / In Progress  
> **Note:** AI integration is currently demonstrated as a prototype architecture and is not presented as a production Azure OpenAI deployment.

---

## 📌 Project Overview

Healthcare organizations generate large amounts of operational data related to:

- Patients
- Doctors
- Departments
- Appointments
- Treatments
- Medications
- Billing

Traditional SQL analytics requires users to understand database structures and write SQL queries.

This project explores an **AI-powered natural-language analytics workflow**, where a user can ask questions such as:

> "Which doctors have the highest number of appointments?"

or

> "What is the average treatment cost?"

The assistant is designed to understand the question, identify the relevant data, generate an appropriate SQL query, and return a business-friendly insight.

---

## 🎯 Project Objectives

The main objectives of this project are:

- Enable natural-language interaction with healthcare data
- Simplify SQL-based data analysis
- Generate relevant SQL queries from business questions
- Provide understandable business insights
- Apply SQL safety and validation concepts
- Demonstrate how Generative AI can enhance traditional data analytics
- Create a bridge between **Business Analytics, SQL and AI**

---

## 🏥 Healthcare Database

The project is based on a structured hospital operations database containing the following entities:

| Table | Description |
|---|---|
| Departments | Hospital departments |
| Doctors | Doctors associated with departments |
| Patients | Patient demographic information |
| Medications | Medication information |
| Appointments | Patient-doctor appointments |
| Treatments | Treatments and treatment costs |
| Billing | Billing information |

### Dataset Size

| Entity | Records |
|---|---:|
| Departments | 8 |
| Doctors | 30 |
| Patients | 350 |
| Medications | 100 |
| Appointments | 500 |
| Treatments | 250 |
| Billing | 250 |
| **Total** | **1,488** |

> The dataset is a synthetic portfolio dataset and does not contain real patient information.

---

## 🧠 AI Analytics Workflow

The proposed workflow is:

```text
User
  ↓
Natural Language Question
  ↓
AI Assistant
  ↓
Understand Business Intent
  ↓
Identify Relevant Database Tables
  ↓
Generate SQL Query
  ↓
SQL Validation / Safety Checks
  ↓
Execute Query
  ↓
Analyze Result
  ↓
Business Insight
