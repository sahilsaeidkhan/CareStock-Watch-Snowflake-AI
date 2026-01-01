import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
import plotly.express as px
from datetime import datetime
import numpy as np
import json

from snowflake_core.ai_component_additions import cortex_demand_forecast

# ...rest of the code copied from snowflake_core/streamlit_app.py...
