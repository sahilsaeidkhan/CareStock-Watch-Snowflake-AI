# CareStock Watch - AI-Powered Hospital Inventory Management System

## 🏥 Project Overview

CareStock Watch is an intelligent Streamlit application built on Snowflake that revolutionizes hospital inventory management through AI-driven insights. The system predicts shortages before shelves go empty and flags overstock waste, ensuring optimal inventory levels across hospital locations.

## 🎯 Key Features

### Dashboard & Analytics
- **Real-Time KPI Metrics**: Display of Critical, Warning, and Healthy inventory items
- **Early-Warning System**: Alerts for stock-out risks based on demand patterns
- **Wastage Detection**: Identifies overstock situations to minimize waste
- **Location-Based Filtering**: Filter inventory by hospital locations
- **Item-Based Filtering**: Focus on specific medical supplies

### Intelligence & Forecasting
- **AI-Driven Demand Forecasting**: Uses historical demand patterns and supplier lead times
- **Predictive Risk Analysis**: Automatically identifies shortage and wastage risks
- **Smart Algorithms**: Machine learning models running inside Snowflake

### Action Management
- **Action Logging**: Track all inventory management actions with timestamps
- **Action Types**: PO Raised, Transferred, Delivered, NGO Support, Other
- **User Attribution**: Log which team member took which action
- **Audit Trail**: Complete history for compliance and analysis

### Alert & Notification System
- **Multi-Channel Alerts**: Email, SMS, WhatsApp notifications
- **Configurable Preferences**: Customize alert severity and recipient groups
- **Flexible Settings**: Enable/disable channels per user preference

### Data Export
- **CSV Export**: Download risk lists and inventory data
- **Priority Lists**: Export early-warning items for quick action
- **Searchable Tables**: Find specific items quickly

## 📁 Project Structure

```
CareStock-Watch/
├── MAIN_README.md                      # Main project documentation
├── SETUP_GUIDE.md                      # Installation and setup instructions
├── API_DOCUMENTATION.md                # API and integration details
├── CODE_STRUCTURE.md                   # Detailed code organization
├── DEPLOYMENT_GUIDE.md                 # Deployment and production setup
│
├── src/                                # Source code directory
│   ├── app.py                          # Main Streamlit application
│   ├── pages/                          # Streamlit pages
│   │   ├── dashboard.py                # Dashboard page
│   │   ├── analytics.py                # Analytics page
│   │   ├── actions.py                  # Action logging page
│   │   └── settings.py                 # User settings page
│   │
│   ├── modules/                        # Core functionality modules
│   │   ├── ai_component_additions.py   # AI/ML enhancements
│   │   ├── data_loader.py              # Snowflake data loading
│   │   ├── forecast_engine.py          # Demand forecasting
│   │   ├── risk_analyzer.py            # Risk detection algorithm
│   │   └── alert_manager.py            # Alert handling
│   │
│   ├── utils/                          # Utility functions
│   │   ├── database.py                 # Database operations
│   │   ├── cache.py                    # Caching utilities
│   │   ├── validators.py               # Input validation
│   │   └── formatters.py               # Data formatting
│   │
│   └── config/                         # Configuration
│       ├── settings.py                 # Application settings
│       ├── database_config.py          # Snowflake config
│       └── constants.py                # Constants and enums
│
├── data/                               # Data files
│   ├── sample_data.csv                 # Sample inventory data
│   └── expected_output.json            # Example outputs
│
├── tests/                              # Test suite
│   ├── test_forecast_engine.py         # Forecast tests
│   ├── test_risk_analyzer.py           # Risk detection tests
│   └── test_data_loader.py             # Data loading tests
│
├── docs/                               # Additional documentation
│   ├── ARCHITECTURE.md                 # System architecture
│   ├── DATABASE_SCHEMA.md              # Snowflake schema details
│   ├── API_ENDPOINTS.md                # API reference
│   └── TROUBLESHOOTING.md              # Troubleshooting guide
│
├── requirements.txt                    # Python dependencies
├── environment.yml                     # Conda environment
├── .gitignore                          # Git ignore rules
├── .github/                            # GitHub workflows
│   └── workflows/                      # CI/CD pipelines
└── LICENSE                             # MIT License
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Snowflake account with database access
- GitHub account (for version control)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sahilsaeidkhan/CareStock-Watch.git
   cd CareStock-Watch
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Snowflake connection**
   ```bash
   # Edit config/database_config.py with your Snowflake credentials
   ```

4. **Run the application**
   ```bash
   streamlit run src/app.py
   ```

## 📊 Data Model

### Core Tables

#### INVENTORY_ITEMS
- Item ID, Name, Category
- Current Stock Level
- Reorder Point, Safety Stock
- Supplier Lead Time

#### DAILY_DEMAND
- Date, Item ID, Location ID
- Quantity Demanded
- Actual Consumption

#### INVENTORY_TRANSACTIONS
- Transaction ID, Type (In/Out)
- Item ID, Quantity, Date
- Location ID, User ID

#### ACTION_LOG
- Action ID, Timestamp
- Item ID, Location ID
- Action Type, User Name
- Notes, Status

#### ALERT_SETTINGS
- User ID, Enabled Channels
- Email Address, Phone Number
- Alert Preferences

## 🔄 Workflow

1. **Data Ingestion**: Daily inventory and demand data from hospital systems
2. **AI Processing**: Snowflake runs demand forecasts and risk analysis
3. **Dashboard Display**: Real-time KPIs and alerts shown to users
4. **Action Logging**: Users log actions taken (PO, Transfer, etc.)
5. **Analytics**: Track impact metrics - patients protected, costs saved, waste reduced
6. **Notifications**: Multi-channel alerts for critical items

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python)
- **Backend**: Python, Snowflake Snowpark
- **Database**: Snowflake Data Cloud
- **ML/AI**: Python scikit-learn, pandas, NumPy
- **Visualization**: Plotly, matplotlib
- **Version Control**: Git, GitHub
- **CI/CD**: GitHub Actions
- **Deployment**: Snowflake Streamlit Apps

## 📈 Key Metrics

- **Patients Protected**: Total patients served with uninterrupted care
- **Cost Savings**: Emergency procurement costs avoided (₹)
- **Waste Reduced**: Expiry risk percentage avoided (%)
- **System Scale**: Locations × Items managed

## 🔐 Security & Compliance

- Snowflake role-based access control (RBAC)
- Data encryption in transit and at rest
- Audit logging of all actions
- HIPAA compliance ready
- User authentication via Snowflake

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Documentation

See the following guides for detailed information:

- [Setup Guide](SETUP_GUIDE.md) - Installation and configuration
- [API Documentation](API_DOCUMENTATION.md) - API references
- [Code Structure](CODE_STRUCTURE.md) - Module descriptions
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Production deployment
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Database Schema](docs/DATABASE_SCHEMA.md) - Data structure

## 🐛 Known Issues

- None currently documented. Please report issues via GitHub Issues.

## 📞 Support

- **Email**: support@carestock-watch.com
- **GitHub Issues**: [Report a bug](https://github.com/sahilsaeidkhan/CareStock-Watch/issues)
- **Documentation**: See docs/ folder

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👥 Authors

- **Sahil Saeid Khan** - Main Developer
- **Contributors**: [Add your name here]

## 🙏 Acknowledgments

- Snowflake for providing the data platform
- Streamlit for the web framework
- The open-source community

---

**Last Updated**: December 26, 2025  
**Version**: 1.0.0  
**Status**: Active Development
