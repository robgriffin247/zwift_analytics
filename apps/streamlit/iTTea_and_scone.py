import os
import streamlit as st
import duckdb
import polars as pl
import json

def events_df_from_text(raw_text: str, league_id: int) -> pl.DataFrame:
    """
    Parse ZwiftPower JSON text (string) and return a Polars DataFrame
    with columns: event_id, event_start_epoch, league_id.
    Accepts either:
        - a JSON object with a top-level "data" list
        - a JSON list (will be treated as {"data": list})
    """
    text = raw_text.strip()
    if not text:
        raise ValueError("Empty input")

    if text.startswith("["):
        payload = {"data": json.loads(text)}
    else:
        payload = json.loads(text)

    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("JSON must contain a top-level 'data' list")

    rows = []
    for event in data:
        rows.append(
            {
                "event_id": event.get("zid"),
                "event_start_epoch": event.get("tm"),
                "league_id": league_id,
            }
        )

    return pl.DataFrame(rows)

def seconds_to_hhmmss(seconds: float) -> str:
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)

    if total >= 3600:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

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



@st.cache_resource(show_spinner="Establishing database connection")
def get_db_connection():
    return duckdb.connect(database, read_only=False)

cache_data_hours = 1

@st.cache_data(
    ttl= cache_data_hours * 60 * 60,
    max_entries=10,
    show_spinner="Loading data from database",
)
def load_data():
    con = get_db_connection()
    results = con.sql("select *, event_start_epoch from core.fct__ts_itt_club_spring_2026__results").pl()
    leaderboard = con.sql("select * from core.fct__ts_itt_club_spring_2026__leaderboard").pl()

    return [results, leaderboard]


st.header("iTTea & Scone")

tab_leaderboard, tab_results, tab_convert = st.tabs(["Leaderboard", "Results", "Add Events"])



results, leaderboard = load_data()

unique_riders = results[["rider"]].unique().sort(by=pl.col("rider"))["rider"].to_list()
unique_cats = results[["category"]].unique().sort(by=pl.col("category"))["category"].to_list()
unique_stages = results[["stage"]].unique().sort(by=pl.col("stage"))["stage"].to_list()




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

    st.dataframe(results[["stage", "rider", "category", "stage_name", "event_start_datetime", "race_time", "race_speed", "is_best_effort"]],
        column_config={
            "stage":st.column_config.NumberColumn("Stage"),
            "rider":st.column_config.TextColumn("Rider"),
            "category":st.column_config.TextColumn("Cat."),
            "stage_name":st.column_config.TextColumn("Route"),
            "event_start_datetime":st.column_config.DatetimeColumn("Date/Time", format="D/M/YY HH:mm"),
            "race_time":st.column_config.TextColumn("Time"),
            "race_speed":st.column_config.NumberColumn("Speed", format="%.2f"),
            "is_best_effort":st.column_config.CheckboxColumn("Best"),
        }
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Time", seconds_to_hhmmss(results[["race_seconds"]].sum()["race_seconds"].to_list()[0]), border=True)
    c2.metric("Distance", f"{results[["stage_distance"]].sum()["stage_distance"].to_list()[0]:.2f} km", border=True)
    c3.metric("Efforts", results.shape[0], border=True)

with tab_convert:

    st.markdown("""
    1. Login to [ZwiftPower](https://zwiftpower.com)
    1. Find the right league and get the ID from the URL (e.g. ``3165`` from ``https://zwiftpower.com/league.php?id=3165``)
    1. Enter the league ID
    1. Get Data
    1. Copy the entire text found at the link
    1. Paste the copied text into the **Data** textbox below
    1. Press convert
    1. Click on a cell in the table, select all (ctrl + A); the data in the table should be highlighted red
    1. Copy the data (probably needs ctrl + C)
    1. Go to [GoogleSheets](https://docs.google.com/spreadsheets/d/1mBaTJDxDu3VArnACJJXKDaMhSkTqTBStrWyvinRWYS0/edit?usp=sharing) and add the data to the events sheet. Take care not to overwrite the column names!
    """)
    c1, c2, _ = st.columns([2,1,5], vertical_alignment="bottom")
    league_id = c1.number_input("League ID", value=3165, label_visibility="hidden")
    c2.link_button("Get Data", f"https://zwiftpower.com/api3.php?do=league_event_results&id={league_id}")
    
    st.write("")
    c1, c2 = st.columns([7,2], vertical_alignment="bottom")
    input_text = c1.text_input("Data")
    if c2.button("Convert"):
        st.dataframe(events_df_from_text(input_text, league_id))
