
# CareStock Watch — Design & Logic

**Author:** Sahil Saeid Khan  
**Scope:** Design decisions, data model, and core logic (forecasting and risk rules)  
**Last Updated:** 2025-12-28

This document describes the **design and logic** behind CareStock Watch: the data model, Snowflake implementation patterns (dynamic tables, views), forecasting approach, and risk categorization logic.

## 1. Data Model
- Core table: daily stock entries `(date, location, item, opening_stock, received, issued, closing_stock, lead_time_days)`
- Reference tables: `INVENTORY_ITEMS`, `LOCATIONS`, `SUPPLIERS`, `ACTION_LOG`

## 2. Forecasting & Confidence
- Use short-term explainable SQL-based forecasting (moving averages, exponential smoothing) inside Snowflake.
- Compute confidence bounds using historical variance and simple statistical assumptions to produce low/high estimates.

## 3. Risk Rules
- Days-to-stock-out = current_stock / expected_daily_usage
- Classification:
  - Critical: days-to-stock-out ≤ safety_lead_time
  - Warning: days-to-stock-out ≤ safety_lead_time * 2
  - Healthy: otherwise

## 4. Actions & Prioritization
- Generate per-location reorder lists sorted by urgency and impact (patients protected).
- Actions are logged in `ACTION_LOG` with user, timestamp, and notes.

## 5. Snowflake Patterns
- Prefer views for business logic and dynamic tables for near-real-time metrics.
- Keep sensitive logic inside Snowpark procedures where needed.

## 6. Notes & Future Work
- Replace SQL forecasting with Snowflake Cortex models as needed.
- Add expiry-aware forecasting and supplier lead-time variability into risk calculations.


## 5. Technology Stack

### Frontend & Visualization
- Streamlit (inside Snowflake)
- Custom HTML / CSS styling

### Data Platform
- Snowflake
- Dynamic Tables
- SQL Views

### AI & Analytics
- Snowflake Cortex (AI-ready design)
- SQL-based forecasting & stock logic
- Confidence band estimation

### Application Logic
- Python
- Snowpark

### Security & Governance
- Snowflake RBAC
- No external data transfer

---

## 6. Project Structure

# CareStock Watch – AI-Powered Inventory Intelligence System

**Author:** Sahil Saeid Khan  
**Last Updated:** 2025  

---

## 1. Project Overview

CareStock Watch is a **Snowflake-native inventory intelligence system** designed for hospitals, public distribution systems (PDS), and NGOs to **predict stock-outs before they happen**, reduce medicine wastage, and support data-driven procurement decisions.

The system runs **entirely inside Snowflake** using Streamlit-in-Snowflake, SQL-based analytics, and AI-ready forecasting logic, ensuring **security, scalability, and zero data movement**.

---

## 2. Problem Addressed

Healthcare and aid organizations often face:
- Late detection of stock-outs
- Overstocking leading to expiry and waste
- Inventory data spread across spreadsheets
- No predictive visibility into future demand
- Poor coordination between procurement and field teams

CareStock Watch converts simple daily stock data into **early warnings, forecasts, and actionable insights**.

---

## 3. Core Features

### 3.1 Inventory Intelligence
- Single live view of inventory health across all locations
- Days-to-stock-out calculation
- Safety buffer analysis
- RED / YELLOW / GREEN risk classification
- Overstock detection to prevent expiry

### 3.2 AI-Assisted Demand Forecasting
- Short-term demand forecasting (7-day horizon)
- Confidence bounds (low / high estimates)
- Explainable, SQL-based logic
- Cortex-ready architecture for future ML model upgrades

### 3.3 Early Warnings & Prioritization
- Critical and warning item identification
- Life-saving item prioritization
- Reorder priority lists per location and item
- CSV export for procurement and field teams

### 3.4 Analytics & Visualization
- Stock health distribution analytics
- Location-wise risk comparison
- Heatmap of locations vs items
- Trend-based operational insights

### 3.5 Human-in-the-Loop Actions
- Action logging for critical items
- Tracks who took action, when, and why
- Supports accountability and audit trails

### 3.6 Impact Measurement
- Estimated patients protected
- Emergency procurement cost savings
- Reduction in medicine wastage
- System coverage (locations × items)

---

## 4. System Architecture (Logical)

**Data Sources**
- Hospitals
- NGOs / Field Centers
- Public Distribution Systems
- Simple daily stock table:
  `(date, location, item, opening_stock, received, issued, closing_stock, lead_time_days)`

**Snowflake Platform**
- Snowflake Tables – Central inventory repository
- Dynamic Tables – Auto-refresh stock health metrics
- SQL Views – Transparent business logic
- Snowpark (Python) – Secure execution inside Snowflake
- Cortex-ready forecasting logic

**Application Layer**
- Streamlit in Snowflake
- No external backend
- No data movement outside Snowflake

**Security & Governance**
- Role-Based Access Control (RBAC)
- Audit-ready design
- Secure-by-default architecture

---

## 5. Technology Stack

### Frontend & Visualization
- Streamlit (inside Snowflake)
- Custom HTML / CSS styling

### Data Platform
- Snowflake
- Dynamic Tables
- SQL Views

### AI & Analytics
- Snowflake Cortex (AI-ready design)
- SQL-based forecasting & stock logic
- Confidence band estimation

### Application Logic
- Python
- Snowpark

### Security & Governance
- Snowflake RBAC
- No external data transfer

---

## 6. Project Structure
CareStock-Watch/
├── streamlit_app.py
├── requirements.txt
├── .gitignore
├── README.md
├── PROJECT_DOCUMENTATION.md
├── SETUP_GUIDE.md
└── CODE_STRUCTURE.md
## 7. Installation & Setup

### Requirements
- Python ≥ 3.8
- Snowflake account with Streamlit enabled
- Required Python packages (see `requirements.txt`)

### Setup Steps
1. Clone the repository
2. Install dependencies  
   ```bash
   pip install -r requirements.txt
Configure Snowflake connection

Run the app inside Snowflake Streamlit environment

8. Usage Guide
Navigation
Dashboard: Real-time inventory health overview

Analytics: Risk distribution, heatmaps, trends

Actions: Log actions taken on critical items

Impact: Quantified real-world impact

Settings: Alert and notification preferences

Filtering
Filter by location and item

Focus on critical or warning inventory

Export priority lists as CSV

9. Future Enhancements
Automated alert delivery using Snowflake Tasks

EOQ and safety stock optimization

Supplier performance analytics

Expiry-aware forecasting

Multi-warehouse optimization

Role-based dashboards per user type

10. Version History
v1.0

Snowflake-native inventory intelligence

AI-assisted forecasting

Early-warning system

Action logging & impact metrics

11. License
MIT License
(For educational and hackathon purposes)

12. Author
Developed by Sahil Saeid Khan
