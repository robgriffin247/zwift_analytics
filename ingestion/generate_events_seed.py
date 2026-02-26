import duckdb
import os
import polars as pl
from datetime import datetime as dt

def _logging_time(): 
    return dt.now().strftime("%Y-%m-%d %H:%M:%S")

def generate_events_seed():

    google_document_id = os.getenv("GS__ZWIFT_ANALYTICS_ADMIN")
    series_sheet_id = os.getenv("GS__ZWIFT_ANALYTICS_ADMIN__SERIES")

    with duckdb.connect() as con:
        print(f"{_logging_time()}: Getting series list")
        active_series = con.sql(f"""
            select * 
            from read_csv_auto('https://docs.google.com/spreadsheets/d/{google_document_id}/export?format=csv&gid={series_sheet_id}')
            where active_from_date<=now() and active_to_date>=now()
            """).pl()

        events = []

        for series in active_series.iter_rows(named=True):
            print(f"{_logging_time()}: Getting events for series ID {series['series_id']}; {series['series_name']}")
            series_events = con.sql(f"""
                select '{series["series_id"]}' as series_id, season_id, event_id, start_epoch
                from read_csv_auto('https://docs.google.com/spreadsheets/d/{series["sheet_id"]}/export?format=csv&gid={series["events_sheet_id"]}')
                """).pl()
            
            events += [series_events]
    
    pl.concat(events).write_csv("seeds/events.csv")

    return f"{_logging_time()}: Events seed generated"

if __name__=="__main__":
    print(generate_events_seed())