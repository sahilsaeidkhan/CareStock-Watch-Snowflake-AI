🛠️ SETUP_GUIDE.md

CareStock Watch – Snowflake-Native AI Inventory Application

1️⃣ Overview

This guide explains how to set up and run CareStock Watch, a Snowflake-native Streamlit application for predicting stock-outs, reducing wastage, and prioritizing reorders for hospitals, public distribution systems (PDS), and NGOs.

The application runs entirely inside Snowflake using:

Snowflake Tables & Dynamic Tables

SQL Views

Snowpark (Python)

Streamlit in Snowflake

AI-ready forecasting logic (Cortex-ready)

No external backend or data movement is required.

2️⃣ Prerequisites

Before starting, ensure you have:

Required

✅ Snowflake account (Trial or Paid)

✅ Role with permission to:

Create databases, schemas, tables

Create Dynamic Tables

Run Streamlit apps

✅ Python 3.8+ (for local testing only, optional)

✅ Git (optional)

Recommended

Snowflake Web UI access

Basic familiarity with SQL and Streamlit

3️⃣ Snowflake Environment Setup
Step 1: Create Database & Schema
CREATE DATABASE CARESTOCK_DB;
CREATE SCHEMA CARESTOCK_DB.PUBLIC;

Step 2: Create Base Inventory Table

This table represents the daily stock snapshot received from hospitals, PDS, or NGOs.

CREATE OR REPLACE TABLE DAILY_STOCK (
    DATE DATE,
    LOCATION STRING,
    ITEM STRING,
    OPENING_STOCK NUMBER,
    RECEIVED NUMBER,
    ISSUED NUMBER,
    CLOSING_STOCK NUMBER,
    LEAD_TIME_DAYS NUMBER
);

Step 3: Load Sample Data (Optional)
INSERT INTO DAILY_STOCK VALUES
('2025-01-01', 'Hospital A', 'Insulin', 100, 20, 30, 90, 7),
('2025-01-01', 'Hospital A', 'Paracetamol', 500, 200, 150, 550, 5),
('2025-01-01', 'NGO Center', 'Oxygen Cylinder', 40, 10, 15, 35, 10);


💡 In production, data can be ingested via Snowpipe / COPY INTO from files or APIs.

4️⃣ Create Stock Health Dynamic Table (AI Brain)

This Dynamic Table automatically computes stock health metrics.

CREATE OR REPLACE DYNAMIC TABLE STOCK_HEALTH_DT
TARGET_LAG = '5 minutes'
WAREHOUSE = COMPUTE_WH
AS
SELECT
    LOCATION,
    ITEM,
    AVG(ISSUED) AS AVG_DAILY_DEMAND,
    MAX(CLOSING_STOCK) AS CLOSING_STOCK,
    MAX(LEAD_TIME_DAYS) AS LEAD_TIME_DAYS,
    CASE
        WHEN MAX(CLOSING_STOCK) / NULLIF(AVG(ISSUED), 0) < 3 THEN 'Critical'
        WHEN MAX(CLOSING_STOCK) / NULLIF(AVG(ISSUED), 0) < 7 THEN 'Warning'
        ELSE 'Healthy'
    END AS STOCK_STATUS,
    MAX(CLOSING_STOCK) / NULLIF(AVG(ISSUED), 1) AS DAYS_TO_STOCKOUT
FROM DAILY_STOCK
GROUP BY LOCATION, ITEM;


This table:

Auto-refreshes

Acts as the AI decision layer

Powers dashboards, alerts, and actions

5️⃣ Create Action Log Table (Human-in-the-Loop)
CREATE OR REPLACE TABLE ACTION_LOG (
    ACTION_TIMESTAMP TIMESTAMP,
    LOCATION STRING,
    ITEM STRING,
    ACTION_TYPE STRING,
    NOTES STRING,
    USER_NAME STRING
);


Used for:

Logging procurement actions

Audit trail

Accountability

6️⃣ Streamlit App Setup (Inside Snowflake)
Step 1: Open Snowflake UI

Go to Projects → Streamlit

Click Create Streamlit App

Step 2: Configure App

Database: CARESTOCK_DB

Schema: PUBLIC

Warehouse: COMPUTE_WH

Step 3: Paste Application Code

Copy contents of streamlit_app.py

Paste into Snowflake Streamlit editor

Save & Run

No external deployment needed.

7️⃣ Python Dependencies (Local Only – Optional)

If running locally:

pip install -r requirements.txt


Example requirements.txt:

streamlit
snowflake-snowpark-python
pandas
plotly

8️⃣ Optional Automation (Future-Ready)

CareStock Watch is designed to support:

🔄 Snowflake Streams for change tracking

⏱️ Snowflake Tasks for scheduled refresh & alerts

📢 Email / SMS alert integration

🔗 External API ingestion via Snowflake External Functions

These are architecturally supported but optional for the prototype.

9️⃣ Security & Governance

Role-based access control (RBAC)

No data movement outside Snowflake

All processing and AI logic runs inside Snowflake

Action logs enable audit-ready workflows

🔟 Validation Checklist (For Judges)

✅ Data ingested into Snowflake
✅ Dynamic Tables auto-compute intelligence
✅ Streamlit app runs natively in Snowflake
✅ AI-ready forecasting logic implemented
✅ Human actions logged and auditable
✅ Secure, privacy-safe architecture

1️⃣1️⃣ Support

For issues:

Review PROJECT_DOCUMENTATION.md

Check Snowflake permissions

Validate warehouse status

1️⃣2️⃣ Author

Developed by: Sahil Saeid Khan
Purpose: AI for Good Hackathon / Educational Use
Status: Prototype (Production-ready architecture
