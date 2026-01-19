# IoT Query Probe

A simple, open-source analytics application for exploring and visualizing IoT data from [Navixy](https://www.navixy.com/) PostgreSQL databases.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Overview

IoT Query Probe is a lightweight, browser-based tool designed for data analysts and developers who need to quickly explore, visualize, and export IoT telematics data. Built with Streamlit, it provides an intuitive interface for running SQL queries against PostgreSQL databases and generating insightful reports.

## Features

### Data Exploration
- **SQL Editor** - Write and execute SELECT queries with syntax highlighting
- **Table Browser** - Browse available tables and load data with one click
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

### Security
- **SELECT-only Queries** - DML/DDL statements are blocked
- **SQL Injection Prevention** - Blocked patterns include multi-statements, comments, system functions
- **Query Timeouts** - 30-second limit prevents runaway queries
- **Row Limits** - Maximum 10,000 rows returned to prevent memory exhaustion
- **Sanitized Errors** - Connection strings and credentials are never exposed in error messages

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Access to a PostgreSQL database

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

3. Select a table or write a custom SQL query

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
QUERY_TIMEOUT_MS = 30000  # Query timeout in milliseconds
```

## Project Structure

```
iot-query-probe/
├── app.py              # Main application (single file)
├── requirements.txt    # Python dependencies
├── .gitignore          # Git ignore rules
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

This application is designed for **read-only data exploration**. Security features include:

- ✅ Only `SELECT` and `WITH` (CTE) queries allowed
- ✅ Blocked: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `GRANT`, `REVOKE`
- ✅ Blocked: Multi-statement queries (`;` followed by another statement)
- ✅ Blocked: SQL comments (`--`, `/* */`)
- ✅ Blocked: PostgreSQL system functions (`pg_*`)
- ✅ Statement and lock timeouts enforced
- ✅ SSL/TLS connections supported

**Note**: For production deployments, consider adding authentication (e.g., Streamlit authentication, reverse proxy with auth).

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

For issues and feature requests, please use the [GitHub Issues](https://github.com/AndyMelnik/iot-query-probe/issues) page.

---

Made with ❤️ for the IoT community

