# CareStock-Watch
# 🏥 CareStock Watch  
**AI-powered Inventory Intelligence for Healthcare & NGOs (Built on Snowflake)**

CareStock Watch is a **Snowflake-native Streamlit application** that helps hospitals, public distribution systems (PDS), and NGOs **predict stock-outs before shelves go empty**, reduce medicine wastage, and prioritize reorders using **AI-driven demand forecasting**.

Built for the **AI for Good Hackathon**, the solution focuses on **real operational problems** faced by frontline healthcare and aid organizations.

---

## 🚨 Problem Statement

Hospitals, public distribution systems, and NGOs struggle to keep essential medicines and supplies available at the **right place and right time**.

Common challenges include:
- Inventory data scattered across spreadsheets and systems
- Stock-outs detected only **after shelves are empty**
- Overstocking leading to **expiry and wastage**
- No predictive visibility into future demand
- Poor coordination between procurement, inventory teams, and field staff

These gaps directly impact **patient safety and service delivery**.

---

## 💡 Solution Overview

CareStock Watch provides a **single, live command center** for inventory health:

- Ingests a **simple daily stock table** (no complex ERP required)
- Computes **stock-health metrics automatically** inside Snowflake
- Uses **AI-assisted demand forecasting** to predict shortages
- Highlights **critical items**, overstock risks, and reorder priorities
- Enables **human-in-the-loop actions** with full audit logging

All data, logic, and UI run **securely inside Snowflake**.

---

## ✨ Key Features

### 📊 Inventory Intelligence
- Single view of stock health across all locations
- RED / YELLOW / GREEN risk classification
- Days-to-stock-out and safety buffer calculations
- Overstock detection to reduce expiry risk

### 🤖 AI-Driven Forecasting
- 7-day demand forecast with confidence bounds
- Explainable predictions (no black-box ML)
- Cortex-ready architecture for future model upgrades

### 🚨 Early Warnings & Actions
- Priority list of critical items
- Downloadable CSV for procurement teams
- Human-in-the-loop action logging (“Who did what, when”)

### 📈 Analytics & Visibility
- Stock health distribution
- Location-wise risk comparison
- Heatmap of locations vs items
- Life-saving items prioritization

### 🌍 Impact Measurement
- Estimated patients protected
- Cost savings from avoided emergency purchases
- Waste reduction due to early overstock detection

---

## 🧱 Architecture (High Level)

- **Data Sources:** Hospitals, NGOs, PDS daily stock records  
- **Snowflake Tables:** Central inventory repository  
- **Dynamic Tables & SQL Views:** Stock health computation  
- **Snowflake Cortex (AI-ready):** Demand forecasting logic  
- **Snowpark (Python):** Secure execution inside Snowflake  
- **Streamlit in Snowflake:** Interactive dashboards & actions  
- **Security:** Role-based access, no data movement outside Snowflake  

*(Refer to architecture diagram in the submission deck)*

---

## 🛠 Tech Stack

**Frontend**
- Streamlit (inside Snowflake)
- Custom HTML/CSS styling

**Data Platform**
- Snowflake
- Dynamic Tables
- SQL Views

**AI & Analytics**
- Snowflake Cortex (AI-ready design)
- SQL-based forecasting & risk logic
- Confidence bands for predictions

**Application Logic**
- Python
- Snowpark

**Security & Governance**
- Snowflake RBAC
- Audit-ready, secure by design

---

🚀 Quick Start (Prototype)

1. Clone the repository
2. Install dependencies:
   pip install -r Docs/requirements.txt
3. Configure Snowflake credentials (see Docs/SETUP_GUIDE.md)
4. Run the Streamlit app inside Snowflake

**Note:** This is a prototype. Demo screenshots and sample outputs are provided for evaluation.

---

## 👥 Intended Users

- Hospital procurement teams  
- Hospital inventory staff  
- NGO field teams  
- Operations managers  
- Data engineers & compliance teams  

---

## 🌱 Future Enhancements

- Automated alert delivery via Snowflake Tasks (Email / SMS)
- EOQ & safety stock optimization
- Supplier performance analytics
- Expiry date–aware forecasting
- Multi-warehouse and inter-location transfers
- Role-based dashboards per user group

---

## 🏆 Hackathon Context

This project was built as part of the **AI for Good Hackathon**, focusing on:
- Practical, real-world impact
- Transparent and explainable AI
- Secure, scalable Snowflake-native architecture

---

## 📎 Repository Structure

/Docs
 ├── PROJECT_DOCUMENTATION.md – Detailed design & logic
 ├── SETUP_GUIDE.md – Environment & execution steps
 ├── CODE_STRUCTURE.md – Code organization & flow
 └── requirements.txt – Python dependencies

Files under `/Docs` contain project documentation and the Python dependency list — use them to understand design, setup, and code layout.

---

## 📄 License

This project is created for **educational and hackathon purposes**.

