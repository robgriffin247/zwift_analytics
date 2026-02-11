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
    leaderboard = con.sql("select * from core.fct__ts_itt_club_spring_2026__leaderboard").pl()


tab_leaderboard, tab_results = st.tabs(["Leaderboard", "Results"])

tab_leaderboard.dataframe(leaderboard[["rider", "category", "races", "total_time"]], 
    column_config={
        "rider":st.column_config.TextColumn("Rider"),
        "category":st.column_config.TextColumn("Cat."),
        "races":st.column_config.NumberColumn("Races"),
        "total_time":st.column_config.TextColumn("Total Time"),
    }
)

tab_results.dataframe(results[["event", "event_start_epoch", "rider", "category", "race_speed", "race_time"]])