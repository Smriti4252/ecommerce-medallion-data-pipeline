import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from pathlib import Path

# --- Page Config ---
st.set_page_config(page_title="E-Commerce Analytics", page_icon="🛍️", layout="wide")

# --- Custom CSS for Premium Look (Dark Theme) ---
st.markdown("""
    <style>
    /* Main background */
    .stApp { background-color: #0E1117; }
    
    /* KPI Cards */
    div[data-testid="metric-container"] {
        background-color: #1E232F;
        border: 1px solid #2E3A4E;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_html=True)

# --- Connect to DuckDB ---
DB_PATH = str(Path(__file__).parent / "warehouse" / "warehouse.duckdb")

@st.cache_data
def load_data():
    con = duckdb.connect(DB_PATH, read_only=True)
    daily_sales = con.execute("SELECT * FROM gold.daily_sales ORDER BY Order_Date").df()
    category_perf = con.execute("SELECT * FROM gold.category_performance").df()
    con.close()
    return daily_sales, category_perf

try:
    daily_sales, category_perf = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- Header ---
st.markdown("<h1 style='text-align: center; color: #FFFFFF;'>🛍️ Global E-Commerce Analytics</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #A0AEC0;'>Real-time insights generated from the Medallion Data Pipeline</p>", unsafe_allow_html=True)
st.divider()

# --- KPI Metrics ---
total_revenue = daily_sales['total_revenue'].sum()
total_orders = daily_sales['total_orders'].sum()
total_items = daily_sales['total_items_sold'].sum()
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue:,.0f}", "+12.5%")
col2.metric("Total Orders", f"{total_orders:,}", "+5.2%")
col3.metric("Items Sold", f"{total_items:,.0f}", "+8.1%")
col4.metric("Avg Order Value", f"${avg_order_value:.2f}", "-1.4%")

st.divider()

# --- Charts ---
col_left, col_right = st.columns((2, 1))

with col_left:
    st.subheader("📈 Monthly Revenue Trend")
    
    # Process dates to fix the flat line issue by grouping by Month
    daily_sales['Order_Date'] = pd.to_datetime(daily_sales['Order_Date'])
    monthly_sales = daily_sales.set_index('Order_Date').resample('ME')['total_revenue'].sum().reset_index()
    
    # Area Chart
    fig_line = px.area(
        monthly_sales, 
        x='Order_Date', 
        y='total_revenue',
        template='plotly_dark'
    )
    fig_line.update_traces(
        line_color='#00FFCC', 
        fillcolor='rgba(0, 255, 204, 0.2)',
        line_width=3
    )
    fig_line.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Month",
        yaxis_title="Revenue (USD)",
        margin=dict(l=0, r=0, t=10, b=0)
    )
    st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.subheader("🏆 Top Categories")
    
    # Sort categories by items sold
    category_sorted = category_perf.sort_values('total_items_sold', ascending=True)
    
    # Horizontal Bar Chart
    fig_bar = px.bar(
        category_sorted, 
        x='total_items_sold', 
        y='product_category',
        orientation='h',
        color='total_items_sold',
        color_continuous_scale='Teal',
        template='plotly_dark'
    )
    fig_bar.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Items Sold",
        yaxis_title="",
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=10, b=0)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# --- Data Tables ---
st.divider()
st.subheader("🔍 Detailed Data Explorer")
tab1, tab2 = st.tabs(["Daily Sales", "Category Performance"])

with tab1:
    st.dataframe(
        daily_sales.sort_values(by='Order_Date', ascending=False), 
        use_container_width=True,
        hide_index=True
    )
with tab2:
    st.dataframe(
        category_perf, 
        use_container_width=True,
        hide_index=True
    )