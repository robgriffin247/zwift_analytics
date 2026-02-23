import os
import httpx
import dlt
from typing import Any
from collections.abc import Iterator
import time 
from dlt.extract import DltResource

base_url = os.getenv("ZWIFT_RACING__URL")
header = {"Authorization": os.getenv("ZWIFT_RACING__KEY")}


@dlt.resource(
    name="event_results",
    write_disposition="merge",
    primary_key="event_id"
)
def get_event_results(event_id: int) -> Iterator[dict[str, Any]]:
    response = httpx.get(f"{base_url}results/{event_id}", headers=header)
    response.raise_for_status()
    yield response.json()


@dlt.resource(
    name="riders",
    write_disposition="merge",
    primary_key="rider_id"
)
def get_rider(rider_id: int) -> Iterator[dict[str, Any]]:
    response = httpx.get(f"{base_url}riders/{rider_id}", headers=header)
    response.raise_for_status()
    yield response.json()


@dlt.resource(
    name="riders",
    write_disposition="merge",
    primary_key="rider_id"
)
def post_riders(rider_ids: list[int]) -> Iterator[dict[str, Any]]:
    response = httpx.post(f"{base_url}riders/", headers=header, json=rider_ids)
    response.raise_for_status()
    for rider in response.json():
        yield rider


@dlt.resource(
    name="riders",
    write_disposition="merge",
    primary_key="rider_id"
)
def get_club_riders(club_id: int, first_rider_id: int = 0) -> Iterator[dict[str, Any]]:
    response = httpx.get(f"{base_url}clubs/{club_id}/{first_rider_id}", headers=header)
    response.raise_for_status()
    riders = response.json()["riders"]

    while len(riders) % 1000 == 0:
        print("Over 1000 riders in the club, waiting one hour...")
        time.sleep(3601)
        last_rider_id = riders[-1]["rider_id"]  # Get last rider ID
        response = httpx.get(f"{base_url}clubs/{club_id}/{last_rider_id}", headers=header)
        response.raise_for_status()
        riders += response.json()["riders"]

    for rider in riders:
        yield rider


def run_pipeline(resource: DltResource) -> None:
    """Run the dlt pipeline with the given resource"""
    target = os.getenv("TARGET")

    if target in ["prod", "test"]:
        destination = dlt.destinations.motherduck(
            credentials={
                "database": f"zwift_analytics_{target}",
                "motherduck_token": os.environ["MOTHERDUCK_TOKEN"],
            }
        )
    elif target == "dev":
        destination = dlt.destinations.duckdb(
            credentials="data/zwift_analytics_dev.duckdb"
        )
    else:
        raise ValueError(f"Invalid TARGET value in environment; expected 'prod', 'test' or 'dev', got '{target}'")

    pipeline = dlt.pipeline(
        pipeline_name=f"zwift_analytics__zwift_racing_{target}_pipeline",
        destination=destination,
        dataset_name="zwift_racing",
    )

    load_info = pipeline.run(resource)
    return load_info


if __name__ == "__main__":
    # Just inspect the data
    # for rider in get_rider(4598636):
    #     print(rider)
    
    # Or run the full pipeline
    # run_pipeline(get_rider(4598636))
    # run_pipeline(post_riders([4598636, 5574]))
    # events = [5237098, 5237099, 5237100, 5237107, 5237108, 5237111]
    # i = 0
    # for event in events:
    #     run_pipeline(get_event_results(event))
    #     i += 1
    #     if i<len(events):
    #         time.sleep(61)
    run_pipeline(get_event_results(5393234))