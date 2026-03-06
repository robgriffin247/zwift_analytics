import streamlit as st 
import os
import duckdb

def spacer(n=2):
    for i in range(n+1):
        st.write("")


def page_setup(title, icon):
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

    st.set_page_config(page_title="Zwift TT Club Racing - Unofficial", page_icon=":bicycle:")


def load_data(cache_data_hours=1):
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


    @st.cache_data(
        ttl= cache_data_hours * 60 * 60,
        max_entries=10,
        show_spinner="Loading data from database",
    )
    def _load():
        con = get_db_connection()
        results = con.sql("select * from core.obt_aaaa_zwift_tt_club").pl()

        return results

    return _load()
