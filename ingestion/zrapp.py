import os
import httpx
import dlt
import json


def ingest_zrapp(endpoint, payload):

    base_url = "https://zwift-ranking.herokuapp.com/public/"
    header = {"Authorization": os.getenv("ZRAPP_API_KEY")}

    @dlt.resource(name="riders", write_disposition="merge", primary_key="rider_id")
    def get_rider(rider_id: int, verbose=False):

        if not isinstance(rider_id, int):
            raise TypeError(f"Rider ID must be an integer, got {rider_id!r}")

        if verbose:
            print(f"Getting rider from {base_url}riders/{rider_id}")

        response = httpx.get(f"{base_url}riders/{rider_id}", headers=header)
        response.raise_for_status()

        content = response.content
        decoded_content = content.decode(encoding="utf-8")
        rider = json.loads(decoded_content)

        yield rider

    @dlt.source
    def zrapp_source(endpoint, payload):
        if endpoint == "rider":
            return [get_rider(payload, verbose=True)]

    destination = os.getenv("DLT_DESTINATION")

    if destination == "duckdb":
        _destination = dlt.destinations.duckdb(
            credentials="data/zwift_analytics.duckdb"
        )

    pipeline = dlt.pipeline(
        pipeline_name="zwift_analytics__zrapp_pipeline",
        destination=_destination,
        dataset_name="zrapp",
    )

    load_info = pipeline.run(zrapp_source(endpoint, payload))

    return load_info


if __name__ == "__main__":
    print(ingest_zrapp("rider", 4598636))
