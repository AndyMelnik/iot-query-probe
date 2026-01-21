# Technical Requirements Document

## IoT Query Probe - SQL Analytics Application

**Version:** 1.0  
**Date:** January 2026  
**Document Type:** Technical Requirements Specification

---

## 1. Overview

### 1.1 Purpose
IoT Query Probe is a lightweight, single-file web application for exploring and analyzing PostgreSQL databases. It provides a secure SQL interface with data visualization and export capabilities, designed for IoT and business data analysis.

### 1.2 Scope
This document defines the functional and non-functional requirements for the IoT Query Probe application.

### 1.3 Target Users
- Data analysts
- IoT platform administrators
- Business intelligence users
- Developers requiring quick database exploration

---

## 2. System Architecture

### 2.1 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Streamlit | Latest |
| Language | Python | 3.8+ |
| Database Driver | pg8000 | Latest |
| Data Processing | Pandas | Latest |
| Visualization | Plotly Express | Latest |
| Export | openpyxl | Latest |

### 2.2 Architecture Pattern
- Single-file application (`app.py`)
- Stateless design with session-based state management
- Client-server model (Streamlit handles both)

### 2.3 Deployment Model
- Single Python file deployment
- No external configuration files required
- All settings embedded in application code

---

## 3. Functional Requirements

### 3.1 Database Connection

#### 3.1.1 Connection Methods
| ID | Requirement |
|----|-------------|
| DB-001 | Support PostgreSQL connection via individual fields (host, port, database, user, password) |
| DB-002 | Support PostgreSQL connection via full connection URL |
| DB-003 | URL-encode special characters in credentials (supports `<`, `>`, `^`, `@`, `#`, etc.) |
| DB-004 | SSL/TLS connection support with configurable modes |

#### 3.1.2 Connection Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| Port | 5432 | PostgreSQL port |
| SSL Mode | require | Connection encryption mode |
| Timeout | 30 seconds | Connection timeout |

#### 3.1.3 Connection Status
| ID | Requirement |
|----|-------------|
| DB-005 | Display "Connected" status on successful connection |
| DB-006 | Display sanitized error message on connection failure |
| DB-007 | Provide disconnect functionality to clear session |

### 3.2 SQL Query Editor

#### 3.2.1 Query Execution
| ID | Requirement |
|----|-------------|
| SQL-001 | Provide text area for SQL query input |
| SQL-002 | Support SELECT queries only |
| SQL-003 | Support Common Table Expressions (WITH clauses) |
| SQL-004 | Execute button to run queries |
| SQL-005 | Clear button to reset query and results |
| SQL-006 | Display execution time, row count, and column count |

#### 3.2.2 Query Validation
| ID | Requirement |
|----|-------------|
| SQL-007 | Block DML statements (INSERT, UPDATE, DELETE) |
| SQL-008 | Block DDL statements (CREATE, ALTER, DROP, TRUNCATE) |
| SQL-009 | Block administrative statements (GRANT, REVOKE, EXECUTE) |
| SQL-010 | Block multiple statements (semicolon followed by statement) |
| SQL-011 | Block SQL comments (-- and /* */) |
| SQL-012 | Block PostgreSQL system function access (pg_*) |
| SQL-013 | Block file operations (INTO OUTFILE, LOAD_FILE) |

### 3.3 Table Browser

| ID | Requirement |
|----|-------------|
| TBL-001 | List available tables after connection (excluding system schemas) |
| TBL-002 | Allow table selection from dropdown |
| TBL-003 | "Load table" button generates SELECT query with LIMIT 100 |
| TBL-004 | Limit table list to 100 entries |

### 3.4 Data Table Display

#### 3.4.1 Table Features
| ID | Requirement |
|----|-------------|
| DT-001 | Display query results in interactive data table |
| DT-002 | Show row count, column count, and filter status metrics |
| DT-003 | Fixed table height (400px) with scroll |
| DT-004 | Full-width responsive layout |

#### 3.4.2 Filtering
| ID | Requirement |
|----|-------------|
| DT-005 | Multi-select column filter in expandable section |
| DT-006 | Per-column value filtering (multi-select unique values) |
| DT-007 | Limit filter options to 50 unique values per column |
| DT-008 | Apply filters to downstream visualizations |

### 3.5 Chart Visualization

| ID | Requirement |
|----|-------------|
| CHT-001 | Line chart visualization using Plotly Express |
| CHT-002 | X-axis column selector (all columns) |
| CHT-003 | Y-axis column selector (all columns) |
| CHT-004 | Optional color-by column selector |
| CHT-005 | Generate Chart button to create visualization |
| CHT-006 | Persist chart in session for export |
| CHT-007 | Light theme (plotly_white) for display |

### 3.6 Map Visualization

| ID | Requirement |
|----|-------------|
| MAP-001 | Scatter map visualization using Plotly Mapbox |
| MAP-002 | Auto-detect latitude column (lat, latitude, y patterns) |
| MAP-003 | Auto-detect longitude column (lon, lng, longitude, x patterns) |
| MAP-004 | Manual latitude/longitude column selection |
| MAP-005 | Optional color-by column selector with legend |
| MAP-006 | Automatic zoom calculation based on data bounds |
| MAP-007 | Center map on data centroid |
| MAP-008 | Sample to 5,000 points for performance |
| MAP-009 | Light map style (carto-positron) |
| MAP-010 | Legend with category colors when color-by is used |

### 3.7 Data Export

#### 3.7.1 Excel Export
| ID | Requirement |
|----|-------------|
| EXP-001 | Export filtered data to Excel (.xlsx) format |
| EXP-002 | Auto-generated filename with timestamp |
| EXP-003 | Handle timezone-aware datetimes (convert to naive) |
| EXP-004 | Maximum 50,000 rows per export |

#### 3.7.2 HTML Report Export
| ID | Requirement |
|----|-------------|
| RPT-001 | Generate print-friendly HTML report |
| RPT-002 | Include report name (user-specified) |
| RPT-003 | Include optional description |
| RPT-004 | Include data table (max 500 rows) |
| RPT-005 | Include chart if generated |
| RPT-006 | Include map if generated |
| RPT-007 | Include generation timestamp and row count |
| RPT-008 | A4 landscape page format |
| RPT-009 | Proper page break handling for printing |
| RPT-010 | Repeating table headers across pages |
| RPT-011 | Light background for print (white) |
| RPT-012 | CDN-hosted Plotly.js for interactivity |

---

## 4. Non-Functional Requirements

### 4.1 Security

| ID | Requirement | Implementation |
|----|-------------|----------------|
| SEC-001 | SELECT-only query execution | Query validation regex |
| SEC-002 | No credential logging | Sanitize error messages |
| SEC-003 | Connection string masking in errors | Regex replacement |
| SEC-004 | Password field masking in UI | type="password" |
| SEC-005 | SSL/TLS database connections | ssl_context configuration |
| SEC-006 | Query timeout enforcement | statement_timeout setting |
| SEC-007 | Lock timeout enforcement | lock_timeout setting |

### 4.2 Performance

| ID | Requirement | Value |
|----|-------------|-------|
| PERF-001 | Maximum query result rows | 10,000 |
| PERF-002 | Maximum export rows | 50,000 |
| PERF-003 | Query timeout | 30 seconds |
| PERF-004 | Lock timeout | 5 seconds |
| PERF-005 | Map point sampling threshold | 5,000 |
| PERF-006 | Table list limit | 100 |

### 4.3 Usability

| ID | Requirement |
|----|-------------|
| UX-001 | Minimal, clean interface without emojis |
| UX-002 | Light/dark theme support with proper contrast |
| UX-003 | Responsive layout (full-width) |
| UX-004 | Sidebar for connection, main area for content |
| UX-005 | Vertical layout: SQL Editor → Table → Chart → Map → Export |
| UX-006 | Loading spinners for async operations |
| UX-007 | Clear success/error messaging |

### 4.4 Compatibility

| ID | Requirement |
|----|-------------|
| COMP-001 | PostgreSQL database support |
| COMP-002 | Modern web browsers (Chrome, Firefox, Safari, Edge) |
| COMP-003 | Python 3.8+ runtime |
| COMP-004 | Cross-platform (Windows, macOS, Linux) |

---

## 5. Configuration Parameters

### 5.1 Application Constants

```python
MAX_ROWS = 10000           # Maximum rows returned from query
MAX_EXPORT_ROWS = 50000    # Maximum rows for Excel export
QUERY_TIMEOUT_MS = 30000   # Query timeout in milliseconds
```

### 5.2 Blocked SQL Patterns

```python
BLOCKED_SQL_PATTERNS = [
    r'\b(DROP|DELETE|TRUNCATE|UPDATE|INSERT|ALTER|CREATE|GRANT|REVOKE)\b',
    r'\b(EXECUTE|EXEC|CALL)\b',
    r';\s*\w',              # Multiple statements
    r'--',                  # SQL comments
    r'/\*',                 # Block comments
    r'\bpg_',               # PostgreSQL system functions
    r'\bINTO\s+OUTFILE\b',  # File operations
    r'\bLOAD_FILE\b',       # File operations
]
```

---

## 6. Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
├─────────────────────────────────────────────────────────────────┤
│  Sidebar              │  Main Content                           │
│  ┌─────────────────┐  │  ┌─────────────────────────────────────┐│
│  │ DB Connection   │  │  │ SQL Editor                          ││
│  │ - Host/Port     │  │  │ - Query Input                       ││
│  │ - Database      │  │  │ - Execute/Clear                     ││
│  │ - User/Pass     │──┼──│ - Results Summary                   ││
│  │ - Connect       │  │  └─────────────────────────────────────┘│
│  └─────────────────┘  │  ┌─────────────────────────────────────┐│
│  ┌─────────────────┐  │  │ Data Table                          ││
│  │ Table Browser   │  │  │ - Filters                           ││
│  │ - Table List    │  │  │ - Metrics                           ││
│  │ - Load Table    │  │  │ - Interactive Grid                  ││
│  └─────────────────┘  │  │ - Excel Export                      ││
│                       │  └─────────────────────────────────────┘│
│                       │  ┌─────────────────────────────────────┐│
│                       │  │ Chart                               ││
│                       │  │ - X/Y/Color Selection               ││
│                       │  │ - Line Chart                        ││
│                       │  └─────────────────────────────────────┘│
│                       │  ┌─────────────────────────────────────┐│
│                       │  │ Map                                 ││
│                       │  │ - Lat/Lon/Color Selection           ││
│                       │  │ - Scatter Map                       ││
│                       │  └─────────────────────────────────────┘│
│                       │  ┌─────────────────────────────────────┐│
│                       │  │ Export Report                       ││
│                       │  │ - Report Name/Description           ││
│                       │  │ - HTML Download                     ││
│                       │  └─────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Dependencies

### 7.1 Python Packages

| Package | Purpose |
|---------|---------|
| streamlit | Web application framework |
| pandas | Data manipulation and analysis |
| plotly | Interactive visualizations |
| pg8000 | PostgreSQL database driver |
| openpyxl | Excel file generation |

### 7.2 requirements.txt

```
streamlit
pandas
plotly
pg8000
openpyxl
```

---

## 8. File Structure

```
iot-query-probe/
├── app.py              # Single application file (all code)
├── requirements.txt    # Python dependencies
├── README.md           # User documentation
└── TECHNICAL_REQUIREMENTS.md  # This document
```

---

## 9. Error Handling

### 9.1 Error Sanitization
- Connection strings masked: `postgresql://***`
- Passwords masked: `password=***`
- Error messages truncated to 200 characters
- No stack traces exposed to users

### 9.2 User Feedback
- Success messages with green styling
- Error messages with red styling
- Loading spinners during operations
- Informational messages for guidance

---

## 10. Future Considerations

### 10.1 Potential Enhancements
- Additional chart types (bar, scatter, pie)
- Query history/favorites
- Multiple database connections
- Query result caching
- PDF export option
- Scheduled report generation

### 10.2 Out of Scope
- User authentication/authorization
- Multi-user session management
- Database write operations
- Real-time data streaming
- Mobile-specific UI

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | January 2026 | - | Initial release |

