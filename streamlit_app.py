import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
import plotly.express as px
from datetime import datetime
import numpy as np
import json
from snowflake_core.ai_component_additions import cortex_demand_forecast

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

# ...rest of the code from snowflake_core/streamlit_app.py continues here (due to length, only the first part is shown)...
