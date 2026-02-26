#  add a generate_events_seed step before getting events, then repeat the logic shown in jobs.py to inget data from zrapp
# Also add a step to generate_seed which adds existing seed rows and then reduce to unique

import os
import duckdb
import time

from ingestion.generate_events_seed import generate_events_seed, _logging_time
from ingestion.zwift_racing import get_event_results, run_pipeline

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

def ingest_events():

    """
    The aim is to:
        - load all events that have *not been loaded* and started > 1hour ago
        - REload all events that have occured in the last 1-12 hours, even if they have already been loaded
    This logic defines the events_to_load, a list which is then iterated through
    """
    print(generate_events_seed())

    with duckdb.connect() as con:
        past_events = con.sql("""
            select event_id 
            from read_csv_auto('seeds/events.csv') 
            where to_timestamp(start_epoch::int)<=now() - interval '1 hours'
            group by 1""").pl()["event_id"].to_list()

        recent_events = con.sql("""
            select event_id 
            from read_csv_auto('seeds/events.csv') 
            where to_timestamp(start_epoch::int) between now() - interval '12 hours' and now()  - interval '1 hours'
            group by 1""").pl()["event_id"].to_list()

    with duckdb.connect(database) as con:
        loaded_events = con.sql("""
            select event_id::int as event_id
            from zwift_racing.event_results
        """).pl()["event_id"].to_list()

    past_events_not_loaded = list(set(past_events) - set(loaded_events))

    events_to_load = list(set(past_events_not_loaded + recent_events))

    remaining_loads = len(events_to_load)

    print(f"{_logging_time()}: Identified {remaining_loads} events to load")

    while remaining_loads>0:
        for event in events_to_load:
            print(f"{_logging_time()}: Getting event {event}")

            time.sleep(70 if remaining_loads < len(events_to_load) else 0)
            
            print(run_pipeline(get_event_results(event)))

            print(f"{_logging_time()}: Event {event} loaded - {remaining_loads} remaining!")
            
            remaining_loads-=1

    return f"{len(events_to_load)} events loaded!\n" + (80*"=")

if __name__=="__main__":
    print(ingest_events())