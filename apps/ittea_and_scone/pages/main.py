import streamlit as st
import polars as pl
import duckdb 

def format_duration(milliseconds):
    total_seconds = milliseconds // 1000
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    if days > 0:
        return f"{days} days, {hours:2}:{minutes:02}"
    else:
        return f"{hours:2}:{minutes:02}"
        
results = st.session_state["results"]

with duckdb.connect() as con:

    leaderboard = con.sql("""
        with source as (
            select
                season_id,
                rider_id,
                rider,
                season_category,
                count(*) as races,
                sum(race_milliseconds) as race_milliseconds,
                sum(event_distance)/sum(race_milliseconds)*3600000 as race_speed
            from results
            where is_best_effort
            group by all
        ),

        add_gap as (
            select
                *,
                race_milliseconds - min(race_milliseconds) over (partition by season_id, races) as overall_gap,
                race_milliseconds - min(race_milliseconds) over (partition by season_id, races, season_category) as category_gap,
            from source
        ),

        null_gap as (
            select 
                * exclude(race_milliseconds, overall_gap, category_gap), 
                race_milliseconds::int as race_milliseconds,
                (case when overall_gap=0 then null else overall_gap end)::int as overall_gap,
                (case when category_gap=0 then null else category_gap end)::int as category_gap,
                row_number() over (partition by season_id order by races desc, race_milliseconds) as overall_rank,
                row_number() over (partition by season_id, season_category order by races desc, race_milliseconds) as category_rank,
            from add_gap
        )

        select * from null_gap order by races desc, race_milliseconds
    """).pl()

    race_medal_table = con.sql("""
        with medals as (
            select 
                rider_id,
                rider,
                sum(category_rank=1) as gold,
                sum(category_rank=2) as silver,
                sum(category_rank=3) as bronze,
                count(*) as races,
            from results
            group by all
        )

        select * exclude(rider_id) from medals order by gold desc, silver desc, bronze desc, races
    """).pl()

    seasons_medal_table = con.sql("""
        with medals as (
            select 
                rider_id,
                rider,
                sum(category_rank=1) as gold,
                sum(category_rank=2) as silver,
                sum(category_rank=3) as bronze,
                count(*) as seasons,
            from leaderboard
            group by all
        )

        select * exclude(rider_id) from medals order by gold desc, silver desc, bronze desc, seasons
    """).pl()


tab_leaderboard, tab_efforts, tab_medals = st.tabs(["Leaderboard", "Efforts", "Medal Tables"])

with tab_leaderboard:
 
    focal_leaderboard = leaderboard
    
    st.write("")
    podium_container = st.container() # Container podium for given season
    st.write("")

    c1, c2, c3 = st.columns([3,3,9], vertical_alignment="bottom")

    leaderboard_season = c1.number_input("Season", min_value=int(focal_leaderboard["season_id"].min()), max_value=int(focal_leaderboard["season_id"].max()), value=int(focal_leaderboard["season_id"].max()), key="leaderboard_season")
    focal_leaderboard = focal_leaderboard.filter(pl.col("season_id")==str(leaderboard_season))

    with podium_container:
        unique_cats = focal_leaderboard["season_category"].unique().sort().to_list()


        # Roll of Honor
        medals = [":1st_place_medal:", ":2nd_place_medal:", ":3rd_place_medal:"]
        
        season_sponsors = [
            "The Greggs Sausage-Roll of Honour",
            "Golden Burr-*iTT*-o Podium, sponsored by Taco Bell",
            "The Ashes, presented by JB BBQs",
        ]
        st.markdown(f"##### {season_sponsors[leaderboard_season-1]}")
        cols = st.columns(len(unique_cats), border=True)
        for i, cat in enumerate(unique_cats):
            with cols[i]:
                leaders = focal_leaderboard.filter(pl.col("season_category")==cat)["rider"].to_list()
                for j, medal in enumerate(medals):
                    if j<len(leaders):
                        st.markdown(
                            f"""
                            {f'**' if j==0 else f''}{cat}{medals[j]} {leaders[j]}{'**' if j==0 else ''}
                            """
                        )

    leaderboard_cat = c2.selectbox("Cat.", options=["All"] + focal_leaderboard["season_category"].unique().sort().to_list(), key="leaderboard_cat")
    focal_leaderboard = focal_leaderboard.filter(pl.col("season_category").is_in([leaderboard_cat] if leaderboard_cat!="All" else ["A", "B", "C", "D"]))

    leaderboard_riders = st.multiselect("Rider(s)", options=focal_leaderboard["rider"].unique().sort().to_list(), key="leaderboard_riders")
    if len(leaderboard_riders)>0:
        focal_leaderboard = focal_leaderboard.filter(pl.col("rider").is_in(leaderboard_riders))
    
    st.write("")

    st.dataframe(
        focal_leaderboard[[
            "overall_rank" if leaderboard_cat=="All" else "category_rank", 
            "rider", "season_category", "races", "race_milliseconds", 
            "overall_gap" if leaderboard_cat=="All" else "category_gap", 
            "race_speed"]],
        column_config={
            "overall_rank":st.column_config.NumberColumn("Rank"),
            "category_rank":st.column_config.NumberColumn("Rank"),
            "rider":st.column_config.TextColumn("Rider"),
            "season_category":st.column_config.TextColumn("Cat."),
            "races":st.column_config.NumberColumn("Races"),
            "race_milliseconds":st.column_config.DatetimeColumn("Time", format="mm:ss.SSS" if focal_leaderboard["race_milliseconds"].max()<3600*1000 else "HH:mm:ss.SSS"),
            "overall_gap":st.column_config.DatetimeColumn("Gap", format="+ mm:ss.SSS" if focal_leaderboard["overall_gap"].max() is not None and focal_leaderboard["overall_gap"].max()<3600*1000 else "HH:mm:ss.SSS"),
            "category_gap":st.column_config.DatetimeColumn("Gap", format="+ mm:ss.SSS" if focal_leaderboard["category_gap"].max() is not None and focal_leaderboard["category_gap"].max()<3600*1000 else "HH:mm:ss.SSS"),
            "race_speed":st.column_config.NumberColumn("km/h", format="%.2f"),
        }
    )

with tab_efforts:

    st.write("")
    c1, c2, c3, c4, _ = st.columns([3,3,3,3,3], vertical_alignment="bottom")
    
    focal_results = results

    efforts_season = c1.number_input("Season", min_value=int(focal_results["season_id"].min()), max_value=int(focal_results["season_id"].max()), value=int(focal_results["season_id"].max()), key="results_season")
    focal_results = focal_results.filter(pl.col("season_id")==str(efforts_season))

    efforts_cat = c2.selectbox("Cat.", options=["All"] + focal_results["category_raced"].unique().sort().to_list(), key="efforts_cat")
    focal_results = focal_results.filter(pl.col("category_raced").is_in([efforts_cat] if efforts_cat!="All" else ["A", "B", "C", "D"]))

    efforts_stage = c3.selectbox("Stage", options=["All"] + focal_results["stage"].unique().sort().to_list())
    if efforts_stage!="All":
        focal_results = focal_results.filter(pl.col("stage")==efforts_stage)

    efforts_bests = c4.toggle("Bests Only", value=True)
    if efforts_bests:
        focal_results = focal_results.filter(pl.col("is_best_effort")==True)

    efforts_riders = st.multiselect("Rider(s)", options=focal_results["rider"].unique().sort().to_list())
    if len(efforts_riders)>0:
        focal_results = focal_results.filter(pl.col("rider").is_in(efforts_riders))
    
    st.write("")
    c1, c2, c3, c4 = st.columns([3,3,3,3], vertical_alignment="bottom")
    c1.metric("Efforts", sum(focal_results["effort_counter"].to_list()), border=True)
    c2.metric("Distance", f"{sum(focal_results["event_distance"].to_list()):.2f} km", border=True)
    c3.metric("Climbing", f"{sum(focal_results["event_elevation"].to_list()):.0f} m", border=True)
    c4.metric("Time", format_duration(sum(focal_results["race_milliseconds"].to_list())), border=True)

    st.write("")
    st.dataframe(
        focal_results[[
            "stage", 
            "overall_rank" if efforts_cat=="All" else "category_rank", 
            "rider", "category_raced", 
            "race_milliseconds", "race_speed", "is_best_effort", "event", "event_start_epoch", ]],
        column_config={
            "stage":st.column_config.TextColumn("Stage"),
            "event":st.column_config.TextColumn("Route"),
            "event_start_epoch":st.column_config.DatetimeColumn("Date/Time", format="D/M/YY HH:mm"),
            "rider":st.column_config.TextColumn("Rider"),
            "category_raced":st.column_config.TextColumn("Cat."),
            "overall_rank":st.column_config.NumberColumn("Rank"),
            "category_rank":st.column_config.NumberColumn("Rank"),
            "race_milliseconds":st.column_config.DatetimeColumn("Time", format="mm:ss.SSS" if focal_results["race_milliseconds"].max()<3600*1000 else "HH:mm:ss.SSS"),
            "race_speed":st.column_config.NumberColumn("km/h", format="%.2f"),
            "is_best_effort":st.column_config.CheckboxColumn("Best"),
        }
        )
        
with tab_medals:
    
    st.write("")
    c1, c2 = st.columns(2)
    
    c1.markdown("##### Races Medal Table")
    c1.dataframe(race_medal_table, column_config={
            "rider":st.column_config.TextColumn("Rider", width=280),
            "gold":st.column_config.NumberColumn("🥇", width=32),
            "silver":st.column_config.NumberColumn("🥈", width=32),
            "bronze":st.column_config.NumberColumn("🥉", width=32),
            "races":st.column_config.NumberColumn("🏁", width=32),
        })

    c2.markdown("##### Seasons Medal Table")
    c2.dataframe(seasons_medal_table, column_config={
            "rider":st.column_config.TextColumn("Rider", width=280),
            "gold":st.column_config.NumberColumn("🥇", width=32),
            "silver":st.column_config.NumberColumn("🥈", width=32),
            "bronze":st.column_config.NumberColumn("🥉", width=32),
            "seasons":st.column_config.NumberColumn("🏁", width=32),
        })