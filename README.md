# IoT Query Probe

A simple, open-source analytics application for exploring and visualizing IoT data from [Navixy IoT Query](https://www.navixy.com/en/iot-query/) database.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Overview

IoT Query Probe is a lightweight, browser-based tool designed for data analysts and developers who need to quickly explore, visualize, and export IoT telematics data. Built with Streamlit, it provides an intuitive interface for running SQL queries against PostgreSQL databases and generating insightful reports.

## Features

### Data Exploration
- **SQL Editor** - Write and execute SQL queries
- **Client-side Filtering** - Filter query results without re-running queries

### Visualizations
- **Interactive Charts** - Line charts with customizable X/Y axes and color grouping
- **Geospatial Maps** - Scatter maps with auto-zoom based on coordinate bounds
- **Color-coded Legends** - Distinguish data categories with automatic color assignment

### Export & Reporting
- **Excel Export** - Download filtered data as `.xlsx` files
- **HTML Reports** - Generate print-friendly reports with:
  - Custom report name and description
  - Data tables (up to 500 rows)
  - Charts and maps with preserved colors
  - Optimized for A4 landscape printing

### Performance & Safety
- **Query Timeouts** - 5-minute limit for complex queries
- **Row Limits** - Maximum 10,000 rows returned to prevent memory exhaustion
- **Sanitized Errors** - Connection strings and credentials are never exposed in error messages
- **SSL/TLS Support** - Secure database connections

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Access to a Navixy IoT Query database

### Installation

1. Clone the repository:
```bash
git clone https://github.com/AndyMelnik/iot-query-probe.git
cd iot-query-probe
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

4. Open your browser to `http://localhost:8501`

### Connecting to a Database

1. Enter your database credentials in the sidebar:
   - **Host**: Database server hostname
   - **Port**: PostgreSQL port (default: 5432)
   - **Database**: Database name
   - **User**: Username
   - **Password**: Password

2. Click **Connect**

3. Write your SQL query and click **Execute**

## Usage Examples

### Basic Query
```sql
SELECT * FROM tracking_data LIMIT 100;
```

### Aggregated Data
```sql
SELECT 
    vehicle_id,
    DATE(timestamp) as date,
    COUNT(*) as points,
    AVG(speed) as avg_speed
FROM tracking_data
WHERE timestamp >= '2024-01-01'
GROUP BY vehicle_id, DATE(timestamp)
ORDER BY date;
```

### Geospatial Query
```sql
SELECT 
    latitude,
    longitude,
    vehicle_name,
    timestamp
FROM tracking_data
WHERE latitude IS NOT NULL
LIMIT 5000;
```

## Configuration

### Environment Variables (Optional)

Create a `.streamlit/secrets.toml` file for default settings:

```toml
# Optional: Pre-configured database connection
[database]
host = "your-db-host.com"
port = "5432"
name = "your_database"
user = "your_user"
# Note: Never commit passwords to version control
```

### Customization

Edit the constants in `app.py` to adjust limits:

```python
MAX_ROWS = 10000          # Maximum rows returned from queries
MAX_EXPORT_ROWS = 50000   # Maximum rows in Excel export
QUERY_TIMEOUT_MS = 300000 # Query timeout in milliseconds (5 minutes)
```

## Project Structure

```
iot-query-probe/
├── app.py              # Main application (single file)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | ≥1.28.0 | Web application framework |
| pandas | ≥2.0.0 | Data manipulation |
| plotly | ≥5.18.0 | Interactive charts and maps |
| pg8000 | ≥1.30.0 | PostgreSQL database driver |
| openpyxl | ≥3.1.0 | Excel file generation |

## Security Considerations

This application executes SQL queries directly against the database. Security is managed at the database level:

- **Database Permissions** - Use database user permissions to control query access
- **Query Timeouts** - 5-minute statement timeout for complex queries
- **Lock Timeouts** - 5-second lock timeout prevents blocking
- **SSL/TLS** - Encrypted database connections supported
- **Credential Protection** - Passwords masked in UI, sanitized in error messages

**Important**: For production deployments:
- Create a read-only database user with limited table access
- Consider adding authentication (e.g., Streamlit authentication, reverse proxy with auth)
- Deploy behind a firewall or VPN for internal use

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- Built for use with [Navixy](https://www.navixy.com/) IoT platform
- Powered by [Streamlit](https://streamlit.io/)
- Maps provided by [CARTO](https://carto.com/)

## Support

THis is AS IS app. For questions, please use the [GitHub Issues](https://github.com/AndyMelnik/iot-query-probe/issues) page.

---



