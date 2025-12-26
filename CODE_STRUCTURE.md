# CareStock Watch - Code Structure and Architecture

## Directory Structure

```
src/
├── app.py                          # Main Streamlit application entry point
├── pages/                          # Streamlit multi-page app directory
│   ├── __init__.py
│   ├── 1_Dashboard.py             # KPI dashboard and overview
│   ├── 2_Analytics.py             # Detailed analytics and graphs
│   ├── 3_Actions.py               # Action logging and management
│   └── 4_Settings.py              # User settings and preferences
│
├── modules/                        # Core application modules
│   ├── __init__.py
│   ├── ai_component_additions.py  # ML/AI enhancements and models
│   ├── data_loader.py             # Snowflake data loading and caching
│   ├── forecast_engine.py         # Demand forecasting algorithm
│   ├── risk_analyzer.py           # Risk detection and categorization
│   └── alert_manager.py           # Alert sending and management
│
├── utils/                          # Utility functions
│   ├── __init__.py
│   ├── database.py                # Database operations and queries
│   ├── cache.py                   # Streamlit cache utilities
│   ├── validators.py              # Input validation functions
│   └── formatters.py              # Data formatting utilities
│
└── config/                         # Configuration files
    ├── __init__.py
    ├── settings.py                # App settings and constants
    ├── database_config.py         # Snowflake connection config
    └── constants.py               # Global constants and enums
```

## Module Descriptions

### 📄 app.py (Main Application)

**Purpose**: Entry point for the Streamlit application

**Key Components**:
- Page configuration and layout
- Session state management
- Navigation logic
- Global styles and theming

**Key Functions**:
```python
if __name__ == "__main__":
    main()
```

---

### 📂 pages/ (Multi-page Application)

#### 1_Dashboard.py
**Purpose**: Display real-time KPI metrics and inventory status

**Features**:
- Critical items count (red/danger)
- Warning items count (yellow/warning)
- Healthy items count (green/success)
- Location and item filters
- Early-warning risk table
- Wastage risk table
- Complete stock overview

**Key Functions**:
```python
def display_kpi_metrics(data)
def display_risk_tables(risk_data)
def filter_inventory_data(location, items)
```

#### 2_Analytics.py
**Purpose**: Detailed analytics and trend visualization

**Features**:
- Demand forecasting charts
- Inventory trend graphs
- Risk distribution pie charts
- Action history timeline
- Impact metrics (patients protected, cost saved, waste reduced)

**Key Functions**:
```python
def generate_forecast_chart(item_id, days=30)
def plot_inventory_trends(location_id)
def calculate_impact_metrics(action_log)
```

#### 3_Actions.py
**Purpose**: Log inventory management actions

**Features**:
- Action type selection (PO Raised, Transferred, etc.)
- Item selection dropdown
- Location selection
- Notes field
- User attribution
- Timestamp tracking
- Action history table

**Key Functions**:
```python
def log_action(item_id, action_type, notes, user)
def display_action_history(filters)
def validate_action_input(form_data)
```

#### 4_Settings.py
**Purpose**: Manage user preferences and alert settings

**Features**:
- Email alert configuration
- SMS/WhatsApp alert configuration
- Alert severity preferences
- Recipient group management
- Settings persistence

**Key Functions**:
```python
def save_alert_preferences(user_id, settings)
def validate_contact_info(email, phone)
def load_user_settings(user_id)
```

---

### 📦 modules/ (Core Functionality)

#### ai_component_additions.py
**Purpose**: AI/ML enhancements and predictive models

**Classes**:
```python
class DemandForecaster:
    """Demand prediction using historical data"""
    def predict(item_id, days_ahead)
    def calculate_confidence_interval()

class RiskDetector:
    """Identifies shortage and wastage risks"""
    def detect_shortage_risk(item_id)
    def detect_wastage_risk(item_id)

class MLPipeline:
    """Machine learning pipeline management"""
    def train_model(training_data)
    def evaluate_model(test_data)
    def make_predictions(input_data)
```

#### data_loader.py
**Purpose**: Load and manage data from Snowflake

**Classes**:
```python
class DataLoader:
    """Handle all Snowflake data operations"""
    def connect_snowflake()
    def load_inventory_items()
    def load_daily_demand(date_range)
    def load_action_log(filters)
    def cache_data(duration)
```

#### forecast_engine.py
**Purpose**: Generate demand forecasts

**Functions**:
```python
def calculate_moving_average(data, window)
def exponential_smoothing(data, alpha)
def linear_regression_forecast(data, periods)
def validate_forecast_accuracy(actual, predicted)
```

#### risk_analyzer.py
**Purpose**: Detect and categorize inventory risks

**Functions**:
```python
def analyze_stock_level(current_stock, reorder_point, demand_forecast)
def calculate_days_of_supply(stock, daily_demand)
def categorize_risk(shortage_probability, wastage_probability)
def generate_risk_recommendations(risk_data)
```

#### alert_manager.py
**Purpose**: Handle alert sending via multiple channels

**Classes**:
```python
class AlertManager:
    """Manage multi-channel alerts"""
    def send_email_alert(recipient, item_data)
    def send_sms_alert(phone, message)
    def send_whatsapp_alert(whatsapp_number, message)
    def send_notification(user_id, alert_data)
```

---

### 🔧 utils/ (Utility Functions)

#### database.py
**Purpose**: Database utility functions

**Functions**:
```python
def execute_query(sql, params)
def insert_action_log(action_data)
def update_inventory(item_id, new_stock)
def get_alert_settings(user_id)
```

#### cache.py
**Purpose**: Streamlit caching utilities

**Functions**:
```python
@st.cache_data
def load_inventory_data(ttl=3600)

@st.cache_resource
def initialize_db_connection()

def clear_cache()
```

#### validators.py
**Purpose**: Input validation

**Functions**:
```python
def validate_email(email)
def validate_phone(phone)
def validate_inventory_input(item_id, quantity)
def validate_date_range(start_date, end_date)
```

#### formatters.py
**Purpose**: Data formatting

**Functions**:
```python
def format_currency(amount)
def format_date(date_obj)
def format_percentage(value)
def format_table_data(dataframe)
```

---

### ⚙️ config/ (Configuration)

#### settings.py
```python
APP_NAME = "CareStock Watch"
APP_VERSION = "1.0.0"
DEBUG_MODE = True
LOG_LEVEL = "INFO"
CACHE_DURATION = 3600
MAX_WORKERS = 4
```

#### database_config.py
```python
SNOWFLAKE_CONFIG = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'warehouse': 'COMPUTE_WH',
    'database': 'HOSPITAL_STOCK_DB',
    'schema': 'PUBLIC'
}
```

#### constants.py
```python
ACTION_TYPES = ['PO Raised', 'Transferred', 'Delivered', 'NGO Support', 'Other']
RISK_CATEGORIES = ['Critical', 'Warning', 'Healthy']
ALERT_CHANNELS = ['Email', 'SMS', 'WhatsApp']
```

---

## Data Flow Architecture

```
Snowflake Database
        ↓
  DataLoader.py
        ↓
  Cache Layer (utils/cache.py)
        ↓
ForecastEngine.py + RiskAnalyzer.py
        ↓
  AI Components (ai_component_additions.py)
        ↓
  Dashboard / Analytics Pages
        ↓
User Actions (Actions.py)
        ↓
  Alert Manager (alert_manager.py)
        ↓
Multi-Channel Alerts (Email, SMS, WhatsApp)
```

## Class Hierarchy

```
DataLoader
    ├── connect_snowflake()
    ├── load_data()
    └── cache_operations()

RiskAnalyzer
    ├── detect_shortage_risk()
    ├── detect_wastage_risk()
    └── categorize_risk()

AlertManager
    ├── send_email_alert()
    ├── send_sms_alert()
    └── send_whatsapp_alert()

ML Pipeline
    ├── train_model()
    ├── predict()
    └── evaluate()
```

## Key Dependencies

- **streamlit**: Web UI framework
- **snowflake-snowpark-python**: Snowflake data operations
- **pandas**: Data manipulation
- **numpy**: Numerical operations
- **plotly**: Interactive visualizations
- **scikit-learn**: Machine learning
- **python-dotenv**: Environment variable management

## Development Guidelines

1. **Code Style**: Follow PEP 8
2. **Naming Conventions**:
   - Functions: `snake_case`
   - Classes: `PascalCase`
   - Constants: `UPPER_CASE`
3. **Docstrings**: Use Google-style docstrings
4. **Error Handling**: Try-except with logging
5. **Type Hints**: Use for function signatures

## Testing Structure

```
tests/
├── test_forecast_engine.py
├── test_risk_analyzer.py
├── test_data_loader.py
└── test_alert_manager.py
```

---

**Last Updated**: December 26, 2025
