import streamlit as st
import duckdb
import os
import sys
from pathlib import Path

import polars as pl

# Ensure repo root is on sys.path for Streamlit Cloud execution.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.helpers import spacer, load_data, page_setup

def get_leaderboard(results):
    with duckdb.connect() as con:
        leaderboard = con.sql(
            """
            with source as (
                select
                    season_id,
                    rider_id,
                    rider,
                    season_category,
                    count(*) as races,
                    sum(race_milliseconds) as race_milliseconds
                from results
                where is_best_effort
                group by all
            ),
            rankings as (
                select
                    *,
                    row_number() over (partition by season_id order by races desc, race_milliseconds) as overall_rank,
                    row_number() over (partition by season_id, season_category order by races desc, race_milliseconds) as category_rank
                from source
            ),
            gaps as (
                select
                    *,
                    race_milliseconds - min(race_milliseconds) over (partition by season_id, races order by race_milliseconds) as gap
                from rankings
            )
            select * exclude(gap), case gap when 0 then null else gap end as gap from gaps order by races desc, race_milliseconds
        """
        ).pl()

    leaderboard = leaderboard.with_columns(
        pl.col("race_milliseconds").cast(pl.Int64),
        pl.col("gap").cast(pl.Int64),
    )

    return leaderboard

# Page setup
page_setup("Zwift TT Club Racing - Unofficial", ":bicycle:")

# Data load
results = load_data()

st.markdown(
    """
    # Zwift TT Club
    ###### *Unofficial racing results*
    """
)

# Season-level filtering
spacer(2)
c1, c2, c3 = st.columns([2,2,6])

seasons = [int(i) for i in results["season_id"].unique().sort().to_list()]

selected_season = c1.number_input(
    "Season",
    value=max(seasons),
    min_value=min(seasons),
    max_value=max(seasons),
    key="selected_season",
    help="Pick a season! Note, not all seasons have been loaded to the database yet.",
)

focal_results = results.filter(pl.col("season_id") == selected_season)

cats = ["All"] + focal_results["season_category"].unique().sort().to_list()
selected_cat = c2.selectbox(
    "Category",
    key="selected_cat",
    options=cats,
    help="Category is specific to season, taken as the highest cat pen the rider raced in over the season."
)
if selected_cat!="All":
    focal_results = focal_results.filter(pl.col("season_category")==selected_cat)

# Derive leaderboard
leaderboard = get_leaderboard(focal_results)
riders = focal_results["rider"].unique().sort().to_list()

# Filter riders
selected_riders = c3.multiselect("Rider(s)", options=riders, key="selected_riders")
if len(selected_riders) > 0:
    focal_results = focal_results.filter(pl.col("rider").is_in(selected_riders))

# Tabs
spacer(1)
tab_results, tab_leaderboard, tab_medals = st.tabs(["Results", "Leaderboard", "Medal Tables"])

# - Results
with tab_results:
    c1, c2, c3, c4 = st.columns([4, 2, 2, 2], vertical_alignment="bottom")

    # Filter...
    stages = focal_results["stage"].unique().sort().to_list()
    if len(stages) > 1:
        stages = ["All"] + stages
    selected_stage = c1.selectbox(
        "Stage", 
        key="selected_stage",
        options=stages,
        disabled=True if len(stages)==1 else False
    )
    if selected_stage != "All":
        focal_results = focal_results.filter(pl.col("stage") == selected_stage)

    pens = focal_results["category_raced"].unique().sort().to_list()
    if len(pens) > 1:
        pens = ["All"] + pens
    selected_pen = c2.selectbox(
        "Pen", 
        key="selected_pen",
        help="This is the pen the rider rode the stage in and can differ from season category if the rider has ridden in different pens during the given season.",
        options=pens
    )
    if selected_pen != "All":
        focal_results = focal_results.filter(pl.col("category_raced") == selected_pen)

    rankings = {"Overall":"overall_rank", "Season Cat.":"season_cat_rank", "Stage Cat.":"stage_cat_rank"}
    selected_ranking = c3.selectbox(
        "Show rank on",
        key="selected_ranking",
        help="Calculate the rank across all riders, or riders competing in the same category for the season or stage.",
        options=[*rankings.keys()]
    )
    selected_bests = c4.toggle(
        "Bests Only",
        help="Show only each riders best effort per stage (Stage PB); if a rider completes multiple efforts on a stage, their best is their fastest effort. Bests are used to derive the leaderboard.",
        value=True,
    )

    if selected_bests:
        focal_results = focal_results.filter(pl.col("is_best_effort"))

    # Table output
    spacer(1)

    if results["race_milliseconds"].max() < 3600 * 1000:
        ms_format = "mm:ss.SSS"
    elif results["race_milliseconds"].max() >= 3600 * 1000:
        ms_format = "HH:mm:ss.SSS"

    results_table_columns = [
        rankings[selected_ranking],
        "rider",
        "season_category",
        "category_raced",
        "race_milliseconds",
        "race_speed",
        "is_best_effort",
        "stage",
        "event_start_epoch",
    ]

    if selected_stage!="All":
        results_table_columns.remove("stage")

    if selected_bests:
        results_table_columns.remove("is_best_effort")

    if focal_results.shape[0]>0:
        st.dataframe(
            focal_results[results_table_columns],
            column_config={
                "overall_rank": "Rank",
                "season_cat_rank": "Rank",
                "stage_cat_rank": "Rank",
                "pen_rank": "Rank",
                "rider": "Rider",
                "season_category": "Cat.",
                "category_raced": "Pen",
                "race_milliseconds": st.column_config.DatetimeColumn(
                    "Time", format=ms_format, timezone="GMT+4"
                ),
                "race_speed": st.column_config.NumberColumn("Speed (km/h)", format="%.2f"),
                "is_best_effort":"Stage PB",
                "stage": "Stage",
                "event_start_epoch":st.column_config.DatetimeColumn("Date/Time", format="MMM D YYYY, H:mm")
            },
        )

        if focal_results.shape[0]==focal_results["rider_id"].unique().shape[0]:
            c1, c2, c3 = st.columns(3)
            c1.metric("Riders", focal_results["rider_id"].unique().shape[0], border=True)
            c2.metric("Distance", f"{focal_results["event_distance"].sum():.0f} km", border=True)
            c3.metric("Climbing", f"{focal_results["event_elevation"].sum()/1000:.0f} km", border=True)

        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Riders", focal_results["rider_id"].unique().shape[0], border=True)
            c2.metric("Efforts", focal_results.shape[0], border=True)
            c3.metric("Distance", f"{focal_results["event_distance"].sum():.0f} km", border=True)
            c4.metric("Climbing", f"{focal_results["event_elevation"].sum()/1000:.0f} km", border=True)

with tab_leaderboard:

    medals = [":1st_place_medal:", ":2nd_place_medal:", ":3rd_place_medal:"]
    c1, c2, c3 = st.columns(3, border=True, vertical_alignment="bottom")

    if leaderboard.shape[0]>0:
        c1.write(f"{medals[0]} {leaderboard[0]["rider"].to_list()[0]}")
    if leaderboard.shape[0]>1:
        c2.write(f"{medals[1]} {leaderboard[1]["rider"].to_list()[0]}")
    if leaderboard.shape[0]>2:
        c3.write(f"{medals[2]} {leaderboard[2]["rider"].to_list()[0]}")

    spacer(1)

    leaderboard_table_columns = [
        "overall_rank" if selected_cat=="All" else "category_rank",
        "rider",
        "season_category",
        "races",
        "race_milliseconds",
        "gap"
    ]

    if len(selected_riders)>0:
        leaderboard = leaderboard.filter(pl.col("rider").is_in(selected_riders))

    if leaderboard["race_milliseconds"].max() < 3600 * 1000:
        ms_format = "mm:ss.SSS"
    elif leaderboard["race_milliseconds"].max() >= 3600 * 1000:
        ms_format = "HH:mm:ss.SSS"

    if leaderboard["gap"].max() < 60 * 1000:
        ms_format_gap = "+ ss.SSS"
    elif leaderboard["gap"].max() < 3600 * 1000:
        ms_format_gap = "+ mm:ss.SSS"
    elif leaderboard["gap"].max() >= 3600 * 1000:
        ms_format_gap = "+ HH:mm:ss.SSS"

    if leaderboard.shape[0]>0:
        st.dataframe(
            leaderboard[leaderboard_table_columns],
            column_config={
                "overall_rank":"Rank",
                "category_rank":"Rank",
                "rider":"Rider",
                "season_category":"Cat.",
                "races":"Races",
                "race_milliseconds": st.column_config.DatetimeColumn(
                    "Time", format=ms_format, timezone="UTC"
                ),
                "gap": st.column_config.DatetimeColumn(
                    "Gap", format=ms_format_gap, timezone="UTC"
                ),
            }
        )

with tab_medals:

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Stage Medals")

        rounds = results["round_id"].unique().sort().to_list()
        select_rounds = st.select_slider(
            "Stages to include",
            help="This is shown as <season>.<stage>, so 31.4 is stage 4 of season 31. The default is to select the previous 12 stages, including the current stage.", 
            options=results["round_id"].unique().sort().to_list(),
            value=[results["round_id"].unique().sort().to_list()[-12], results["round_id"].unique().sort().to_list()[-1]]
        )
    
        selected_rounds = rounds[rounds.index(select_rounds[0]) : rounds.index(select_rounds[1]) + 1]

        results_for_medals = results.filter(pl.col("round_id").is_in(selected_rounds))


        with duckdb.connect() as con:
            stage_medals = con.sql("""
                select
                    rider_id, 
                    rider,
                    sum(stage_cat_rank=1) as gold,
                    sum(stage_cat_rank=2) as silver,
                    sum(stage_cat_rank=3) as bronze,
                    count(*) as races
                from results_for_medals
                where is_best_effort
                group by all
                order by gold desc, silver desc, bronze desc, races
            """).pl()

        st.dataframe(
            stage_medals[["rider", "gold", "silver", "bronze", "races"]],
            column_config={
                "rider":"Rider",
                "gold":"🥇",
                "silver":"🥈",
                "bronze":"🥉",
                "races":"🏁",
            }
        )

        st.markdown(f"*{len(selected_rounds)} stages selected*")
        
    with c2:
        st.markdown("#### Season Medals")
        selected_seasons = st.slider(
            "Seasons to include",
            value=[results["season_id"].max()-3, results["season_id"].max()],
            min_value=results["season_id"].min(),
            max_value=results["season_id"].max()
        )

        leaderboard_for_medals = get_leaderboard(results).filter(pl.col("season_id").is_in(range(selected_seasons[0], selected_seasons[1]+1)))

        with duckdb.connect() as con:
            stage_medals = con.sql("""
                select
                    rider_id, 
                    rider,
                    sum(category_rank=1) as gold,
                    sum(category_rank=2) as silver,
                    sum(category_rank=3) as bronze,
                    count(*) as races
                from leaderboard_for_medals
                group by all
                order by gold desc, silver desc, bronze desc, races
            """).pl()

        st.dataframe(
            stage_medals[["rider", "gold", "silver", "bronze", "races"]],
            column_config={
                "rider":"Rider",
                "gold":"🥇",
                "silver":"🥈",
                "bronze":"🥉",
                "races":"🏁",
            }
        )

        st.markdown(f"*{selected_seasons[1]-selected_seasons[0]} seasons selected*")

    st.markdown("""
    -----
    The medal tables are a rolling competition showing medals won over the previous stages and seasons. 
    Medals are awarded to the top three of each category, allowing a little competition to form across categories. 
    The default has been set to include: 
    - the previous 12 stages (including the current) for the stage medals table
    - the previous 3 seasons (including the current) for the seasons table

    Note that the tables above are independent of the season and stage selectors/filters *above* the tabs; those only affect results and the leaderboard. Control the medal tables using the sliders within the medal table tab.
    """)