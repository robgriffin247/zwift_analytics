import os
import httpx
import dlt
import json
from decimal import Decimal
import time
from typing import Any
from collections.abc import Iterator
from dlt.extract import DltResource
from dlt.common.pipeline import LoadInfo
from decimal import Decimal, ROUND_HALF_UP


def ingest_zrapp(endpoint, payload) -> LoadInfo:

    base_url = "https://zwift-ranking.herokuapp.com/public/"
    header = {"Authorization": os.getenv("ZRAPP_API_KEY")}
    DECIMAL_QUANT = Decimal("0.0001")

    def wait_429(response: httpx.Response) -> int | None:
        """
        A 429 means there has not been enough time elapsed since the previous call to the endpoint; you've hit the rate limiter.
        This returns a helpful message (rather than just raising 429 error) and helps if you want to automate retry.
        """
        if response.status_code == 429:
            content = response.content
            decoded_content = content.decode(encoding="utf-8")
            json_content = json.loads(decoded_content)

            time_to_wait = int(json_content.get("retryAfter")) + 1
            hours, remainder = divmod(time_to_wait, 3600)
            minutes, seconds = divmod(remainder, 60)

            print(
                f"429 Error: Wait {(str(hours) + ':') if time_to_wait >= 3600 else ""}{minutes:02}:{seconds:02} to try again!"
            )

            return time_to_wait

        return None

    def coerce_floats(rider: dict[str, Any]) -> dict[str, Any]:
        """
        This is to prevent variant columns in dlt as columns such as weight will be interpreted as either ints or floats depending on the rider value.
        """
        FLOAT_FIELDS = [
            "weight",
            "power__wkg5",
            "power__wkg15",
            "power__wkg30",
            "power__wkg60",
            "power__wkg120",
            "power__wkg300",
            "power__wkg1200",
            "power__cp",
            "power__awc",
            "power__compound_score",
            "power__power_rating",
            "race__last__rating",
            "race__current__rating",
            "race__max30__rating",
            "race__max90__rating",
            "handicap__profiles__flat",
            "handicap__profiles__rolling",
            "handicap__profiles__hilly",
            "handicap__profiles__mountainous",
            "phenotype__scores__sprinter",
            "phenotype__scores__puncheur",
            "phenotype__scores__pursuiter",
            "phenotype__scores__climber",
            "phenotype__scores__tt",
            "phenotype__bias",
        ]

        for f in FLOAT_FIELDS:
            target = rider
            parts = f.split("__")
            for part in parts[:-1]:
                target = target.get(part)
                if target is None:
                    break
            else:
                leaf = parts[-1]
                value = target.get(leaf)
                if value is not None:
                    target[leaf] = Decimal(str(value)).quantize(
                        DECIMAL_QUANT, rounding=ROUND_HALF_UP
                    )

        return rider

    @dlt.resource(name="riders", write_disposition="merge", primary_key="rider_id")
    def get_rider(rider_id: int) -> Iterator[dict[str, Any]]:
        """
        Make a GET request to the riders endpoint for a single rider
        """
        if not isinstance(rider_id, int):
            raise TypeError(f"Rider ID must be an integer, got {rider_id!r}")

        print(f"Getting rider {rider_id}")

        response = httpx.get(f"{base_url}riders/{rider_id}", headers=header)
        wait_429(response)
        response.raise_for_status()

        content = response.content
        decoded_content = content.decode(encoding="utf-8")
        rider = json.loads(decoded_content)

        yield coerce_floats(rider)

        time.sleep(3)

    @dlt.resource(name="riders", write_disposition="merge", primary_key="rider_id")
    def get_club(club_id: int) -> Iterator[dict[str, Any]]:
        """
        Make a GET request to the clubs endpoint for all (up to 1000) riders in a single club (if >1000 riders in a club, it's the first 1000 sorted on riderId).
        """
        if not isinstance(club_id, int):
            raise TypeError(f"Club ID must be an integer, got {club_id!r}")

        print(f"Getting club {club_id}")

        response = httpx.get(f"{base_url}clubs/{club_id}", headers=header)
        wait_429(response)
        response.raise_for_status()

        content = response.content
        decoded_content = content.decode(encoding="utf-8")
        club = json.loads(decoded_content)

        """
        Riders in club endpoint riders data are missing the club id and name so need this info adding in.
        """
        riders = club["riders"]
        club_name = club["name"]

        for rider in riders:
            coerce_floats(rider)
            rider["club"] = {"id": club_id, "name": club_name}
            yield rider

        time.sleep(3)

    @dlt.resource(name="riders", write_disposition="merge", primary_key="rider_id")
    def get_riders(ids: list[int]) -> Iterator[dict[str, Any]]:
        """
        Make a POST request to get rider details for a list of rider IDs.
        """
        if not isinstance(ids, list) or len(ids) == 0 or not isinstance(ids[0], int):
            raise TypeError(f"Input must be a list of ID integers, got {ids!r}")

        print(
            f"Getting {len(ids)} riders: {', '.join([str(i) for i in ids]) if len(ids)<=3 else ', '.join([str(i) for i in ids[:2]]) + '... ' + str(ids[-1])}"
        )

        response = httpx.post(
            f"{base_url}riders/", headers=header, json=ids, timeout=30
        )
        wait_429(response)
        response.raise_for_status()

        content = response.content
        decoded_content = content.decode(encoding="utf-8")
        riders = json.loads(decoded_content)

        for rider in riders:
            yield coerce_floats(rider)

        time.sleep(3)

    @dlt.source
    def zrapp_source(endpoint, payload) -> list[DltResource[Any]]:
        """
        Return the correct resource depending on the chosen endpoint.
        """

        if endpoint == "rider":
            return [get_rider(payload)]

        if endpoint == "club":
            return [get_club(payload)]

        if endpoint == "riders":
            return [get_riders(payload)]

        else:
            raise ValueError("Endpoint must be one of rider, club and riders")

    """
    Set dlt destination credentials, specific to dev and prod.
    """
    target = os.getenv("TARGET")

    if target == "prod":
        _destination = dlt.destinations.motherduck(
            credentials={
                "database": "zwift_analytics",
                "motherduck_token": os.environ["MOTHERDUCK_TOKEN"],
            }
        )
    elif target == "dev":
        _destination = dlt.destinations.duckdb(
            credentials="data/zwift_analytics.duckdb"
        )
    else:
        raise ValueError(
            "Invalid TARGET; check TARGET is exported with value prod or dev."
        )

    pipeline = dlt.pipeline(
        pipeline_name=f"zwift_analytics__zrapp_{target}_pipeline",
        destination=_destination,
        dataset_name="zrapp",
    )

    """
    Run the pipeline!
    """
    load_info = pipeline.run(zrapp_source(endpoint, payload))

    return load_info


if __name__ == "__main__":
    print(ingest_zrapp("rider", 4598636))
