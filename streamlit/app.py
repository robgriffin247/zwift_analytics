import streamlit as st
import duckdb
import polars as pl
import os
import re

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
        df = con.sql(
            "select * from zwift_analytics.core.dim_riders order by velo_90_day_peak desc, ftp_watts"
        ).pl()
    return df


def format_riders_dataframe(container: st.container, riders: pl.DataFrame):
    columns = [ "rider",
                "club",
                "velo_90_day_peak",
                "velo_90_day_peak_category_short",
                "weight_kg",
                "watts_5s",
                "watts_kg_5s",
                "watts_120s",
                "watts_kg_120s",
                "ftp_watts",
                "ftp_watts_kg",
                "phenotype",
                "races",
                "race_win_rate",
                "race_podium_rate", ]
    
    if "team" in riders.columns:
        columns = ["team"] + columns

    container.dataframe(
        riders[columns],
        column_config={
            "rider_id": st.column_config.NumberColumn("Rider ID", format="%.0f"),
            "team": st.column_config.NumberColumn("Team", pinned=True, format="%.0f", width=48),
            "rider": st.column_config.TextColumn("Rider", pinned=True, width=175),
            "club": st.column_config.TextColumn("Club", width=64),
            "velo_90_day_peak": st.column_config.NumberColumn("📈vELO", format="%0.1f", width=64),
            "velo_90_day_peak_category_short": st.column_config.TextColumn("💎", width=64),
            "weight_kg": st.column_config.NumberColumn("kg", format="%0.1f", width=64),
            "watts_5s": st.column_config.NumberColumn("⚡5s W", format="%0.0f", width=64),
            "watts_kg_5s": st.column_config.NumberColumn("/kg", format="%0.2f", width=48),
            "watts_120s": st.column_config.NumberColumn("⚡2m W", format="%0.0f", width=64),
            "watts_kg_120s": st.column_config.NumberColumn("/kg", format="%0.2f", width=48),
            "ftp_watts": st.column_config.NumberColumn("⚡FTP W", format="%0.0f", width=64),
            "ftp_watts_kg": st.column_config.NumberColumn("/kg", format="%0.2f", width=48),
            "phenotype": st.column_config.TextColumn("Type", width=90),
            "races": st.column_config.NumberColumn("🏁", format="%0.0f", width=64),
            "race_win_rate": st.column_config.NumberColumn("🥇%", format="%0.0f", width=64),
            "race_podium_rate": st.column_config.NumberColumn(
                "🥉%", format="%0.0f", width=64
            ),
        },
    )


def select_riders(container: st.container, options: list[str], team: int, bulk_select=False):

    if bulk_select:
        input_string = container.text_input(
            f"Team {team} Riders",
            key=f"selected_riders_team_{team}_input_string",
            placeholder="Paste in IDs, URLs and more..." if team==1 else "All numbers will convert to IDs!"
        )

        input_ids = [int(s) for s in re.findall(r"\d+", input_string)]

        st.session_state[f"selected_riders_team_{team}"] = dim_riders.filter(pl.col("rider_id").is_in(input_ids)).with_columns(pl.lit(team).alias("team"))
    
    else:
        container.multiselect(
            f"Team {team} Riders",
            options=options,
            max_selections=5,
            key=f"selected_riders_team_{team}_rider_strings",
        )

        st.session_state[f"selected_riders_team_{team}"] = dim_riders.filter(
            pl.col("rider_search_string").is_in(
                st.session_state[f"selected_riders_team_{team}_rider_strings"]
            )
        ).with_columns(pl.lit(team).alias("team"))
    


st.set_page_config(
    layout="wide",
    page_icon=":bicycle:",
    page_title="Zwift Analytics",
    menu_items={"Get Help": "mailto:robgriffin247@hotmail.com"},
)

# Layout
_0, main, _1 = st.columns([2,7,2])
with main:
    st.title("Zwift Analytics")
    st.html("<br/>")
    rider_input_1, rider_input_2, bulk_select_toggle = st.columns([5,5,2], gap="large", vertical_alignment="bottom")
    st.html("<br/>")
    riders_dataframe = st.container()

# Backend
dim_riders = get_dim_riders()

unique_riders = (
        dim_riders[["rider_search_string"]]
        .unique()
        .sort(pl.col("rider_search_string"))["rider_search_string"]
        .to_list()
    )

with bulk_select_toggle:
    st.toggle("Bulk Select", key="bulk_select")


select_riders(rider_input_1, unique_riders, 1, bulk_select=st.session_state["bulk_select"])
select_riders(rider_input_2, unique_riders, 2, bulk_select=st.session_state["bulk_select"])

selected_riders = pl.concat([st.session_state["selected_riders_team_1"], st.session_state["selected_riders_team_2"]])
 

format_riders_dataframe(riders_dataframe, selected_riders if selected_riders.shape[0]>0 else dim_riders)
