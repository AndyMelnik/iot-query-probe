"""
IoT Query Probe - Minimalistic SQL Query Interface
Single-file application for PostgreSQL data exploration

Security features:
- SELECT-only queries (blocks DML/DDL)
- Query timeout limits
- Row limits to prevent memory exhaustion
- Sanitized error messages
- No credentials logging
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote, unquote, urlparse, parse_qs
import io
import html
import re
import copy
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
MAX_ROWS = 10000
MAX_EXPORT_ROWS = 50000
QUERY_TIMEOUT_MS = 30000

# Blocked SQL patterns (case-insensitive)
BLOCKED_SQL_PATTERNS = [
    r'\b(DROP|DELETE|TRUNCATE|UPDATE|INSERT|ALTER|CREATE|GRANT|REVOKE)\b',
    r'\b(EXECUTE|EXEC|CALL)\b',
    r';\s*\w',  # Multiple statements
    r'--',  # SQL comments (potential injection)
    r'/\*',  # Block comments
    r'\bpg_',  # PostgreSQL system functions
    r'\bINTO\s+OUTFILE\b',
    r'\bLOAD_FILE\b',
]

st.set_page_config(
    page_title="IoT Query Probe",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal CSS with contrast support for light/dark themes
st.markdown("""
<style>
    .main .block-container { padding: 1rem 2rem; max-width: 100%; }
    h1, h2, h3 { font-weight: 500; margin-bottom: 0.5rem; }
    .stTextArea textarea { font-family: 'Consolas', 'Monaco', monospace; font-size: 13px; }
    hr { margin: 1.5rem 0; opacity: 0.3; }
    
    /* Light theme */
    @media (prefers-color-scheme: light) {
        .success-msg { background: #d4edda; border-left: 3px solid #28a745; padding: 10px 15px; margin: 10px 0; color: #155724; }
        .error-msg { background: #f8d7da; border-left: 3px solid #dc3545; padding: 10px 15px; margin: 10px 0; color: #721c24; }
    }
    
    /* Dark theme */
    @media (prefers-color-scheme: dark) {
        .success-msg { background: #1e3a29; border-left: 3px solid #28a745; padding: 10px 15px; margin: 10px 0; color: #a3d9b1; }
        .error-msg { background: #3d1f1f; border-left: 3px solid #dc3545; padding: 10px 15px; margin: 10px 0; color: #f5a5a5; }
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SECURITY FUNCTIONS
# =============================================================================
def validate_query(query: str) -> tuple[bool, str]:
    """
    Validate SQL query for security.
    Only allows SELECT queries, blocks dangerous patterns.
    
    Returns: (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, "Query cannot be empty"
    
    # Normalize query
    normalized = query.strip().upper()
    
    # Must start with SELECT or WITH (for CTEs)
    if not (normalized.startswith('SELECT') or normalized.startswith('WITH')):
        return False, "Only SELECT queries are allowed"
    
    # Check for blocked patterns
    for pattern in BLOCKED_SQL_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return False, "Query contains blocked SQL pattern"
    
    return True, ""


def sanitize_error(error: Exception) -> str:
    """Sanitize error message to avoid leaking sensitive information."""
    error_str = str(error)
    
    # Remove potential connection string details
    error_str = re.sub(r'postgresql://[^\s]+', 'postgresql://***', error_str)
    error_str = re.sub(r'password[=:][^\s,]+', 'password=***', error_str, flags=re.IGNORECASE)
    
    # Truncate long errors
    if len(error_str) > 200:
        error_str = error_str[:200] + "..."
    
    return error_str


# =============================================================================
# DATABASE CONNECTION
# =============================================================================
def build_connection_string(host: str, port: str, database: str, user: str, password: str) -> str:
    """Build PostgreSQL connection string from individual components."""
    # Validate inputs
    if not all([host, port, database, user, password]):
        return ""
    
    # Basic input validation
    if not re.match(r'^[\w\.\-]+$', host):
        return ""
    if not port.isdigit():
        return ""
    
    # URL-encode user and password to handle special characters like <, >, ^, etc.
    encoded_user = quote(user, safe='')
    encoded_password = quote(password, safe='')
    return f"postgresql://{encoded_user}:{encoded_password}@{host}:{port}/{database}?sslmode=require"


def get_connection(db_url: str):
    """Create database connection with pg8000."""
    import pg8000.native
    import ssl
    
    parsed = urlparse(db_url)
    params = parse_qs(parsed.query)
    
    # Decode URL-encoded username and password (handles special chars like <, >, ^, etc.)
    username = unquote(parsed.username) if parsed.username else None
    password = unquote(parsed.password) if parsed.password else None
    
    # SSL configuration
    ssl_context = None
    sslmode = params.get('sslmode', ['prefer'])[0]
    if sslmode in ('require', 'verify-ca', 'verify-full', 'prefer'):
        ssl_context = ssl.create_default_context()
        if sslmode in ('require', 'prefer'):
            # For require/prefer, we accept any certificate
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
    
    return pg8000.native.Connection(
        user=username,
        password=password,
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip('/'),
        ssl_context=ssl_context,
        timeout=QUERY_TIMEOUT_MS // 1000
    )


def execute_query(db_url: str, query: str) -> pd.DataFrame:
    """Execute SQL query and return DataFrame."""
    # Validate query first
    is_valid, error_msg = validate_query(query)
    if not is_valid:
        raise ValueError(error_msg)
    
    conn = get_connection(db_url)
    try:
        # Set statement timeout for safety
        conn.run(f"SET statement_timeout = '{QUERY_TIMEOUT_MS}'")
        conn.run("SET lock_timeout = '5000'")
        
        result = conn.run(query)
        columns = [col['name'] for col in conn.columns] if conn.columns else []
        
        if result and columns:
            df = pd.DataFrame(result, columns=columns)
            return df.head(MAX_ROWS)
        return pd.DataFrame()
    finally:
        conn.close()


def get_tables(db_url: str) -> list:
    """Get list of available tables."""
    query = """
        SELECT table_schema || '.' || table_name as full_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name
        LIMIT 100
    """
    try:
        df = execute_query(db_url, query)
        return df['full_name'].tolist() if not df.empty else []
    except Exception:
        return []


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================
def generate_excel(df: pd.DataFrame) -> bytes:
    """Generate Excel file from DataFrame."""
    output = io.BytesIO()
    export_df = df.head(MAX_EXPORT_ROWS).copy()
    
    # Fix timezone-aware datetimes (Excel doesn't support them)
    for col in export_df.columns:
        if pd.api.types.is_datetime64_any_dtype(export_df[col]):
            if export_df[col].dt.tz is not None:
                export_df[col] = export_df[col].dt.tz_localize(None)
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Data')
    
    return output.getvalue()


def generate_html_report(df: pd.DataFrame, chart_fig=None, map_fig=None, 
                         report_name: str = "Data Report", description: str = "") -> str:
    """Generate minimal print-friendly HTML report."""
    
    def escape(text):
        return html.escape(str(text))
    
    # Build table HTML
    table_rows = []
    table_rows.append('<tr>' + ''.join(f'<th>{escape(c)}</th>' for c in df.columns) + '</tr>')
    for _, row in df.head(500).iterrows():
        table_rows.append('<tr>' + ''.join(f'<td>{escape(v)}</td>' for v in row) + '</tr>')
    
    table_html = f'<table>{"".join(table_rows)}</table>'
    
    # Chart HTML
    chart_html = ""
    if chart_fig:
        fig_dict = copy.deepcopy(chart_fig.to_dict())
        chart_fig_print = go.Figure(fig_dict)
        chart_fig_print.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='black'),
            title_font=dict(color='black'),
            xaxis=dict(color='black', gridcolor='#ddd', linecolor='#333'),
            yaxis=dict(color='black', gridcolor='#ddd', linecolor='#333'),
            legend=dict(font=dict(color='black'))
        )
        chart_html = f'<div class="section section-chart"><h2>Chart</h2>{chart_fig_print.to_html(full_html=False, include_plotlyjs="cdn")}</div>'
    
    # Map HTML - use original map with light style
    map_html = ""
    if map_fig:
        map_fig.update_layout(
            mapbox_style="carto-positron",
            paper_bgcolor='white'
        )
        map_html = f'<div class="section section-map"><h2>Map</h2>{map_fig.to_html(full_html=False, include_plotlyjs="cdn")}</div>'
    
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    
    desc_html = ""
    if description:
        desc_html = f'<div class="description">{escape(description)}</div>'
    
    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{escape(report_name)}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
            font-size: 11px; 
            padding: 15px; 
            margin: 0;
            background: #fff; 
            color: #000; 
        }}
        h1 {{ font-size: 16px; margin: 0 0 5px 0; }}
        h2 {{ font-size: 13px; margin: 10px 0 8px 0; padding-bottom: 5px; border-bottom: 1px solid #ddd; }}
        .header {{ page-break-after: avoid; }}
        .meta {{ color: #333; margin-bottom: 5px; }}
        .description {{ margin-bottom: 10px; padding: 8px; background: #f9f9f9; border-left: 3px solid #ddd; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
        th, td {{ padding: 4px 6px; border: 1px solid #ddd; text-align: left; }}
        th {{ background: #f5f5f5; font-weight: 600; }}
        tr:nth-child(even) {{ background: #fafafa; }}
        thead {{ display: table-header-group; }}
        tr {{ page-break-inside: avoid; }}
        .section {{ margin: 15px 0; }}
        .section-chart, .section-map {{ page-break-inside: avoid; page-break-before: auto; }}
        @media print {{
            body {{ font-size: 9px; padding: 0; }}
            table {{ font-size: 8px; }}
            .header {{ page-break-after: avoid; }}
            h2 {{ page-break-after: avoid; }}
        }}
        @page {{ margin: 1cm; size: A4 landscape; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{escape(report_name)}</h1>
        <div class="meta">Generated: {timestamp} | Rows: {len(df):,}</div>
        {desc_html}
    </div>
    <div class="section"><h2>Data</h2>{table_html}</div>
    {chart_html}
    {map_html}
</body>
</html>'''


# =============================================================================
# SIDEBAR - DATABASE CONNECTION
# =============================================================================
def render_sidebar():
    """Render sidebar with database connection options."""
    with st.sidebar:
        st.markdown("### Database Connection")
        
        use_url = st.checkbox("Use connection URL", value=False, key="use_url_checkbox")
        
        if use_url:
            db_url = st.text_input(
                "Connection URL",
                type="password",
                placeholder="postgresql://user:pass@host:5432/dbname",
                help="PostgreSQL connection string",
                key="db_url_input"
            )
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                host = st.text_input("Host", placeholder="db.example.com", key="host_input")
            with col2:
                port = st.text_input("Port", value="5432", key="port_input")
            
            database = st.text_input("Database", placeholder="database_name", key="database_input")
            user = st.text_input("User", placeholder="username", key="user_input")
            password = st.text_input("Password", type="password", key="password_input")
            
            if host and database and user and password:
                db_url = build_connection_string(host, port, database, user, password)
            else:
                db_url = ""
        
        if st.button("Connect", type="primary", disabled=not db_url):
            with st.spinner("Connecting..."):
                try:
                    tables = get_tables(db_url)
                    st.session_state["db_url"] = db_url
                    st.session_state["tables"] = tables
                    st.session_state["connected"] = True
                    st.success("Connected")
                except Exception as e:
                    st.error(f"Connection failed: {sanitize_error(e)}")
                    st.session_state["connected"] = False
        
        if st.session_state.get("connected") and st.session_state.get("tables"):
            st.markdown("---")
            st.markdown("### Tables")
            
            tables = st.session_state.get("tables", [])
            selected_table = st.selectbox(
                "Select table",
                options=[""] + tables,
                format_func=lambda x: x if x else "-- Select --"
            )
            
            if selected_table and st.button("Load table"):
                st.session_state["sql_query"] = f"SELECT * FROM {selected_table} LIMIT 100;"
                st.rerun()
        
        if st.session_state.get("connected"):
            st.markdown("---")
            if st.button("Disconnect"):
                st.session_state["connected"] = False
                st.session_state["db_url"] = ""
                st.session_state["tables"] = []
                st.session_state["query_result"] = None
                st.rerun()


# =============================================================================
# MAIN CONTENT
# =============================================================================
def render_sql_editor():
    """Render SQL query editor."""
    st.markdown("## SQL Editor")
    
    if not st.session_state.get("connected"):
        st.info("Connect to a database using the sidebar.")
        return
    
    default_query = st.session_state.get("sql_query", "SELECT * FROM table_name LIMIT 100;")
    
    query = st.text_area(
        "Query",
        value=default_query,
        height=120,
        key="sql_input",
        label_visibility="collapsed"
    )
    
    # Security notice
    st.caption("Only SELECT queries are allowed. DML/DDL statements are blocked.")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        execute_btn = st.button("Execute", type="primary")
    with col2:
        if st.button("Clear"):
            st.session_state["query_result"] = None
            st.session_state["sql_query"] = ""
            st.rerun()
    
    if execute_btn and query:
        with st.spinner("Executing..."):
            try:
                db_url = st.session_state.get("db_url")
                start_time = datetime.now()
                df = execute_query(db_url, query)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                st.session_state["query_result"] = df
                st.session_state["sql_query"] = query
                
                st.markdown(f"""
                <div class="success-msg">
                    Query executed successfully. 
                    Rows: {len(df):,} | Columns: {len(df.columns)} | Time: {duration:.0f}ms
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.markdown(f"""
                <div class="error-msg">
                    Error: {sanitize_error(e)}
                </div>
                """, unsafe_allow_html=True)


def render_data_table():
    """Render data table with Excel export."""
    df = st.session_state.get("query_result")
    
    if df is None or df.empty:
        return
    
    st.markdown("---")
    st.markdown("## Data Table")
    
    with st.expander("Filters"):
        filter_cols = st.multiselect("Filter columns", options=df.columns.tolist())
        filters = {}
        for col in filter_cols:
            unique_vals = df[col].dropna().unique().tolist()[:50]
            selected = st.multiselect(f"{col}", unique_vals, key=f"filter_{col}")
            if selected:
                filters[col] = selected
    
    filtered_df = df.copy()
    for col, vals in filters.items():
        filtered_df = filtered_df[filtered_df[col].isin(vals)]
    
    st.session_state["filtered_df"] = filtered_df
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", f"{len(filtered_df):,}")
    col2.metric("Columns", len(filtered_df.columns))
    col3.metric("Filtered", "Yes" if filters else "No")
    
    st.dataframe(filtered_df, use_container_width=True, height=400)
    
    excel_data = generate_excel(filtered_df)
    st.download_button(
        label="Download Excel",
        data=excel_data,
        file_name=f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def render_chart():
    """Render chart section."""
    df = st.session_state.get("filtered_df")
    
    if df is None or df.empty:
        return
    
    st.markdown("---")
    st.markdown("## Chart")
    
    all_cols = df.columns.tolist()
    
    if not all_cols:
        st.info("No columns available for charting.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        x_axis = st.selectbox("X-axis", options=all_cols, key="chart_x")
    with col2:
        y_axis = st.selectbox("Y-axis", options=all_cols, key="chart_y")
    with col3:
        color_by = st.selectbox("Color by", options=["None"] + all_cols, key="chart_color")
    
    if st.button("Generate Chart"):
        try:
            color = None if color_by == "None" else color_by
            fig = px.line(
                df,
                x=x_axis,
                y=y_axis,
                color=color,
                title=f"{y_axis} over {x_axis}",
                template="plotly_white"
            )
            fig.update_layout(
                margin=dict(l=40, r=40, t=40, b=40)
            )
            st.session_state["current_chart"] = fig
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart error: {sanitize_error(e)}")
    
    elif "current_chart" in st.session_state:
        st.plotly_chart(st.session_state["current_chart"], use_container_width=True)


def calculate_map_zoom(lat_min, lat_max, lon_min, lon_max):
    """Calculate appropriate zoom level based on coordinate bounds."""
    lat_span = lat_max - lat_min
    lon_span = lon_max - lon_min
    max_span = max(lat_span, lon_span)
    
    if max_span > 100:
        return 1
    elif max_span > 50:
        return 2
    elif max_span > 20:
        return 3
    elif max_span > 10:
        return 4
    elif max_span > 5:
        return 5
    elif max_span > 2:
        return 6
    elif max_span > 1:
        return 7
    elif max_span > 0.5:
        return 8
    elif max_span > 0.2:
        return 9
    elif max_span > 0.1:
        return 10
    elif max_span > 0.05:
        return 11
    elif max_span > 0.01:
        return 12
    else:
        return 13


def render_map():
    """Render map section."""
    df = st.session_state.get("filtered_df")
    
    if df is None or df.empty:
        return
    
    st.markdown("---")
    st.markdown("## Map")
    
    all_cols = df.columns.tolist()
    
    lat_patterns = ['lat', 'latitude', 'y']
    lon_patterns = ['lon', 'lng', 'longitude', 'x']
    
    detected_lat = next((c for c in all_cols if any(p in c.lower() for p in lat_patterns)), all_cols[0] if all_cols else None)
    detected_lon = next((c for c in all_cols if any(p in c.lower() for p in lon_patterns)), all_cols[0] if all_cols else None)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        lat_idx = all_cols.index(detected_lat) if detected_lat in all_cols else 0
        lat_col = st.selectbox("Latitude", options=all_cols, index=lat_idx, key="map_lat")
    with col2:
        lon_idx = all_cols.index(detected_lon) if detected_lon in all_cols else 0
        lon_col = st.selectbox("Longitude", options=all_cols, index=lon_idx, key="map_lon")
    with col3:
        color_col = st.selectbox("Color by", options=["None"] + all_cols, key="map_color")
    
    if st.button("Generate Map"):
        try:
            map_df = df.copy()
            map_df[lat_col] = pd.to_numeric(map_df[lat_col], errors='coerce')
            map_df[lon_col] = pd.to_numeric(map_df[lon_col], errors='coerce')
            map_df = map_df.dropna(subset=[lat_col, lon_col])
            
            if len(map_df) > 5000:
                map_df = map_df.sample(n=5000, random_state=42)
                st.warning("Sampled to 5,000 points for performance.")
            
            if len(map_df) == 0:
                st.warning("No valid coordinates found.")
                return
            
            lat_min, lat_max = map_df[lat_col].min(), map_df[lat_col].max()
            lon_min, lon_max = map_df[lon_col].min(), map_df[lon_col].max()
            
            center_lat = (lat_min + lat_max) / 2
            center_lon = (lon_min + lon_max) / 2
            
            zoom = calculate_map_zoom(lat_min, lat_max, lon_min, lon_max)
            
            color = None if color_col == "None" else color_col
            fig = px.scatter_mapbox(
                map_df,
                lat=lat_col,
                lon=lon_col,
                color=color,
                zoom=zoom,
                center={"lat": center_lat, "lon": center_lon},
                height=500,
                mapbox_style="carto-positron"
            )
            
            if color:
                fig.update_layout(
                    margin={"r": 0, "t": 30, "l": 0, "b": 0},
                    legend=dict(
                        title=dict(text=color_col, font=dict(size=12, color="#333")),
                        font=dict(size=11, color="#333"),
                        bgcolor="rgba(255, 255, 255, 0.9)",
                        bordercolor="#ccc",
                        borderwidth=1,
                        orientation="v",
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01,
                        itemsizing="constant"
                    ),
                    showlegend=True
                )
            else:
                fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            
            st.session_state["current_map"] = fig
            st.plotly_chart(fig, use_container_width=True)
            
            if color:
                unique_values = map_df[color_col].dropna().unique()
                if len(unique_values) <= 20:
                    st.caption(f"Legend: {color_col} ({len(unique_values)} categories)")
            
        except Exception as e:
            st.error(f"Map error: {sanitize_error(e)}")
    
    elif "current_map" in st.session_state:
        st.plotly_chart(st.session_state["current_map"], use_container_width=True)


def render_html_export():
    """Render HTML report export button at the bottom."""
    df = st.session_state.get("filtered_df")
    
    if df is None or df.empty:
        return
    
    st.markdown("---")
    st.markdown("## Export Report")
    
    col1, col2 = st.columns(2)
    with col1:
        report_name = st.text_input(
            "Report Name",
            value=st.session_state.get("report_name_value", "Data Report"),
            key="report_name_input",
            placeholder="Enter report title"
        )
        # Store in session state to persist
        st.session_state["report_name_value"] = report_name
    with col2:
        report_desc = st.text_input(
            "Description (optional)",
            value=st.session_state.get("report_desc_value", ""),
            key="report_desc_input",
            placeholder="Brief description of the report"
        )
        st.session_state["report_desc_value"] = report_desc
    
    # Use the entered report name (with fallback)
    final_report_name = report_name.strip() if report_name and report_name.strip() else "Data Report"
    
    chart_fig = st.session_state.get("current_chart")
    map_fig = st.session_state.get("current_map")
    
    # Generate safe filename from report name
    safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in final_report_name)
    safe_filename = safe_filename.strip().replace(' ', '_')[:50] or "report"
    
    # Prepare final values
    final_description = report_desc.strip() if report_desc else ""
    
    html_report = generate_html_report(
        df, 
        chart_fig, 
        map_fig, 
        report_name=final_report_name,
        description=final_description
    )
    
    # Show preview of what will be in the report
    preview_text = f"Report title: **{final_report_name}**"
    if final_description:
        preview_text += f" | Description: _{final_description[:50]}{'...' if len(final_description) > 50 else ''}_"
    preview_text += f" | File: {safe_filename}_{datetime.now().strftime('%Y%m%d')}.html"
    st.caption(preview_text)
    
    st.download_button(
        label="Download HTML Report",
        data=html_report,
        file_name=f"{safe_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        mime="text/html"
    )
    
    st.caption("Report includes: Data table, Chart (if generated), Map (if generated). Optimized for printing.")


# =============================================================================
# MAIN
# =============================================================================
def main():
    st.markdown("# IoT Query Probe")
    
    if "connected" not in st.session_state:
        st.session_state["connected"] = False
    
    render_sidebar()
    render_sql_editor()
    render_data_table()
    render_chart()
    render_map()
    render_html_export()


if __name__ == "__main__":
    main()
