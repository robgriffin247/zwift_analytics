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

tab_leaderboard, tab_best_results, tab_results = st.tabs(["Leaderboard", "Best Efforts", "All Results"])

tab_leaderboard.dataframe(leaderboard[["rider", "category", "races", "total_time"]], 
    column_config={
        "rider":st.column_config.TextColumn("Rider"),
        "category":st.column_config.TextColumn("Cat."),
        "races":st.column_config.NumberColumn("Races"),
        "total_time":st.column_config.TextColumn("Total Time"),
    }
)

tab_best_results.dataframe(best_results[["stage", "stage_name", "event_start_datetime", "rider", "category", "race_speed", "race_time"]],
    column_config={
        "stage":st.column_config.NumberColumn("Stage"),
        "stage_name":st.column_config.TextColumn("Route"),
        "event_start_datetime":st.column_config.DatetimeColumn("Date/Time", format="D MMM, h:mm a"),
        "rider":st.column_config.TextColumn("Rider"),
        "category":st.column_config.TextColumn("Cat."),
        "race_speed":st.column_config.NumberColumn("Speed", format="%.2f"),
        "race_time":st.column_config.TextColumn("Time"),
    }
)

tab_results.dataframe(results[["stage", "stage_name", "event_start_datetime", "rider", "category", "race_speed", "race_time"]],
    column_config={
        "stage":st.column_config.NumberColumn("Stage"),
        "stage_name":st.column_config.TextColumn("Route"),
        "event_start_datetime":st.column_config.DatetimeColumn("Date/Time", format="D MMM, h:mm a"),
        "rider":st.column_config.TextColumn("Rider"),
        "category":st.column_config.TextColumn("Cat."),
        "race_speed":st.column_config.NumberColumn("Speed", format="%.2f"),
        "race_time":st.column_config.TextColumn("Time"),
    }
)