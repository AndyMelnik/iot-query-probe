import streamlit as st
import pandas as pd
import pg8000
import plotly.express as px

# Function to connect to the database
def connect_to_db(host, dbname, user, password, port):
    try:
        conn = pg8000.connect(
            host=host,
            database=dbname,
            user=user,
            password=password,
            port=int(port)
        )
        return conn
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

# Function to check if the connection is still alive
def check_connection(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        return True
    except:
        return False

# UI for database connection
st.title("PTL Database Explorer")

with st.sidebar:
    st.header("Database Connection")
    host = st.text_input("Host", value="hostname")
    dbname = st.text_input("Database Name", value="client_XXXXXXX")
    user = st.text_input("Username", value="client_XXXXXXX_user")
    password = st.text_input("Password", type="password")
    port = st.text_input("Port", value="5432")
    connect_button = st.button("Connect")

    if connect_button:
        conn = connect_to_db(host, dbname, user, password, port)
        if conn:
            st.session_state["conn"] = conn
            st.success("Connection established successfully!")
        else:
            st.session_state["conn"] = None

    conn = st.session_state.get("conn", None)
    if conn and check_connection(conn):
        st.success("Status: Connected")
    elif conn:
        st.error("Status: Disconnected")
        st.session_state.pop("conn")
        conn = None
    else:
        st.warning("Status: Not connected")

    # Show tables from specific schemas if connected
    if conn:
        try:
            schemas = ['raw_business_data', 'raw_telematics_data']
            for schema in schemas:
                query = f"""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = '{schema}';
                    """
                df_schema = pd.read_sql(query, conn)
                st.subheader(f"Tables in {schema} schema")
                st.write(df_schema)
        except Exception as e:
            st.error(f"Error retrieving tables: {e}")

# Main content: SQL query execution and plotting
if "conn" in st.session_state and st.session_state["conn"]:
    conn = st.session_state["conn"]

    st.subheader("SQL Query Execution")
    sql_query = st.text_area("Enter SQL Query", "SELECT object_label FROM raw_business_data.objects LIMIT 1000;")
    execute_button = st.button("Execute")

    if execute_button:
        try:
            df = pd.read_sql(sql_query, conn)
            st.session_state["df"] = df
            st.dataframe(df)
        except Exception as e:
            st.error(f"Query execution error: {e}")

    if "df" in st.session_state:
        df = st.session_state["df"]
        if not df.empty:
            st.subheader("Plot Data")

            # Optional filtering widgets
            st.markdown("**Optional Filters:**")
            filter_columns = st.multiselect("Select columns to filter by", df.columns)
            filters = {}
            for col in filter_columns:
                unique_vals = df[col].dropna().unique()
                selected_vals = st.multiselect(f"Filter values for {col}", unique_vals)
                if selected_vals:
                    filters[col] = selected_vals

            # Apply filters
            filtered_df = df.copy()
            for col, vals in filters.items():
                filtered_df = filtered_df[filtered_df[col].isin(vals)]

            x_axis = st.selectbox("Select X-axis", filtered_df.columns, key="x_axis")
            y_axis = st.selectbox("Select Y-axis", filtered_df.columns, key="y_axis")

            color_by = None
            if filters:
                color_by = st.selectbox("Color by (based on selected filters)", list(filters.keys()))

            plot_button = st.button("Plot it!")

            if plot_button:
                fig = px.line(filtered_df, x=x_axis, y=y_axis, color=color_by, title="Line Chart")
                st.plotly_chart(fig)
