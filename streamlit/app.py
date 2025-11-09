import streamlit as st
import duckdb
import polars as pl
import os


@st.cache_data(
    ttl=24 * 3600,
    show_spinner="Getting data from the Watopian census...",
    show_time=True,
)
def get_dim_riders():
    with duckdb.connect(
        f"md:zwift_analytics",
        config={"motherduck_token": os.getenv("MOTHERDUCK_TOKEN")},
    ) as con:
        df = con.sql("select * from zwift_analytics.core.dim_riders order by velo_90_day_peak desc, ftp_watts").pl()
    return df


def format_riders_dataframe(container: st.container, riders: pl.DataFrame):
    container.dataframe(
        riders[
            [
                "rider_id",
                "rider",
                "club",
                "velo_90_day_peak",
                "velo_90_day_peak_category",
                "weight_kg",
                "ftp_watts",
                "ftp_watts_kg",
                "phenotype",
                "races",
                "race_win_rate",
                "race_podium_rate",
            ]
        ],
        column_config={
            "rider_id":st.column_config.NumberColumn("Rider ID", format="%.0f"),
            "rider":st.column_config.TextColumn("Rider"),
            "club":st.column_config.TextColumn("Club"),
            "velo_90_day_peak":st.column_config.NumberColumn("📈vELO", format="%0.1f"),
            "velo_90_day_peak_category":st.column_config.TextColumn("💎 Category"),
            "weight_kg":st.column_config.NumberColumn("KG", format="%0.1f"),
            "ftp_watts":st.column_config.NumberColumn("⚡FTP", format="%0.0f"),
            "ftp_watts_kg":st.column_config.NumberColumn("⚡FTP/KG", format="%0.2f"),
            "phenotype":st.column_config.TextColumn("Type"),
            "races":st.column_config.NumberColumn("🏁 Races", format="%0.0f"),
            "race_win_rate":st.column_config.NumberColumn("🥇Win %", format="%0.2f"),
            "race_podium_rate":st.column_config.NumberColumn("🥉Podium %", format="%0.2f"),
        }
    )


st.set_page_config(
    layout="wide",
    page_icon=":bicycle:",
    page_title="Zwift Analytics",
    menu_items={"Get Help": "mailto:robgriffin247@hotmail.com"},
)

# Layout
st.title("Zwift Analytics")
riders_dataframe = st.container()


# Backend
dim_riders = get_dim_riders()
format_riders_dataframe(riders_dataframe, dim_riders)
