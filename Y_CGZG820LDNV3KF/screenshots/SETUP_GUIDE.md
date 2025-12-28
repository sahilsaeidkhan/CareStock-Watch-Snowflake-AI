# CareStock Watch - Setup and Installation Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Snowflake Configuration](#snowflake-configuration)
4. [Environment Variables](#environment-variables)
5. [Running the Application](#running-the-application)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **pip**: Latest version
- **Git**: For version control
- **OS**: Linux, macOS, or Windows
- **RAM**: Minimum 4GB
- **Disk Space**: At least 2GB for dependencies

### Accounts and Services
- Snowflake account (Standard Edition or higher)
- Snowflake warehouse (compute resources)
- GitHub account (for repository access)

### Required Software
```bash
# Check Python version
python --version  # Should be 3.8+

# Check pip
pip --version

# Check Git
git --version
```

## Local Development Setup

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/sahilsaeidkhan/CareStock-Watch.git

# Navigate to project directory
cd CareStock-Watch

# Check git status
git status
```

### Step 2: Create Virtual Environment

**Using venv (Recommended)**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

**Using Conda**
```bash
# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate carestock-watch
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list | grep -E 'streamlit|snowflake|pandas'
```

### Step 4: Verify Installation

```bash
# Test imports
python -c "import streamlit as st; import snowflake.snowpark as sp; print('All imports successful!')"
```

## Snowflake Configuration

### Step 1: Create Snowflake Database

Log in to your Snowflake account and execute:

```sql
-- Create database
CREATE DATABASE HOSPITAL_STOCK_DB;

-- Use the database
USE DATABASE HOSPITAL_STOCK_DB;

-- Create schema
CREATE SCHEMA PUBLIC;

-- Create warehouse (if not exists)
CREATE WAREHOUSE COMPUTE_WH WITH WAREHOUSE_SIZE = 'SMALL';
```

### Step 2: Create Required Tables

```sql
-- INVENTORY_ITEMS table
CREATE TABLE INVENTORY_ITEMS (
    ITEM_ID INT PRIMARY KEY,
    ITEM_NAME VARCHAR(100),
    CATEGORY VARCHAR(50),
    CURRENT_STOCK INT,
    REORDER_POINT INT,
    SAFETY_STOCK INT,
    SUPPLIER_LEAD_DAYS INT,
    UNIT_COST DECIMAL(10,2),
    LAST_UPDATED TIMESTAMP
);

-- DAILY_DEMAND table
CREATE TABLE DAILY_DEMAND (
    DEMAND_ID INT PRIMARY KEY,
    DEMAND_DATE DATE,
    ITEM_ID INT,
    LOCATION_ID INT,
    QUANTITY_DEMANDED INT,
    ACTUAL_CONSUMPTION INT,
    FOREIGN KEY(ITEM_ID) REFERENCES INVENTORY_ITEMS(ITEM_ID)
);

-- ACTION_LOG table
CREATE TABLE ACTION_LOG (
    ACTION_ID INT PRIMARY KEY,
    ACTION_TIMESTAMP TIMESTAMP,
    ITEM_ID INT,
    LOCATION_ID INT,
    ACTION_TYPE VARCHAR(50),
    USER_NAME VARCHAR(100),
    NOTES VARCHAR(500),
    STATUS VARCHAR(20),
    FOREIGN KEY(ITEM_ID) REFERENCES INVENTORY_ITEMS(ITEM_ID)
);

-- ALERT_SETTINGS table
CREATE TABLE ALERT_SETTINGS (
    USER_ID INT PRIMARY KEY,
    EMAIL_ALERTS BOOLEAN,
    SMS_ALERTS BOOLEAN,
    WHATSAPP_ALERTS BOOLEAN,
    EMAIL_ADDRESS VARCHAR(100),
    PHONE_NUMBER VARCHAR(20),
    ALERT_SEVERITY VARCHAR(20)
);
```

### Step 3: Load Sample Data

```sql
-- Insert sample inventory items
INSERT INTO INVENTORY_ITEMS VALUES
(1, 'Bandages', 'Supplies', 500, 100, 50, 3, 5.00, CURRENT_TIMESTAMP),
(2, 'Insulin', 'Medications', 200, 50, 25, 5, 50.00, CURRENT_TIMESTAMP),
(3, 'Oxygen', 'Gases', 300, 75, 40, 2, 100.00, CURRENT_TIMESTAMP),
(4, 'Syringes', 'Supplies', 1000, 200, 100, 2, 2.00, CURRENT_TIMESTAMP);
```

## Environment Variables

### Create .env File

```bash
# In project root directory, create .env file
cat > .env << EOF
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account_name
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=HOSPITAL_STOCK_DB
SNOWFLAKE_SCHEMA=PUBLIC

# Application Settings
APP_ENV=development
DEBUG_MODE=true
LOG_LEVEL=INFO

# Alert Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Optional Settings
MAX_WORKERS=4
CACHE_DURATION=3600
EOF
```

### Update config/database_config.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

SNOWFLAKE_CONFIG = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    'database': os.getenv('SNOWFLAKE_DATABASE', 'HOSPITAL_STOCK_DB'),
    'schema': os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC')
}
```

## Running the Application

### Local Development

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run Streamlit application
streamlit run src/app.py

# Application will be available at http://localhost:8501
```

### Production Deployment (Snowflake Streamlit)

1. Push code to GitHub:
   ```bash
   git add .
   git commit -m "Deploy to production"
   git push origin main
   ```

2. In Snowflake, create Streamlit app:
   ```sql
   CREATE STREAMLIT CARESTOCK_WATCH_APP
   ROOT_LOCATION = @STREAMLIT_STAGE
   MAIN_FILE = 'src/app.py';
   ```

3. Access via Snowsight at: `https://<account>.snowflakecomputing.com/streamlit/`

## Troubleshooting

### Common Issues

**Issue 1: ModuleNotFoundError**
```bash
# Solution: Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Issue 2: Snowflake Connection Error**
```bash
# Solution: Verify Snowflake credentials
# Check .env file
# Verify account name format: https://<account_id>.snowflakecomputing.com
```

**Issue 3: Port 8501 Already in Use**
```bash
# Solution: Run on different port
streamlit run src/app.py --server.port 8502
```

**Issue 4: Virtual Environment Not Found**
```bash
# Solution: Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Getting Help

1. Check logs:
   ```bash
   # Streamlit debug mode
   streamlit run src/app.py --logger.level=debug
   ```

2. Test database connection:
   ```bash
   python -c "from src.modules.data_loader import DataLoader; DataLoader().test_connection()"
   ```

3. Check Python version:
   ```bash
   python --version
   ```

4. Report issues on GitHub: [Issue Tracker](https://github.com/sahilsaeidkhan/CareStock-Watch/issues)

## Next Steps

1. Read [MAIN_README.md](MAIN_README.md) for project overview
2. Check [CODE_STRUCTURE.md](CODE_STRUCTURE.md) for codebase organization
3. Review [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API details
4. Start the application and explore the dashboard

---

**Setup Last Updated**: December 26, 2025
