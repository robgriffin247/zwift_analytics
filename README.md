# Zwift Analytics

## Overview

An app to collect and visualise data related to Zwift racing.

## Data Stack

|Task|Tool|
|----|----|
|Ingestion|dlt & httpx|
|Storage|DuckDB (dev) & MotherDuck (prod)|
|Orchestration|Modal|
|Version Control|Git & GitHub|
|CI/CD|GitHub Actions|

## DevLog

#### Prerequisites

- Git
- GitHub
- uv
- direnv
- DuckDB
- MotherDuck account
- ZwiftRacing.app API token


#### Setup 

1. Create repo on GitHub

1. Clone repo

    ```
    git clone git@github.com:robgriffin247/zwift_analytics.git
    cd zwift_analytics
    ```

1. Add ``uv`` as the package manager with ``uv init``

1. Add Black formatter with ``uv add black``

1. Add ``.env`` to ``.gitignore``

1. Add zrapp API key to ``.env``  as ``ZRAPP_API_KEY="<ZRAPP_API_KEY>"``

1. Add ``.envrc`` file as follows

    ```
    # Handle windows carriage-returns
    sed -i 's/\r$//' .env

    # Export .env variables
    set -a
    source .env
    set +a
    ```

1. Run ``direnv allow``, allowing ``direnv`` to run the ``.envrc`` as you ``cd`` into the project 

#### Ingestion (feat-0001/setup-ingestion-from-zrapp)

<!-- TODO: fix up these notes -->

Data is extracted from zwiftracing.app API (zrapp) using httpx and loaded to duckdb (and motherduck in prod in th future) using dlt

    1.

    ```
    uv add httpx dlt dlt[duckdb]
    mkdir data
    echo "data/" >> .gitignore
    echo 'DLT_DESTINATION="duckdb"' >> .env
    ```

    ```{python}
    # ./ingestion/zrapp.py
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


    def ingest_zrapp(endpoint, payload) -> LoadInfo:

        base_url = "https://zwift-ranking.herokuapp.com/public/"
        header = {"Authorization": os.getenv("ZRAPP_API_KEY")}

        def wait_429(response) -> None:
            if response.status_code == 429:
                time_to_wait = int(
                    json.loads(response.content.decode(encoding="utf-8")).get("retryAfter")
                )
                print(
                    f"429 Error: Too Many Requests - wait {time_to_wait} seconds to try again!"
                )

            return

        def coerce_floats(rider: dict[str, Any]) -> dict[str, Any]:
            """
            This is to prevent variant columns in dlt as columns such as weight will be interpreted as either ints or floats
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
                        target[leaf] = Decimal(str(value))

            return rider

        @dlt.resource(name="riders", write_disposition="merge", primary_key="rider_id")
        def get_rider(rider_id: int) -> Iterator[dict[str, Any]]:

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

            if not isinstance(club_id, int):
                raise TypeError(f"Club ID must be an integer, got {club_id!r}")

            print(f"Getting club {club_id}")

            response = httpx.get(f"{base_url}clubs/{club_id}", headers=header)
            wait_429(response)
            response.raise_for_status()

            content = response.content
            decoded_content = content.decode(encoding="utf-8")
            club = json.loads(decoded_content)

            # Riders in club endpoint missing the club id and name so need adding in
            riders = club["riders"]
            club_name = club["name"]
            for rider in riders:
                coerce_floats(rider)
                rider["club"] = {"id": club_id, "name": club_name}
                yield rider

            time.sleep(3)

        @dlt.resource(name="riders", write_disposition="merge", primary_key="rider_id")
        def get_riders(ids: list[int]) -> Iterator[dict[str, Any]]:

            if not isinstance(ids, list) or len(ids) == 0 or not isinstance(ids[0], int):
                raise TypeError(f"Input must be a list of ID integers, got {ids!r}")

            print(f"Getting {len(ids)} riders")

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

            if endpoint == "rider":
                return [get_rider(payload)]

            if endpoint == "club":
                return [get_club(payload)]

            if endpoint == "riders":
                return [get_riders(payload)]

            else:
                raise ValueError("Endpoint must be one of rider, club and riders")

        destination = os.getenv("DLT_DESTINATION")

        if destination == "duckdb":
            _destination = dlt.destinations.duckdb(
                credentials="data/zwift_analytics.duckdb"
            )

        # Add in here for motherduck once setup

        pipeline = dlt.pipeline(
            pipeline_name="zwift_analytics__zrapp_pipeline",
            destination=_destination,
            dataset_name="zrapp",
        )

        load_info = pipeline.run(zrapp_source(endpoint, payload))

        return load_info


    if __name__ == "__main__":
        print(ingest_zrapp("rider", 4598636))
        print(ingest_zrapp("riders", [5574, 2822494, 4638424]))
        print(ingest_zrapp("club", 20650))

    ```

#### Transformation (feat-0002/setup-dbt-to-stage-data-in-dev)

- add ``./profiles.yml``

    ```
    transform:
    target: dev
    outputs:
      dev:
        type: duckdb
        path: data/zwift_analytics.duckdb
        schema: staging
        threads: 2
    ```

- add ``./dbt_profiles.yml``

- add ``./macros/schema_prefix.yml``

- add ``./models/staging/stg_riders.sql``

- add ``./models/staging/stg_riders.yml``

- add ``./models/_sources.yml``

- add ``dbt`` with ``uv add dbt-core dbt-duckdb``

- *optional;* view the data with ``uv run duckdb -ui``

    ```
    attach 'data/zwift_analytics.duckdb';
    show all tables;
    select * from zwift_analytics.staging.stg_riders;
    .exit
    ```

## Tasks

- [x] **feat-0001/setup-ingestion-from-zrapp**
    - Rider data needs to be extracted from the ZwiftRacing.app API into a database
    - Extract from get riders, get clubs and post riders
    - Load all to a raw riders table in duckdb
    - Constrain decimals to be decimals
- [ ] **feat-0002/setup-dbt-to-stage-data-in-dev**
    - Data needs to be modelled from raw to staging using dbt
    - Setup dbt project using local duckdb
    - Select, type and name columns