import os
import duckdb
import time

from dbt_runner import build_models

from ingestion.google_sheets import get_events, get_riders, get_seasons
from ingestion.zwift_racing import run_pipeline, get_event_results, post_riders

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


def refresh_riders_job():
    with duckdb.connect(database) as con:

        rider_ids = con.sql("""
            select rider_id 
            from zwift_racing.riders 
            order by _dlt_load_id 
            limit 1000
            """).pl()["rider_id"].to_list()
    
    load_info = run_pipeline(post_riders(rider_ids))
    
    print(f"Refreshed {len(rider_ids)}")


def get_event_results_job():
    
    # Update the google sheets data into db
    get_events()
    get_riders()
    get_seasons()

    with duckdb.connect(database) as con:

        event_ids = con.sql("""
            with
            expected_events as (
                select event_id::int as event_id,
                from google_sheets.events
                where to_timestamp(event_start_epoch::int)<now()
                    and date_diff('minutes', to_timestamp(event_start_epoch::int), now()) > 45
            ),

            loaded_events as (
                select event_id::int as event_id
                from zwift_racing.event_results
                where 
                    date_diff('minutes', to_timestamp(time::int), now()) > 120 and
                    _dlt_id in (select _dlt_parent_id from zwift_racing.event_results__results group by 1)
                group by 1
            )
            
            select * 
            from expected_events 
            where event_id not in (select event_id from loaded_events)
            """).pl()["event_id"].to_list()
    
    if len(event_ids)>0:
        i = 0
        print(f"Identified {len(event_ids)} events to load!")
        for event in event_ids:
            print(f"Getting event {event}")
            if i>=1:
                print("Waiting to run api request...")
                time.sleep(70)
            i+=1

            print(run_pipeline(get_event_results(event)))

        build_models()

    
if __name__=="__main__":
    get_event_results_job()
    
