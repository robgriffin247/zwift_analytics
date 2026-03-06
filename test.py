from ingestion.zwift_racing_app import run_pipeline, get_rider, get_club_riders, get_event_results

if __name__=="__main__":
    print(run_pipeline(get_event_results(5393486)))