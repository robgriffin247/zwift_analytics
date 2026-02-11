import duckdb
import os

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

def get_events():
    with duckdb.connect(database) as con:
        con.execute(
            f"""
            create schema if not exists google_sheets;

            create or replace table google_sheets.events as
            select *
            from read_csv_auto('https://docs.google.com/spreadsheets/d/{os.getenv("GOOGLE_SHEETS__ZWIFT_ANALYTICS")}/export?format=csv&gid={os.getenv("GOOGLE_SHEETS__ZWIFT_ANALYTICS__EVENTS_SHEET")}');
        """
        )
    
    return "Loaded events from google sheets"

def get_riders():
    with duckdb.connect(database) as con:
        con.execute(
            f"""
            create schema if not exists google_sheets;

            create or replace table google_sheets.riders as
            select *
            from read_csv_auto('https://docs.google.com/spreadsheets/d/{os.getenv("GOOGLE_SHEETS__ZWIFT_ANALYTICS")}/export?format=csv&gid={os.getenv("GOOGLE_SHEETS__ZWIFT_ANALYTICS__RIDERS_SHEET")}');
        """
        )
    
    return "Loaded riders from google sheets"

if __name__=="__main__":
    print(get_events())
    print(get_riders())