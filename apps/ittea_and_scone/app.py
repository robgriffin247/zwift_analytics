import os
import streamlit as st
import duckdb
import polars as pl


# Page Setup
st.html(
    """
<style>
        .stMainBlockContainer, stVerticalBlock {
            width: 95% !important;
            max-width: 950px !important;
        }

        .stMetric {
            font-size: 0
            padding: 15px;
            border-radius: 5px;
        }
        
        .stMetric:hover {
            font-size: 0
            padding: 15px;
            border-radius: 5px;
        }
</style>
"""
)


st.set_page_config(page_title="iTTea & Scone", page_icon=":tea:")

main_page = st.Page("pages/main.py", title="Home", icon="🏆")
data_input_page = st.Page("pages/data_input.py", title="Add Events", icon=":material/add_circle:")

st.header("iTTea & Scone")


# Data load
target = os.getenv("TARGET")
motherduck_token = os.getenv("MOTHERDUCK_TOKEN")

if target=="prod":
    database = f"md:zwift_analytics_prod?motherduck_token={motherduck_token}"
elif target=="test":
    database = f"md:zwift_analytics_test?motherduck_token={motherduck_token}"
elif target=="dev":
    database = "data/zwift_analytics_dev.duckdb"
else:
    raise ValueError(f"Invalid TARGET value in environment; expected 'prod', 'test' or 'dev', got '{target}'")

@st.cache_resource(show_spinner="Establishing database connection")
def get_db_connection():
    return duckdb.connect(database, read_only=False)

cache_data_hours = 0.25

@st.cache_data(
    ttl= cache_data_hours * 60 * 60,
    max_entries=10,
    show_spinner="Loading data from database",
)
def load_data():
    con = get_db_connection()
    results = con.sql("select * from core.obt_aaab_ittea_and_scone").pl()

    return results

if "results" not in st.session_state:
    st.session_state["results"] = load_data()

results = st.session_state["results"]

# Run pages
pg = st.navigation([main_page, data_input_page])
pg.run()
