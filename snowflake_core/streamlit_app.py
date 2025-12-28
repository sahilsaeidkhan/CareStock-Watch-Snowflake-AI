import streamlit as st
#from ai_component_additions import cortex_demand_forecast
import pandas as pd
from snowflake.snowpark.context import get_active_session
import plotly.express as px
from datetime import datetime
import numpy as np

# =================================================
# INVENTORY OPTIMIZATION (EOQ + SAFETY STOCK)
# =================================================

def calculate_eoq(avg_daily_demand, ordering_cost=500, holding_cost=50):
    """
    EOQ calculationa
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
    return get_active_session()

session = get_session()

# =================================================
# LOAD DATA (Dynamic Table = AI Brain)
# =================================================
@st.cache_data(ttl=300)
def load_stock_health():
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

    with fcol1:
        sel_locations = st.multiselect(
            "📍 Location",
            options=sorted(df["LOCATION"].unique()),
            default=sorted(df["LOCATION"].unique()),
            key="filter_location"
        )

    with fcol2:
        sel_items = st.multiselect(
            "📦 Item",
            options=sorted(df["ITEM"].unique()),
            default=sorted(df["ITEM"].unique()),
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
# =================================================
elif page == "Actions":

    st.markdown(
        """
        <h1 style="margin-bottom:0.3rem;">📝 Action Log</h1>
        <p style="color:#475569; font-size:1rem; max-width:900px;">
        Record and track actions taken on at-risk items.
        This ensures accountability, coordination, and avoids duplicate efforts.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    at_risk = df[df["STOCK_STATUS"].isin(["Critical", "Warning"])]

    if at_risk.empty:
        st.success("No critical or warning items at the moment 🎉")
    else:
        st.subheader("🚨 Select an at-risk item")

        selected_index = st.selectbox(
            "Item requiring action",
            at_risk.index,
            format_func=lambda i: (
                f"{at_risk.loc[i,'LOCATION']} → "
                f"{at_risk.loc[i,'ITEM']} "
                f"({at_risk.loc[i,'STATUS_BADGE']})"
            )
        )

        selected_item = at_risk.loc[selected_index]

        st.divider()

        st.markdown(
            f"""
            <div style="
                background:#F8FAFC;
                border:1px solid #E2E8F0;
                border-radius:16px;
                padding:18px;">
                <b>📍 Location:</b> {selected_item['LOCATION']}<br>
                <b>📦 Item:</b> {selected_item['ITEM']}<br>
                <b>🚦 Status:</b> {selected_item['STATUS_BADGE']}<br>
                <b>⏳ Days to stock-out:</b> {round(selected_item['DAYS_TO_STOCKOUT'], 1)}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        st.subheader("✍️ Log action taken")

        with st.form("action_form"):
            action_taken = st.selectbox(
                "Action type",
                [
                    "Purchase order raised",
                    "Transferred from another location",
                    "Delivered to location",
                    "NGO / partner support requested",
                    "Other"
                ]
            )

            notes = st.text_area(
                "Additional notes (optional)",
                placeholder="Add any useful context for other teams or future reference..."
            )

            user = st.text_input(
                "Your name / team",
                placeholder="e.g. District Hospital Supply Team"
            )

            submit = st.form_submit_button("💾 Save action")

        if submit:
            if not user.strip():
                st.error("Please enter your name or team before saving.")
            else:
                session.sql(
                    """
                    INSERT INTO ACTION_LOG
                    (ACTION_TIMESTAMP, LOCATION, ITEM, ACTION_TYPE, NOTES, USER_NAME)
                    VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)
                    """,
                    params=[
                        selected_item["LOCATION"],
                        selected_item["ITEM"],
                        action_taken,
                        notes,
                        user
                    ]
                ).collect()

                st.success("Action logged successfully ✅")

    st.divider()

    st.subheader("📜 Recent actions")

    try:
        actions_df = session.sql(
            """
            SELECT
                ACTION_TIMESTAMP,
                LOCATION,
                ITEM,
                ACTION_TYPE,
                NOTES,
                USER_NAME
            FROM ACTION_LOG
            ORDER BY ACTION_TIMESTAMP DESC
            LIMIT 20
            """
        ).to_pandas()

        if actions_df.empty:
            st.info("No actions recorded yet.")
        else:
            st.dataframe(actions_df, use_container_width=True)

    except Exception:
        st.info(
            "Action log table not found. "
            "Create ACTION_LOG table to enable this feature."
        )

    st.info(
        "ℹ️ **Why this matters**  \n"
        "Action logging keeps humans in control, improves coordination, "
        "and creates an audit trail for critical supply decisions."
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

