import streamlit as st
import json
import polars as pl

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
    out = events_df_from_text(input_text, league_id)
    st.toast(f"{out.shape[0]} events found!")
    st.dataframe(out)
