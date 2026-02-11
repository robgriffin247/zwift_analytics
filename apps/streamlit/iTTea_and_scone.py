import os
import streamlit as st
import duckdb
import polars as pl


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

with duckdb.connect(database) as con:
    results = con.sql("select * from core.fct__ts_itt_club_spring_2026__results").pl()
    best_results = con.sql("select * from core.fct__ts_itt_club_spring_2026__best_results").pl()
    leaderboard = con.sql("select * from core.fct__ts_itt_club_spring_2026__leaderboard").pl()

st.header("iTTea & Scone")

tab_leaderboard, tab_results = st.tabs(["Leaderboard", "Results"])

with tab_leaderboard:
    c1, c2, c3 = st.columns([2,2,6])
    selected_cats = c1.selectbox("Category", options=["All", "B", "C", "D"])

    if selected_cats=="All":
        pass
    else:
        leaderboard = leaderboard.filter(pl.col("category").is_in([selected_cats]))

    leaderboard = leaderboard.with_columns(
        pl.int_range(1, pl.len() + 1).alias("rank")
    )

    st.dataframe(leaderboard[["rank", "rider", "category", "races", "total_time"]], 
        column_config={
            "rank":st.column_config.NumberColumn("Rank", width="small"),
            "rider":st.column_config.TextColumn("Rider"),
            "category":st.column_config.TextColumn("Cat.", width="small"),
            "races":st.column_config.NumberColumn("Races", width="small"),
            "total_time":st.column_config.TextColumn("Total Time", width="small"),
        },
    )



tab_results.dataframe(results[["stage", "stage_name", "event_start_datetime", "rider", "category", "race_speed", "race_time", "is_best_effort"]],
    column_config={
        "stage":st.column_config.NumberColumn("Stage"),
        "stage_name":st.column_config.TextColumn("Route"),
        "event_start_datetime":st.column_config.DatetimeColumn("Date/Time", format="D MMM, h:mm a"),
        "rider":st.column_config.TextColumn("Rider"),
        "category":st.column_config.TextColumn("Cat."),
        "race_speed":st.column_config.NumberColumn("Speed", format="%.2f"),
        "race_time":st.column_config.TextColumn("Time"),
        "is_best_effort":st.column_config.CheckboxColumn("Best"),
    }
)