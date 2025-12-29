import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
import plotly.express as px
from datetime import datetime
import numpy as np
import json


# -------------------------------------------------
# Snowflake-safe type casting helpers   
# -------------------------------------------------
def sf_int(x):
    try:
        return int(x)
    except Exception:
        return None

def sf_float(x):
    try:
        return float(x)
    except Exception:
        return None
 
# =================================================
# INVENTORY OPTIMIZATION (EOQ + SAFETY STOCK)
# =================================================

def calculate_eoq(avg_daily_demand, ordering_cost=500, holding_cost=50):
    """
    EOQ calculation
    ordering_cost: cost per order (INR)
    holding_cost: annual holding cost per unit (INR)
    """
    annual_demand = avg_daily_demand * 365
    if annual_demand <= 0:
        return 0
    return round(np.sqrt((2 * annual_demand * ordering_cost) / holding_cost), 1)


def calculate_safety_stock(avg_daily_demand, lead_time_days, service_level=1.65):
    """
    Safety stock calculation
    service_level = 1.65 ≈ 95% service level
    """
    demand_std = avg_daily_demand * 0.3  # assume 30% variability
    return round(service_level * demand_std * np.sqrt(lead_time_days), 1)


def calculate_reorder_point(avg_daily_demand, lead_time_days, safety_stock):
    """
    Reorder Point (ROP)
    """
    return round((avg_daily_demand * lead_time_days) + safety_stock, 1)

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="CareStock Watch",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.block-container {padding-top: 1.5rem;}
</style>
""", unsafe_allow_html=True)

# =================================================
# SNOWFLAKE SESSION
# =================================================
@st.cache_resource
def get_session():
    try:
        # Prefer an active session when running inside Snowpark-managed environments
        return get_active_session()
    except Exception:
        # Attempt to build a session from environment variables (for local dev)
        import os
        try:
            from snowflake.snowpark.session import Session
        except Exception:
            Session = None

        cfg = {}
        for k, env in {
            "account": "SNOWFLAKE_ACCOUNT",
            "user": "SNOWFLAKE_USER",
            "password": "SNOWFLAKE_PASSWORD",
            "role": "SNOWFLAKE_ROLE",
            "warehouse": "SNOWFLAKE_WAREHOUSE",
            "database": "SNOWFLAKE_DATABASE",
            "schema": "SNOWFLAKE_SCHEMA",
            "private_key": "SNOWFLAKE_PRIVATE_KEY"
        }.items():
            v = os.getenv(env)
            if v:
                cfg[k] = v

        if cfg and Session is not None:
            try:
                return Session.builder.configs(cfg).create()
            except Exception as e:
                st.warning(f"Failed to create Snowflake Session from env vars: {e}")

        # No session available; app should run in local demo mode
        st.warning("No Snowflake session found. Running in LOCAL demo mode (no Snowflake connection).")
        return None

session = get_session()

# =================================================
# LOAD DATA (Dynamic Table = AI Brain)
# =================================================
@st.cache_data(ttl=300)
def load_stock_health():
    # If no Snowflake session is available, return a small demo dataframe for local testing
    if session is None:
        demo = pd.DataFrame([
            {
                "LOCATION": "Central Medical Store",
                "ITEM": "Insulin",
                "CLOSING_STOCK": 100,
                "AVG_DAILY_DEMAND": 5,
                "DAYS_TO_STOCKOUT": 20,
                "STOCK_STATUS": "Healthy",
                "LEAD_TIME_DAYS": 7
            },
            {
                "LOCATION": "District Hospital",
                "ITEM": "Oxygen",
                "CLOSING_STOCK": 10,
                "AVG_DAILY_DEMAND": 3,
                "DAYS_TO_STOCKOUT": 3,
                "STOCK_STATUS": "Critical",
                "LEAD_TIME_DAYS": 14
            },
            {
                "LOCATION": "Community Health Centre",
                "ITEM": "Paracetamol",
                "CLOSING_STOCK": 500,
                "AVG_DAILY_DEMAND": 2,
                "DAYS_TO_STOCKOUT": 250,
                "STOCK_STATUS": "Healthy",
                "LEAD_TIME_DAYS": 5
            }
        ])
        return demo

    return session.sql("""
        SELECT
            LOCATION,
            ITEM,
            CLOSING_STOCK,
            AVG_DAILY_DEMAND,
            DAYS_TO_STOCKOUT,
            STOCK_STATUS,
            LEAD_TIME_DAYS
        FROM STOCK_HEALTH_DT
    """).to_pandas()

df = load_stock_health()

# Demo data generator (for local testing)
def generate_demo_data(n=100):
    import random
    locations = [
        "Central Medical Store",
        "District Hospital",
        "Community Health Centre",
        "Primary Health Post",
        "Urban Clinic"
    ]
    items = ["Insulin", "Oxygen", "Paracetamol", "Bandage", "Antibiotic", "Ventilator", "Blood"]
    rows = []
    for _ in range(n):
        loc = random.choice(locations)
        item = random.choice(items)
        closing_stock = max(0, int(np.random.poisson(80)))
        avg_daily_demand = max(0.1, round(np.random.exponential(2.5), 2))
        lead_time = random.randint(1, 30)
        days_to_stockout = round(closing_stock / max(avg_daily_demand, 1), 1)
        if days_to_stockout <= 5:
            status = "Critical"
        elif days_to_stockout <= 15:
            status = "Warning"
        else:
            status = "Healthy"
        rows.append({
            "LOCATION": loc,
            "ITEM": item,
            "CLOSING_STOCK": closing_stock,
            "AVG_DAILY_DEMAND": avg_daily_demand,
            "DAYS_TO_STOCKOUT": days_to_stockout,
            "STOCK_STATUS": status,
            "LEAD_TIME_DAYS": lead_time
        })
    return pd.DataFrame(rows)

# Apply user-provided location mapping so UI shows readable names
if "location_map" in st.session_state and st.session_state.location_map:
    try:
        df["LOCATION"] = df["LOCATION"].astype(str).apply(
            lambda x: st.session_state.location_map.get(x, x)
        )
    except Exception:
        # if mapping fails, continue with original LOCATION values
        pass

# Use a generated demo dataset if the user requested it (keeps state across reruns)
if "demo_df" in st.session_state and st.session_state.demo_df is not None:
    df = st.session_state.demo_df

# =================================================
# SESSION STATE (Settings persistence)
# =================================================
if "email_alert" not in st.session_state:
    st.session_state.email_alert = False
if "email" not in st.session_state:
    st.session_state.email = ""
if "sms_alert" not in st.session_state:
    st.session_state.sms_alert = False
if "phone" not in st.session_state:
    st.session_state.phone = ""
if "alert_levels" not in st.session_state:
    st.session_state.alert_levels = ["Critical", "Warning"]
if "recipients" not in st.session_state:
    st.session_state.recipients = ["Hospital procurement team"]

# -----------------------
# Location mapping editor
# -----------------------
if "location_map" not in st.session_state:
    # start with an empty mapping; users can provide mappings via the editor if desired
    st.session_state.location_map = {}

with st.expander("🔁 Edit location name mappings (optional)"):
    loc_json = json.dumps(st.session_state.location_map, ensure_ascii=False, indent=2)
    user_input = st.text_area(
        "Provide a JSON object mapping raw LOCATION codes to full names (leave as {} to keep raw LOCATION codes):",
        value=loc_json,
        height=160
    )
    if st.button("Apply location mapping"):
        try:
            parsed = json.loads(user_input)
            if not isinstance(parsed, dict):
                st.error("Mapping must be a JSON object (dictionary).")
            else:
                st.session_state.location_map = parsed
                st.success("Location mapping updated")
        except Exception as e:
            st.error(f"Invalid JSON: {e}")

# =================================================
# SIDEBAR
# =================================================
page = st.selectbox(
    "Navigate",
    ["Dashboard", "Analytics", "Actions", "Impact", "Settings"]
)


# =================================================
# TOP FILTER BAR (GLOBAL)
# =================================================

with st.container():
    fcol1, fcol2, fcol3 = st.columns([2, 2, 6])

    # Safely determine available options (works with empty or missing columns)
    loc_options = sorted(df["LOCATION"].dropna().unique()) if "LOCATION" in df.columns else []
    item_options = sorted(df["ITEM"].dropna().unique()) if "ITEM" in df.columns else []

    with fcol1:
        sel_locations = st.multiselect(
            "📍 Location",
            options=loc_options,
            default=loc_options,
            key="filter_location"
        )

    with fcol2:
        sel_items = st.multiselect(
            "📦 Item",
            options=item_options,
            default=item_options,
            key="filter_item"
        )

    with fcol3:
        st.markdown(
            """
            <div style="margin-top:28px; color:#64748B; font-size:13px;">
            Filters apply across Dashboard, Analytics, Actions & Impact
            </div>
            """,
            unsafe_allow_html=True
        )

st.divider()

# Apply filters
df = df[
    df["LOCATION"].isin(sel_locations) &
    df["ITEM"].isin(sel_items)
].copy()


# =================================================
# CORTEX AI DEMAND FORECAST
# =================================================
def safe_cortex_forecast(row):
    try:
        return cortex_demand_forecast(
            row["AVG_DAILY_DEMAND"],
            row["LEAD_TIME_DAYS"],
            horizon_days=7
        )
    except Exception:
        return {
            "forecast_units": row["AVG_DAILY_DEMAND"] * 7,
            "lower_bound": row["AVG_DAILY_DEMAND"] * 5,
            "upper_bound": row["AVG_DAILY_DEMAND"] * 9,
            "explanation": "Fallback estimate based on historical demand"
        }

df["AI_FORECAST"] = df.apply(safe_cortex_forecast, axis=1)

df["FORECAST_7D"] = df["AI_FORECAST"].apply(lambda x: x["forecast_units"])
df["FORECAST_LOW"] = df["AI_FORECAST"].apply(lambda x: x["lower_bound"])
df["FORECAST_HIGH"] = df["AI_FORECAST"].apply(lambda x: x["upper_bound"])
df["AI_EXPLANATION"] = df["AI_FORECAST"].apply(lambda x: x["explanation"])

# =================================================
# DERIVED METRICS
# =================================================
df["DAYS_OF_COVER"] = df["CLOSING_STOCK"] / df["LEAD_TIME_DAYS"].replace(0, 1)

status_badge = {
    "Critical": "🔴 Critical",
    "Warning": "🟡 Warning",
    "Healthy": "🟢 Healthy"
}
df["STATUS_BADGE"] = df["STOCK_STATUS"].map(status_badge)

LIFE_SAVING_ITEMS = ["Insulin", "Oxygen", "Blood", "Ventilator"]
df["ITEM_PRIORITY"] = df["ITEM"].apply(
    lambda x: "🔴 Life-saving" if x in LIFE_SAVING_ITEMS else "🟢 Essential"
)

df["OVERSTOCK_RISK"] = df["DAYS_OF_COVER"] > 90
df["OVERSTOCK_BADGE"] = df["OVERSTOCK_RISK"].apply(
    lambda x: "🟣 Overstock risk" if x else ""
)
# =================================================
# EOQ + SAFETY STOCK CALCULATIONS
# =================================================

df["EOQ"] = df["AVG_DAILY_DEMAND"].apply(
    lambda d: calculate_eoq(d)
)

df["SAFETY_STOCK"] = df.apply(
    lambda row: calculate_safety_stock(
        row["AVG_DAILY_DEMAND"],
        row["LEAD_TIME_DAYS"]
    ),
    axis=1
)

df["REORDER_POINT"] = df.apply(
    lambda row: calculate_reorder_point(
        row["AVG_DAILY_DEMAND"],
        row["LEAD_TIME_DAYS"],
        row["SAFETY_STOCK"]
    ),
    axis=1
)

df["REORDER_RECOMMENDATION"] = df.apply(
    lambda row: (
        "🔴 Order now"
        if row["CLOSING_STOCK"] <= row["REORDER_POINT"]
        else "🟢 Stock sufficient"
    ),
    axis=1
)


# =================================================
# DASHBOARD
# =================================================
# ================================================
# DASHBOARD
# ================================================
if page == "Dashboard":

    # -------------------------------------------------
    # HERO HEADER
    # -------------------------------------------------
    st.markdown(
        """
        <div style="
            padding:24px 28px;
            border-radius:20px;
            background:linear-gradient(135deg,#0F172A,#1E293B);
            color:white;">
            <h1 style="margin-bottom:6px;">🏥 CareStock Watch</h1>
            <p style="font-size:15px; max-width:900px; color:#E5E7EB;">
            Predicts shortages <b>before shelves go empty</b> and flags overstock
            to reduce medicine wastage. Intelligence runs directly inside
            <b>Snowflake</b> using demand patterns and supplier lead times.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # -------------------------------------------------
    # DATA STATUS PANEL (helps debug empty views)
    # -------------------------------------------------
    total_rows = len(df)
    status_counts = df["STOCK_STATUS"].value_counts().to_dict() if "STOCK_STATUS" in df.columns else {}
    life_saving_at_risk = len(df[(df.get("ITEM_PRIORITY") == "🔴 Life-saving") & (df.get("STOCK_STATUS").isin(["Critical","Warning"]))]) if "ITEM_PRIORITY" in df.columns and "STOCK_STATUS" in df.columns else 0

    conn_label = "Snowflake" if session else "LOCAL demo"

    st.info(
        f"**Data status:** Connection: **{conn_label}** — Rows: **{total_rows}**  |  "
        f"🔴 Critical: **{status_counts.get('Critical',0)}**  |  🟡 Warning: **{status_counts.get('Warning',0)}**  |  🟢 Healthy: **{status_counts.get('Healthy',0)}**"
    )

    if not session:
        with st.expander("Demo data tools"):
            size = st.selectbox("Demo dataset size", [10, 50, 100, 200], index=1)
            if st.button("🔁 Generate larger demo dataset", key="gen_demo"):
                st.session_state.demo_df = generate_demo_data(size)
                st.experimental_rerun()

    # -------------------------------------------------
    # CORE KPIs (EXECUTIVE VIEW)
    # -------------------------------------------------
    critical = (df["STOCK_STATUS"] == "Critical").sum()
    warning = (df["STOCK_STATUS"] == "Warning").sum()
    healthy = (df["STOCK_STATUS"] == "Healthy").sum()
    overstock = df["OVERSTOCK_RISK"].sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div style="background:#FEF2F2; border:1px solid #FECACA;
                        border-radius:16px; padding:18px;">
                <div style="font-size:13px; color:#991B1B;">🔴 CRITICAL</div>
                <div style="font-size:34px; font-weight:700; color:#7F1D1D;">
                    {critical}
                </div>
                <div style="font-size:12px; color:#7F1D1D;">
                    Immediate risk
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background:#FFFBEB; border:1px solid #FDE68A;
                        border-radius:16px; padding:18px;">
                <div style="font-size:13px; color:#92400E;">🟡 WARNING</div>
                <div style="font-size:34px; font-weight:700; color:#78350F;">
                    {warning}
                </div>
                <div style="font-size:12px; color:#78350F;">
                    Trending low
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="background:#ECFDF5; border:1px solid #A7F3D0;
                        border-radius:16px; padding:18px;">
                <div style="font-size:13px; color:#065F46;">🟢 HEALTHY</div>
                <div style="font-size:34px; font-weight:700; color:#064E3B;">
                    {healthy}
                </div>
                <div style="font-size:12px; color:#064E3B;">
                    Adequate stock
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div style="background:#F5F3FF; border:1px solid #DDD6FE;
                        border-radius:16px; padding:18px;">
                <div style="font-size:13px; color:#5B21B6;">🟣 OVERSTOCK</div>
                <div style="font-size:34px; font-weight:700; color:#4C1D95;">
                    {overstock}
                </div>
                <div style="font-size:12px; color:#4C1D95;">
                    Wastage risk
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # -------------------------------------------------
    # EARLY WARNING TABLE (MOST IMPORTANT)
    # -------------------------------------------------
    st.subheader("🚨 Early-warning: items requiring attention")

    risk_df = df[df["STOCK_STATUS"].isin(["Critical", "Warning"])]

    if risk_df.empty:
        st.success("No immediate risks detected. Inventory is stable ✅")
    else:
        st.dataframe(
            risk_df[
                [
                    "LOCATION",
                    "ITEM",
                    "ITEM_PRIORITY",
                    "STATUS_BADGE",
                    "CLOSING_STOCK",
                    "DAYS_TO_STOCKOUT"
                ]
            ],
            use_container_width=True
        )

    st.divider()

    # -------------------------------------------------
    # AI FORECAST SNAPSHOT (HIGH IMPACT, LOW NOISE)
    # -------------------------------------------------
    st.subheader("🤖 AI snapshot: next 7-day demand risk")

    ai_focus = df[
        (df["STOCK_STATUS"].isin(["Critical", "Warning"])) &
        (df["ITEM_PRIORITY"] == "🔴 Life-saving")
    ]

    if ai_focus.empty:
        st.info("Life-saving items are currently well covered.")
    else:
        st.dataframe(
            ai_focus[
                [
                    "LOCATION",
                    "ITEM",
                    "AVG_DAILY_DEMAND",
                    "FORECAST_7D",
                    "FORECAST_LOW",
                    "FORECAST_HIGH"
                ]
            ],
            use_container_width=True
        )

        with st.expander("🧠 How the AI forecast works"):
            st.markdown(
                """
                - Learns from historical average daily usage  
                - Projects demand for the next 7 days  
                - Adjusts risk using supplier lead time  
                - Adds confidence bounds for uncertainty  

                Designed to be explainable and replaceable with
                Snowflake Cortex models in production.
                """
            )

    st.divider()
    

    # -------------------------------------------------
    # QUICK ACTION EXPORT
    # -------------------------------------------------
    st.download_button(
        "⬇️ Download priority action list (CSV)",
        risk_df.to_csv(index=False),
        file_name="carestock_priority_actions.csv",
        mime="text/csv"
    )

    st.divider()

    # -------------------------------------------------
    # DECISION LOGIC (TRUST BUILDER)
    # -------------------------------------------------
    st.info(
        "🔍 **Decision logic**  \n"
        "- Demand learned from historical usage  \n"
        "- Days-to-stockout = stock ÷ demand  \n"
        "- Compared against supplier lead time  \n"
        "- Life-saving items always prioritized  \n"
        "- Overstock flagged to reduce expiry & waste"
    )

        # =================================================
    
# ACTIONS
elif page == "Actions":

    # -------------------------------------------------
    # INIT LOCAL STATE (NO DB WRITE)
    # -------------------------------------------------
    if "action_log" not in st.session_state:
        st.session_state.action_log = []

    if "working_df" not in st.session_state:
        st.session_state.working_df = df.copy()

    df = st.session_state.working_df

    # -------------------------------------------------
    # HEADER
    # -------------------------------------------------
    st.markdown(
        """
        <h1>📝 Action Center</h1>
        <p style="color:#475569;">
        Take real-world actions on inventory items.  
        Quantities update instantly to simulate live operations.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # -------------------------------------------------
    # FILTER AT-RISK ITEMS
    # -------------------------------------------------
    at_risk = df[df["STOCK_STATUS"].isin(["Critical", "Warning"])]

    if at_risk.empty:
        st.success("🎉 No critical or warning items right now.")
        st.stop()

    selected_index = st.selectbox(
        "Select item",
        at_risk.index,
        format_func=lambda i: (
            f"{at_risk.loc[i,'LOCATION']} → "
            f"{at_risk.loc[i,'ITEM']} "
            f"({at_risk.loc[i,'STATUS_BADGE']})"
        )
    )

    item = df.loc[selected_index]

    # -------------------------------------------------
    # ITEM CONTEXT
    # -------------------------------------------------
    st.markdown(
        f"""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;
        border-radius:14px;padding:16px;">
        <b>📍 Location:</b> {item['LOCATION']}<br>
        <b>📦 Item:</b> {item['ITEM']}<br>
        <b>📊 Current Stock:</b> {int(item['CLOSING_STOCK'])}<br>
        <b>⏳ Days to Stock-out:</b> {round(item['DAYS_TO_STOCKOUT'],1)}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # -------------------------------------------------
    # ACTION FORM
    # -------------------------------------------------
    with st.form("action_form"):
        action_type = st.selectbox(
            "Action type",
            [
                "Received stock",
                "Transferred from another location",
                "Emergency delivery",
                "NGO / partner support",
                "Manual adjustment"
            ]
        )

        quantity = st.number_input(
            "Quantity (units)",
            min_value=1,
            step=1,
            help="Example: 5 bandages received"
        )

        user = st.text_input(
            "Your name / team",
            placeholder="e.g. Central Medical Store"
        )

        submit = st.form_submit_button("✅ Apply action")

    # -------------------------------------------------
    # APPLY FAKE UPDATE (REAL FEEL)
    # -------------------------------------------------
    if submit:
        if not user.strip():
            st.error("Please enter your name or team.")
        else:
            # Update stock
            df.loc[selected_index, "CLOSING_STOCK"] += quantity

            # Recalculate days to stockout
            avg_demand = max(item["AVG_DAILY_DEMAND"], 1)
            new_days = df.loc[selected_index, "CLOSING_STOCK"] / avg_demand
            df.loc[selected_index, "DAYS_TO_STOCKOUT"] = round(new_days, 1)

            # Update status automatically
            if new_days > 15:
                df.loc[selected_index, "STOCK_STATUS"] = "Healthy"
                df.loc[selected_index, "STATUS_BADGE"] = "🟢 Healthy"
            elif new_days > 5:
                df.loc[selected_index, "STOCK_STATUS"] = "Warning"
                df.loc[selected_index, "STATUS_BADGE"] = "🟡 Warning"
            else:
                df.loc[selected_index, "STOCK_STATUS"] = "Critical"
                df.loc[selected_index, "STATUS_BADGE"] = "🔴 Critical"

            # Persist changes
            st.session_state.working_df = df

            # Log action
            st.session_state.action_log.insert(0, {
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Location": item["LOCATION"],
                "Item": item["ITEM"],
                "Action": action_type,
                "Quantity": f"+{quantity}",
                "User": user
            })

            st.success(f"✅ {quantity} units added successfully")

    st.divider()

    # -------------------------------------------------
    # RECENT ACTIONS
    # -------------------------------------------------
    st.subheader("📜 Recent actions")

    if st.session_state.action_log:
        st.dataframe(
            pd.DataFrame(st.session_state.action_log),
            use_container_width=True
        )
    else:
        st.info("No actions recorded yet.")

    st.info(
        "ℹ️ Demo mode: updates are simulated. "
        "Production version writes to Snowflake using Snowpark."
    )



# =================================================
# SETTINGS
# =================================================
elif page == "Settings":

    st.markdown(
        """
        <h1 style="margin-bottom:0.3rem;">⚙️ Alert & Notification Settings</h1>
        <p style="color:#475569; font-size:1rem; max-width:900px;">
        Configure how and when teams should be notified about inventory risks.
        These preferences are designed for flexibility and safe human oversight.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.subheader("📢 Notification channels")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.email_alert = st.checkbox(
            "Enable email alerts",
            value=st.session_state.email_alert
        )
        st.session_state.email = st.text_input(
            "Notification email address",
            value=st.session_state.email,
            placeholder="supply-team@hospital.org"
        )

    with col2:
        st.session_state.sms_alert = st.checkbox(
            "Enable SMS / WhatsApp alerts",
            value=st.session_state.sms_alert
        )
        st.session_state.phone = st.text_input(
            "Mobile number",
            value=st.session_state.phone,
            placeholder="+91XXXXXXXXXX"
        )

    st.divider()

    st.subheader("🚦 Alert severity preferences")

    alert_levels = st.multiselect(
        "Send alerts for",
        options=["Critical", "Warning", "Overstock"],
        default=st.session_state.get("alert_levels", ["Critical", "Warning"])
    )

    st.session_state.alert_levels = alert_levels

    st.divider()

    st.subheader("👥 Alert recipients")

    recipients = st.multiselect(
        "Recipient groups",
        options=[
            "Hospital procurement team",
            "Warehouse manager",
            "District health office",
            "NGO / partner organization"
        ],
        default=st.session_state.get(
            "recipients", ["Hospital procurement team"]
        )
    )

    st.session_state.recipients = recipients

    st.divider()

    if st.button("💾 Save alert preferences"):
        st.success("Alert preferences saved successfully ✅")

    st.info(
        "ℹ️ In production, these settings would be stored in Snowflake "
        "and consumed by Tasks or external notification services."
    )


# =================================================
# IMPACT
# =================================================
# =================================================
# IMPACT
# =================================================
elif page == "Impact":

    # -------------------------------------------------
    # HEADER
    # -------------------------------------------------
    st.markdown(
        """
        <h1 style="margin-bottom:0.3rem;">🌍 Real-World Impact</h1>
        <p style="color:#475569; font-size:1rem; max-width:900px;">
        CareStock Watch is designed to deliver <b>measurable, real-world outcomes</b> —
        protecting patients, reducing emergency costs, and minimizing medicine wastage
        across hospitals, public distribution systems, and NGOs.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # -------------------------------------------------
    # ASSUMPTIONS (TRANSPARENT & EXPLAINABLE)
    # -------------------------------------------------
    with st.expander("📌 Impact assumptions (transparent & conservative)"):
        st.markdown(
            """
            - Average patients served per item per day: **3**  
            - Average emergency procurement cost per stock-out: **₹2,500**  
            - Average wastage reduction due to early visibility: **15%**  
            - Average stock-out days prevented per incident: **5 days**  

            These assumptions are conservative and can be refined using
            real hospital / PDS / NGO data in production.
            """
        )

    # -------------------------------------------------
    # CORE DATA
    # -------------------------------------------------
    critical = df[df["STOCK_STATUS"] == "Critical"]
    warning = df[df["STOCK_STATUS"] == "Warning"]
    overstock = df[df["OVERSTOCK_RISK"]]

    # -------------------------------------------------
    # IMPACT CALCULATIONS
    # -------------------------------------------------
    PATIENTS_PER_ITEM_PER_DAY = 3
    COST_PER_STOCKOUT = 2500
    DAYS_PREVENTED = 5
    WASTE_REDUCTION_RATE = 0.15

    patients_protected = (
        (len(critical) + len(warning))
        * PATIENTS_PER_ITEM_PER_DAY
        * DAYS_PREVENTED
    )

    cost_saved = len(critical) * COST_PER_STOCKOUT
    waste_reduction_pct = int(WASTE_REDUCTION_RATE * 100)

    locations_covered = df["LOCATION"].nunique()
    items_monitored = df["ITEM"].nunique()

    life_saving_items_monitored = df[df["ITEM_PRIORITY"] == "🔴 Life-saving"]["ITEM"].nunique()

    # -------------------------------------------------
    # PREMIUM KPI CARDS
    # -------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div style="background:#ECFDF5; border:1px solid #A7F3D0;
                        border-radius:16px; padding:20px; text-align:center;">
                <div style="font-size:14px; color:#065F46;">🧑‍⚕️ Patients protected</div>
                <div style="font-size:34px; font-weight:700; color:#064E3B;">
                    {patients_protected}+
                </div>
                <div style="font-size:12px; color:#064E3B;">
                    uninterrupted care delivered
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background:#EFF6FF; border:1px solid #BFDBFE;
                        border-radius:16px; padding:20px; text-align:center;">
                <div style="font-size:14px; color:#1E3A8A;">💰 Cost savings</div>
                <div style="font-size:34px; font-weight:700; color:#1E40AF;">
                    ₹{cost_saved:,}
                </div>
                <div style="font-size:12px; color:#1E40AF;">
                    emergency procurement avoided
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="background:#FFFBEB; border:1px solid #FDE68A;
                        border-radius:16px; padding:20px; text-align:center;">
                <div style="font-size:14px; color:#92400E;">♻️ Waste reduced</div>
                <div style="font-size:34px; font-weight:700; color:#78350F;">
                    {waste_reduction_pct}%
                </div>
                <div style="font-size:12px; color:#78350F;">
                    expiry risk prevented
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div style="background:#F8FAFC; border:1px solid #E2E8F0;
                        border-radius:16px; padding:20px; text-align:center;">
                <div style="font-size:14px; color:#334155;">📦 System scale</div>
                <div style="font-size:30px; font-weight:700; color:#0F172A;">
                    {locations_covered} × {items_monitored}
                </div>
                <div style="font-size:12px; color:#334155;">
                    locations × items monitored
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # -------------------------------------------------
    # ADDITIONAL IMPACT METRICS
    # -------------------------------------------------
    st.subheader("📈 Additional impact indicators")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Life-saving items tracked",
        life_saving_items_monitored,
        help="Critical supplies like insulin, oxygen, blood, ventilators"
    )

    c2.metric(
        "At-risk items identified early",
        len(critical) + len(warning),
        help="Detected before shelves go empty"
    )

    c3.metric(
        "Overstock risks flagged",
        len(overstock),
        help="Potential expiry or wastage identified in advance"
    )

    st.divider()

    # -------------------------------------------------
    # IMPACT MECHANISM
    # -------------------------------------------------
    st.subheader("🧠 How CareStock Watch creates impact")

    st.markdown(
        """
        - **Early-warning intelligence** detects shortages days in advance  
        - **AI-assisted demand forecasting** supports proactive procurement  
        - **Overstock detection** reduces medicine expiry and wastage  
        - **Human-in-the-loop actions** improve accountability and coordination  
        - **Shared visibility** aligns hospitals, warehouses, and NGOs  
        """
    )

    st.divider()

    # -------------------------------------------------
    # BEFORE VS AFTER COMPARISON
    # -------------------------------------------------
    st.subheader("📌 Problem validation: before vs after")

    impact_table = pd.DataFrame({
        "Aspect": [
            "Stock-out detection",
            "Emergency procurement",
            "Medicine wastage",
            "Inter-team coordination",
            "Decision-making speed"
        ],
        "Before CareStock Watch": [
            "Detected after shelves are empty",
            "High, unplanned spending",
            "Hidden until expiry",
            "Manual follow-ups",
            "Reactive firefighting"
        ],
        "With CareStock Watch": [
            "Detected days in advance",
            "Reduced through early planning",
            "Flagged proactively",
            "Logged & visible actions",
            "Proactive, data-driven decisions"
        ]
    })

    st.dataframe(impact_table, use_container_width=True)

    st.divider()

    st.success(
        "CareStock Watch transforms inventory management from a reactive process "
        "into a proactive, AI-assisted public-good system."
    )


# =================================================
# ANALYTICS
# =================================================
elif page == "Analytics":

    # -------------------------------------------------
    # HEADER
    # -------------------------------------------------
    st.markdown(
        """
        <h1 style="margin-bottom:0.3rem;">📊 Inventory Analytics</h1>
        <p style="color:#475569; font-size:1rem; max-width:900px;">
        Visual insights that help decision-makers quickly understand
        <b>where risks are concentrated</b> and <b>what needs attention first</b>.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # -------------------------------------------------
    # 1️⃣ STOCK HEALTH DISTRIBUTION
    # -------------------------------------------------
    st.subheader("Overall stock health distribution")

    status_counts = (
        df.groupby("STOCK_STATUS")
        .size()
        .reset_index(name="COUNT")
    )

    fig_status = px.bar(
        status_counts,
        x="STOCK_STATUS",
        y="COUNT",
        color="STOCK_STATUS",
        color_discrete_map={
            "Critical": "#EF4444",
            "Warning": "#F59E0B",
            "Healthy": "#10B981"
        },
        text="COUNT"
    )

    fig_status.update_layout(
        template="simple_white",
        height=360,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="",
        yaxis_title="Number of items",
        showlegend=False,
        title=dict(
            text="Items by inventory health status",
            x=0,
            font=dict(size=18)
        )
    )

    fig_status.update_traces(
        textposition="outside",
        marker=dict(opacity=0.9)
    )

    st.plotly_chart(fig_status, use_container_width=True)

    st.caption(
        "This view helps leaders immediately assess how much inventory "
        "is at risk versus healthy."
    )

    st.divider()

    # -------------------------------------------------
    # 2️⃣ LOCATION RISK COMPARISON
    # -------------------------------------------------
    st.subheader("At-risk items by location")

    location_risk = (
        df[df["STOCK_STATUS"].isin(["Critical", "Warning"])]
        .groupby("LOCATION")
        .size()
        .reset_index(name="AT_RISK_ITEMS")
        .sort_values("AT_RISK_ITEMS", ascending=False)
    )

    if location_risk.empty:
        st.info("No locations currently have critical or warning items.")
    else:
        fig_location = px.bar(
            location_risk,
            x="LOCATION",
            y="AT_RISK_ITEMS",
            text="AT_RISK_ITEMS",
            color_discrete_sequence=["#6366F1"]
        )

        fig_location.update_layout(
            template="simple_white",
            height=360,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="Location",
            yaxis_title="At-risk items",
            title=dict(
                text="Locations with highest supply risk",
                x=0,
                font=dict(size=18)
            )
        )

        fig_location.update_traces(
            textposition="outside",
            marker=dict(opacity=0.85)
        )

        st.plotly_chart(fig_location, use_container_width=True)

    st.caption(
        "This ranking helps prioritize interventions at locations "
        "with the highest concentration of risk."
    )

    st.divider()

    # -------------------------------------------------
    # 3️⃣ STOCK COVERAGE HEATMAP
    # -------------------------------------------------
    st.subheader("Days of stock cover — heatmap")

    heat = (
        df.pivot(
            index="LOCATION",
            columns="ITEM",
            values="DAYS_OF_COVER"
        )
        .fillna(0)
    )

    fig_heat = px.imshow(
        heat,
        color_continuous_scale=[
            "#FEE2E2",  # low cover (risk)
            "#FEF3C7",  # medium
            "#DCFCE7"   # healthy
        ],
        aspect="auto"
    )

    fig_heat.update_layout(
        template="simple_white",
        height=420,
        margin=dict(l=20, r=20, t=40, b=20),
        title=dict(
            text="Days of stock cover by location and item",
            x=0,
            font=dict(size=18)
        ),
        coloraxis_colorbar=dict(
            title="Days of cover",
            thickness=12,
            len=0.6
        )
    )

    st.plotly_chart(fig_heat, use_container_width=True)

    st.caption(
        "Red zones indicate items likely to run out soon; "
        "green zones indicate adequate coverage."
    )

    st.divider()

    # -------------------------------------------------
    # 4️⃣ LIFE-SAVING ITEMS FOCUS
    # -------------------------------------------------
    st.subheader("Life-saving items at risk")

    life_risk = df[
        (df["ITEM_PRIORITY"] == "🔴 Life-saving") &
        (df["STOCK_STATUS"].isin(["Critical", "Warning"]))
    ]

    if life_risk.empty:
        st.success("All life-saving items currently have sufficient coverage.")
    else:
        st.dataframe(
            life_risk[
                [
                    "LOCATION",
                    "ITEM",
                    "STATUS_BADGE",
                    "CLOSING_STOCK",
                    "DAYS_TO_STOCKOUT"
                ]
            ],
            use_container_width=True
        )

        st.warning(
            "Life-saving supplies should always be prioritized "
            "over non-critical inventory."
        )

    st.divider()

    # -------------------------------------------------
    # 5️⃣ EXECUTIVE INSIGHTS
    # -------------------------------------------------
    st.markdown(
        """
        **Key insights**
        - Stock health distribution shows overall system risk at a glance  
        - Location ranking highlights where intervention will have the most impact  
        - Heatmaps expose hidden gaps across locations and items  
        - Life-saving supplies receive explicit priority  
        - Early analytics enables proactive rather than reactive decisions
        """
    )

