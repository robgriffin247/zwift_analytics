import streamlit as st
import polars as pl
import duckdb 

def seconds_to_hhmmss(seconds: float) -> str:
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)

    if total >= 3600:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

leaderboard = st.session_state["leaderboard"]
results = st.session_state["results"]

with duckdb.connect() as con:
    season_medals = con.sql("""
        select 
            rider_id, 
            rider, 
            category,
            sum(category_rank=1) as category_gold,
            sum(category_rank=2) as category_silver,
            sum(category_rank=3) as category_bronze,
            sum(category_rank in (1,2,3)) as category_total
        from leaderboard group by all
        order by category_gold desc, category_silver desc, category_bronze desc, category
    """).pl()

    stage_medals = con.sql("""
            select 
                rider_id, 
                rider, 
                category,
                sum(category_placing=1) as category_gold,
                sum(category_placing=2) as category_silver,
                sum(category_placing=3) as category_bronze,
                sum(category_placing in (1,2,3)) as category_total
            from results group by all
            order by category_gold desc, category_silver desc, category_bronze desc, category
        """).pl()


# Show season selector if >1 season in data
if results[["season_id"]].unique().shape[0]>1:

    c1, _ = st.columns([2,12])

    selected_season = c1.number_input(
        "Season", 
        min_value=results[["season_id"]].min()["season_id"].to_list()[0],
        max_value=results[["season_id"]].max()["season_id"].to_list()[0],
        value=results[["season_id"]].max()["season_id"].to_list()[0],
    )

    st.write("")

    leaderboard = leaderboard.filter(pl.col("season_id")==selected_season)
    results = results.filter(pl.col("season_id")==selected_season)

else:
    selected_season = results[["season_id"]].min()["season_id"].to_list()[0]

unique_riders = results[["rider"]].unique().sort(by=pl.col("rider"))["rider"].to_list()
unique_cats = results[["category"]].unique().sort(by=pl.col("category"))["category"].to_list()
unique_stages = results[["stage"]].unique().sort(by=pl.col("stage"))["stage"].to_list()


tab_leaderboard, tab_results, tab_medal = st.tabs(["Season Standings", "Race Results", "Medal Tables"])

with tab_leaderboard:

        
    # Roll of Honor
    medals = [":1st_place_medal:", ":2nd_place_medal:", ":3rd_place_medal:"]
    st.markdown(f"##### The Greggs Sausage-Roll of Honour")
    cols = st.columns(len(unique_cats), border=True)
    for i, cat in enumerate(unique_cats):
        with cols[i]:
            leaders = leaderboard.filter(pl.col("category")==cat)["rider"].to_list()
            for j, medal in enumerate(medals):
                if j<len(leaders):
                    st.markdown(
                        f"""
                        {'**' if j==0 else ''}{medals[j]} {leaders[j]}{'**' if j==0 else ''}
                        """
                    )

    st.markdown("-----")
    c1, c2, _ = st.columns([2,6,4])
    input_leaderboard_categories = c1.selectbox("Category", options=["All"] + unique_cats, key="leaderboard_cats")
    selected_leaderboard_categories = unique_cats if input_leaderboard_categories == "All" else [input_leaderboard_categories] 
    leaderboard = leaderboard.filter(pl.col("category").is_in(selected_leaderboard_categories))
    selected_leaderboard_riders = c2.multiselect("Rider(s)", options=leaderboard[["rider"]].unique().sort(by=pl.col("rider"))["rider"].to_list(), key="leaderboard_riders")

    if len(selected_leaderboard_riders)==0:
        pass
    else:
        leaderboard = leaderboard.filter(pl.col("rider").is_in(selected_leaderboard_riders))
    
    if leaderboard.shape[0]>0:
        st.dataframe(leaderboard[["category_rank" if input_leaderboard_categories!="All" else "overall_rank", "rider", "category", "velo_first", "velo_first_category", "races", "gap"]], 
            column_config={
                "overall_rank":st.column_config.NumberColumn("Rank", width="small"),
                "category_rank":st.column_config.NumberColumn("Rank", width="small"),
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
    
    c1, c2, c3, c4 = st.columns([2,2,6,2], vertical_alignment="bottom")

    input_results_categories = c1.selectbox("Category", options=["All"] + unique_cats, key="results_cats")
    selected_results_categories = unique_cats if input_results_categories == "All" else [input_results_categories] 
    results = results.filter(pl.col("category").is_in(selected_results_categories))
    
    selected_stage = c2.selectbox("Stage", options=["All"] + unique_stages)
    selected_results_riders = c3.multiselect("Rider(s)", options=results[["rider"]].unique().sort(by=pl.col("rider"))["rider"].to_list())
    only_show_best_efforts = c4.toggle("Bests Only", value=True)


    if len(selected_results_riders)==0:
        pass
    else:
        results = results.filter(pl.col("rider").is_in(selected_results_riders))
    
    if selected_stage=="All":
        pass
    else:
        results = results.filter(pl.col("stage").is_in([selected_stage]))
    
    if not only_show_best_efforts:
        pass
    else:
        results = results.filter(pl.col("is_best_effort")==True)

    st.write(f"")
    st.dataframe(results[["stage", "category", "overall_placing" if input_results_categories=="All" else "category_placing", "rider", "race_time", "race_speed", "is_best_effort", "event_start_datetime", ]],
        column_config={
            "stage":st.column_config.NumberColumn("Stage"),
            "overall_placing":st.column_config.NumberColumn("Rank"),
            "category_placing":st.column_config.NumberColumn("Rank"),
            "rider":st.column_config.TextColumn("Rider"),
            "category":st.column_config.TextColumn("Cat."),
            "stage_name":st.column_config.TextColumn("Route"),
            "event_start_datetime":st.column_config.DatetimeColumn("Date/Time", format="D/M/YY HH:MM"),
            "race_time":st.column_config.TextColumn("Time"),
            "race_speed":st.column_config.NumberColumn("Speed", format="%.2f"),
            "is_best_effort":st.column_config.CheckboxColumn("Best"),
        }
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Time", seconds_to_hhmmss(results[["race_seconds"]].sum()["race_seconds"].to_list()[0]), border=True)
    c2.metric("Distance", f"{results[["stage_distance"]].sum()["stage_distance"].to_list()[0]:.2f} km", border=True)
    c3.metric("Efforts", results[["effort_counter"]].sum()["effort_counter"].to_list()[0] , border=True)

with tab_medal:
    
    c1, c2 = st.columns(2)
    c1.markdown("##### Season Medals")
    c1.dataframe(season_medals[["rider", "category_gold", "category_silver", "category_bronze", "category_total"]],
        column_config={
            "rider":st.column_config.TextColumn("Rider"),
            "category_gold":st.column_config.NumberColumn("🥇", width=40),
            "category_silver":st.column_config.NumberColumn("🥈", width=40),
            "category_bronze":st.column_config.NumberColumn("🥉", width=40),
            "category_total":st.column_config.NumberColumn("Total", width=40),
        }
    )

    c2.markdown("##### Stage Medals")
    c2.dataframe(stage_medals[["rider", "category_gold", "category_silver", "category_bronze", "category_total"]],
        column_config={
            "rider":st.column_config.TextColumn("Rider"),
            "category_gold":st.column_config.NumberColumn("🥇", width=40),
            "category_silver":st.column_config.NumberColumn("🥈", width=40),
            "category_bronze":st.column_config.NumberColumn("🥉", width=40),
            "category_total":st.column_config.NumberColumn("Total", width=40),
        }
    )

    st.markdown("*Medals awarded per category*")