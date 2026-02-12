import os
import streamlit as st
import duckdb
import polars as pl


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
        
        p {
            font-size: 16px !important
        }
        
        .stMetric:hover {
            font-size: 0
            padding: 15px;
            border-radius: 5px;
        }
</style>
"""
)

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
    unique_riders = results[["rider"]].unique().sort(by=pl.col("rider"))["rider"].to_list()
    unique_cats = results[["category"]].unique().sort(by=pl.col("category"))["category"].to_list()
    unique_stages = results[["stage"]].unique().sort(by=pl.col("stage"))["stage"].to_list()

st.header("iTTea & Scone")

tab_leaderboard, tab_results = st.tabs(["Leaderboard", "Results"])

with tab_leaderboard:
    
    st.markdown("##### The Sausage-Roll of Honour, sponsored by Greggs")
    cols = st.columns(len(unique_cats), border=True)
    for i, cat in enumerate(unique_cats):
        with cols[i]:
            st.markdown(
                f"""
                ###### {cat} Cat 🏆
                ##### {leaderboard.filter(pl.col("category")==cat)["rider"].to_list()[0]}
                """
            )
            st.write("")

    st.markdown("##### Current Leaderboard")
    leaderboard = leaderboard.with_columns(
        pl.int_range(1, pl.len() + 1).alias("rank")
    )

    st.dataframe(leaderboard[["rank", "rider", "category", "velo_first", "velo_first_category", "races", "total_time", "gap"]], 
        column_config={
            "rank":st.column_config.NumberColumn("Rank", width="small"),
            "rider":st.column_config.TextColumn("Rider"),
            "category":st.column_config.TextColumn("Cat.", width="small"),
            "velo_first":st.column_config.NumberColumn("Velo", format="%.1f"),
            "velo_first_category":st.column_config.TextColumn("Velo Cat."),
            "races":st.column_config.NumberColumn("Races", width="small"),
            "total_time":st.column_config.TextColumn("Total Time", width="small"),
            "gap":st.column_config.TextColumn("Gap", width="small"),
        },
    )


with tab_results:
    
    c1, c2, c3 = st.columns([5,2,2], vertical_alignment="bottom")
    selected_rider = c1.selectbox("Rider", options=["All"] + unique_riders)
    selected_stage = c2.selectbox("Stage", options=["All"] + unique_stages)
    only_show_best_efforts = c3.toggle("Bests Only", value=False)

    if selected_rider=="All":
        pass
    else:
        results = results.filter(pl.col("rider").is_in([selected_rider]))
    
    if selected_stage=="All":
        pass
    else:
        results = results.filter(pl.col("stage").is_in([selected_stage]))
    
    if not only_show_best_efforts:
        pass
    else:
        results = results.filter(pl.col("is_best_effort")==True)

    st.dataframe(results[["stage", "stage_name", "event_start_epoch", "rider", "category", "race_speed", "race_time", "is_best_effort"]],
        column_config={
            "stage":st.column_config.NumberColumn("Stage"),
            "stage_name":st.column_config.TextColumn("Route"),
            "event_start_epoch":st.column_config.DatetimeColumn("Date/Time", format="D MMM, h:mm a"),
            "rider":st.column_config.TextColumn("Rider"),
            "category":st.column_config.TextColumn("Cat."),
            "race_speed":st.column_config.NumberColumn("Speed", format="%.2f"),
            "race_time":st.column_config.TextColumn("Time"),
            "is_best_effort":st.column_config.CheckboxColumn("Best"),
        }
    )