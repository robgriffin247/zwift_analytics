import streamlit as st
import polars as pl

def seconds_to_hhmmss(seconds: float) -> str:
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)

    if total >= 3600:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

results = st.session_state["results"]
leaderboard = st.session_state["leaderboard"]

unique_riders = results[["rider"]].unique().sort(by=pl.col("rider"))["rider"].to_list()
unique_cats = results[["category"]].unique().sort(by=pl.col("category"))["category"].to_list()
unique_stages = results[["stage"]].unique().sort(by=pl.col("stage"))["stage"].to_list()


tab_leaderboard, tab_results = st.tabs(["Leaderboard", "Results"])

with tab_leaderboard:
    
    medals = [":1st_place_medal:", ":2nd_place_medal:", ":3rd_place_medal:"]
    st.markdown("##### The Sausage-Roll of Honour, sponsored by Greggs")
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

    st.dataframe(results[["event_id", "stage", "rider", "category", "stage_name", "event_start_datetime", "race_time", "race_speed", "is_best_effort"]],
        column_config={
            "stage":st.column_config.NumberColumn("Stage"),
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
    c3.metric("Efforts",
        int(count) if (count := results.with_columns(
            pl.when((pl.col("rider_id") == 5083506) & (pl.col("event_id") == 5393497))
            .then(0.5)
            .otherwise(1.0)
            .alias("weight")
        ).select(pl.col("weight").sum()).item()) == int(count) else count
        , border=True
    )
        # 5083506
        # 5393497