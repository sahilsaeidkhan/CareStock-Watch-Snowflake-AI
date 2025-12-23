# CareStock Watch - Hospital Inventory Management
# With Smart Alert System

import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
import numpy as np
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="CareStock Watch",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get Snowflake session
session = get_active_session()

# Sidebar navigation
st.sidebar.title("Hospital Inventory Management")
page = st.sidebar.radio("Navigate", ["Dashboard", "Inventory", "Smart Alerts", "Settings"])

if page == "Dashboard":
    st.title("Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Items", "245", "+12")
    with col2:
        st.metric("Low Stock Items", "8", "-2")
    with col3:
        st.metric("Expiring Soon", "3", "+1")

elif page == "Inventory":
    st.title("Inventory Management")
    st.info("Inventory management features coming soon...")

elif page == "Smart Alerts":
    st.title("Smart Alert System")
    
    # Global threshold settings
    st.subheader("Configure Smart Alert Thresholds")
    col1, col2 = st.columns(2)
    with col1:
        global_low_pct = st.slider("Default low stock threshold (%)", 5, 50, 20)
    with col2:
        global_over_pct = st.slider("Default overstock threshold (% above max)", 0, 200, 50)
    
    # Sample data for demonstration
    sample_data = pd.DataFrame({
        "ITEM": ["Insulin", "Bandages", "Syringes", "Oxygen", "Saline"],
        "CATEGORY": ["Medication", "Supplies", "Supplies", "Equipment", "Medication"],
        "CURRENT_STOCK": [150, 500, 1200, 45, 200],
        "REORDER_POINT": [100, 300, 800, 50, 150],
        "MAX_STOCK": [300, 1000, 2000, 100, 400],
        "EXPIRY_DATE": ["2025-06-15", "2026-12-31", "2026-03-30", "2025-08-20", "2025-09-10"]
    })
    
    st.subheader("Smart Alert Rules per Item")
    
    # Editable rules table
    rules_df = sample_data[["ITEM"]].copy()
    rules_df["Low_Stock_%"] = global_low_pct
    rules_df["Overstock_%"] = global_over_pct
    rules_df["Perishable_Days"] = 30
    
    edited_rules = st.data_editor(
        rules_df,
        num_rows="dynamic",
        use_container_width=True,
        key="smart_rules_editor"
    )
    
    # Create item_rules dictionary
    item_rules = {}
    if edited_rules is not None:
        for _, row in edited_rules.iterrows():
            item_rules[row["ITEM"]] = {
                "low_pct": row["Low_Stock_%"],
                "over_pct": row["Overstock_%"],
                "perishable_days": row["Perishable_Days"],
            }
    
    # Smart alerts function
    def get_smart_alerts(df):
        alerts = []
        today = datetime.today().date()

        for _, row in df.iterrows():
            item = row["ITEM"]
            current = row["CURRENT_STOCK"]
            reorder_point = row.get("REORDER_POINT", 0)
            max_stock = row.get("MAX_STOCK", np.nan)
            expiry = row.get("EXPIRY_DATE", None)

            rules = item_rules.get(item, {
                "low_pct": global_low_pct,
                "over_pct": global_over_pct,
                "perishable_days": 30,
            })

            # 1) Low stock percentage threshold
            if reorder_point and reorder_point > 0:
                pct_of_reorder = (current / reorder_point) * 100
                if pct_of_reorder <= rules["low_pct"]:
                    alerts.append({
                        "Item": item,
                        "Type": "Low stock",
                        "Message": f"{item} at {pct_of_reorder:.1f}% of reorder level",
                        "Severity": "Critical" if pct_of_reorder <= rules["low_pct"] / 2 else "Warning",
                        "Created_At": today,
                    })

            # 2) Overstock warnings
            if not np.isnan(max_stock) and max_stock > 0:
                if current > max_stock * (1 + rules["over_pct"] / 100):
                    alerts.append({
                        "Item": item,
                        "Type": "Overstock",
                        "Message": f"{item} exceeds max by {rules['over_pct']}%",
                        "Severity": "Info",
                        "Created_At": today,
                    })

            # 3) Expiry alerts for perishables
            if expiry and not pd.isna(expiry):
                expiry_date = pd.to_datetime(expiry).date()
                days_left = (expiry_date - today).days
                if days_left <= rules["perishable_days"]:
                    alerts.append({
                        "Item": item,
                        "Type": "Expiry",
                        "Message": f"{item} expires in {days_left} days",
                        "Severity": "Warning" if days_left > 0 else "Critical",
                        "Created_At": today,
                    })

        return pd.DataFrame(alerts) if alerts else pd.DataFrame(
            columns=["Item", "Type", "Message", "Severity", "Created_At"]
        )
    
    # Generate alerts
    smart_alerts_df = get_smart_alerts(sample_data)
    
    # Display alerts summary
    st.subheader("Current Alerts Summary")
    if not smart_alerts_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            critical_count = len(smart_alerts_df[smart_alerts_df["Severity"] == "Critical"])
            st.metric("Critical Alerts", critical_count)
        with col2:
            warning_count = len(smart_alerts_df[smart_alerts_df["Severity"] == "Warning"])
            st.metric("Warnings", warning_count)
        with col3:
            info_count = len(smart_alerts_df[smart_alerts_df["Severity"] == "Info"])
            st.metric("Info", info_count)
    
    # Alert history with filtering
    st.subheader("Alert History & Filtering")
    
    if not smart_alerts_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            severity_filter = st.multiselect(
                "Filter by Severity",
                options=sorted(smart_alerts_df["Severity"].unique()),
                default=list(smart_alerts_df["Severity"].unique()),
            )
        
        with col2:
            type_filter = st.multiselect(
                "Filter by Alert Type",
                options=sorted(smart_alerts_df["Type"].unique()),
                default=list(smart_alerts_df["Type"].unique()),
            )
        
        # Apply filters
        filt = (
            smart_alerts_df["Severity"].isin(severity_filter)
            & smart_alerts_df["Type"].isin(type_filter)
        )
        
        st.dataframe(
            smart_alerts_df[filt].sort_values("Created_At", ascending=False),
            use_container_width=True,
        )
    else:
        st.info("No alerts generated. Adjust thresholds or stock levels to see alerts.")

elif page == "Settings":
    st.title("Settings")
    st.subheader("Notification Settings")
    email_alerts = st.checkbox("Enable email alerts", value=True)
    sms_alerts = st.checkbox("Enable SMS alerts", value=False)
    if st.button("Save Settings"):
        st.success("Settings saved successfully!")

st.sidebar.divider()
st.sidebar.info("CareStock Watch v1.0 - Hospital Inventory Management powered by Snowflake")
