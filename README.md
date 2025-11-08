# Zwift Analytics

## Overview

An app to collect and visualise data related to Zwift racing.

## Data Stack

|Task|Tool|
|----|----|
|Ingestion|dlt & httpx|
|Transformation|dbt|
|Storage|DuckDB (dev) & MotherDuck (prod)|
<!-- |Orchestration|Modal| -->
<!-- |Version Control|Git & GitHub| -->
<!-- |CI/CD|GitHub Actions| -->


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

1. Add ``httpx``, ``dlt`` and ``dlt[duckdb]`` packages

    ```
    uv add httpx dlt dlt[duckdb]
    ```
    
1. Setup to load data to a DuckDB database

    ```
    mkdir data
    echo "data/" >> .gitignore
    echo 'DLT_DESTINATION="duckdb"' >> .env
    ```

1. Create ``./ingestion/zrapp.py``

    ```
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
                        target[leaf] = Decimal(str(value))

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

        """
        Run the pipeline!
        """
        load_info = pipeline.run(zrapp_source(endpoint, payload))

        return load_info


    if __name__ == "__main__":
        print(ingest_zrapp("rider", 4598636))
        print(ingest_zrapp("riders", [5574, 2822494, 4638424]))
        print(ingest_zrapp("club", 20650))
    ```

1. Ingest data with ``uv run python3 ingestion/zrapp.py``


#### Transformation (feat-0002/setup-dbt-to-stage-data-in-dev)

dbt is used to transform data into production ready datasets using ``.sql`` files to model data and ``.yml`` for documentation and data tests.

1. Add the ``dbt`` package with ``uv add dbt-core dbt-duckdb``

1. Add ``./dbt_project.yml``

    ```
    name: 'zwift_analytics'
    version: '1.0.0'

    profile: 'zwift_analytics'

    model-paths: ["models"]
    macro-paths: ["macros"]

    clean-targets:
    - "target"
    - "dbt_packages"

    models:
    zwift_analytics:
        staging:
        +schema: staging
        +materialized: table
    ```

1. Add ``./profiles.yml``

    ```
    zwift_analytics:
    target: dev
    outputs:
        dev:
        type: duckdb
        path: data/zwift_analytics.duckdb
        threads: 2
    ```

1. Add ``./models/_sources.yml`` which tells dbt which raw data tables exist in the database

    ```
    version: 2

    models: 
    - name: stg_riders
        description: Riders data from zrapp, staged to select columns, set types and rename.
        config:
        tags: ["zrapp", "staging", "riders"]
        columns:
        - name: rider_id
            description: Unique identifier per rider
            data_tests:
            - not_null
            - unique
    ```

1. Add ``./models/staging/stg_riders.sql`` to select, type and rename columns

    ```
    with 

    source as (
    select * 
    from {{ source("zrapp", "riders")}}
    ),

    select_type_and_rename as (
    select
        rider_id::int as rider_id,
        name::varchar as rider,
        club__id::int as club_id,
        club__name::varchar as club,
        race__max90__rating::decimal as velo_90_day_peak,
        race__max90__mixed__category::varchar as velo_90_day_peak_category,
        race__max90__mixed__number::varchar as velo_90_day_peak_category_number,
        zp_category::varchar as zwift_category,
        zp_ftp::int as ftp_watts,
        weight::decimal as weight_kg,
        power__w5::int as watts_5s,
        power__w15::int as watts_15s,
        power__w30::int as watts_30s,
        power__w60::int as watts_60s,
        power__w120::int as watts_120s,
        power__w300::int as watts_300s,
        power__w1200::int as watts_1200s,
        power__wkg5::decimal as watts_kg_5s,
        power__wkg15::decimal as watts_kg_15s,
        power__wkg30::decimal as watts_kg_30s,
        power__wkg60::decimal as watts_kg_60s,
        power__wkg120::decimal as watts_kg_120s,
        power__wkg300::decimal as watts_kg_300s,
        power__wkg1200::decimal as watts_kg_1200s,
        race__finishes::int as races,
        race__wins::int as race_wins,
        race__podiums::int as race_podiums,
        handicaps__profile__flat::decimal as handicap_flat,
        handicaps__profile__rolling::decimal as handicap_rolling,
        handicaps__profile__hilly::decimal as handicap_hilly,
        handicaps__profile__mountainous::decimal as handicap_mountainous,
        phenotype__scores__sprinter::decimal as phenotype_sprinter,
        phenotype__scores__puncheur::decimal as phenotype_puncheur,
        phenotype__scores__pursuiter::decimal as phenotype_pursuiter,
        phenotype__scores__climber::decimal as phenotype_climber,
        phenotype__scores__tt::decimal as phenotype_tt,
        _dlt_load_id::decimal as _dlt_load_id
    from source
    )

    select * from select_type_and_rename
    ```

1. Add ``./models/staging/stg_riders.yml`` to create meta-data

    ```
    version: 2

    models: 
    - name: stg_riders
        description: Riders data from zrapp, staged to select columns, set types and rename.
        config:
        tags: ["zrapp", "staging", "riders"]
        columns:
        - name: rider_id
            description: Unique identifier per rider
            data_tests:
            - not_null
            - unique

    ```

1. *Optional;* Add ``./macros/schema_prefix.sql`` to prevent dbt from prefix schema names with ``main_``

    ```
    {% macro generate_schema_name(custom_schema_name, node) -%}

        {%- set default_schema = target.schema -%}
        {%- if custom_schema_name is none -%}

            {{ default_schema }}

        {%- else -%}

            {{ custom_schema_name | trim }}

        {%- endif -%}

    {%- endmacro %}
    ```

1. Run dbt with ``uv run dbt build``

    - Select models with ``-s`` and up/downstream with ``+``, e.g. ``uv run dbt build -s stg_riders+`` builds ``stg_rider`` and anything downstream

1. *Optional;* View the data with ``uv run duckdb -ui``

    ```
    attach 'data/zwift_analytics.duckdb';
    show all tables;
    select * from zwift_analytics.staging.stg_riders;
    .exit
    ```

#### Dev & Production Databases (feat-0003/add-motherduck-as-prod-storage)

1. Create database ``zwift_analytics`` in MotherDuck

1. Add ``MOTHERDUCK_TOKEN="<token>"`` and ``TARGET="dev"`` to ``.env``, and remove ``DLT_DESTINATION`` (the single ``TARGET`` variable will now be used to control this)
    
1. Run ``direnv allow`` to update the working environment

1. Configure ``profiles.yml``

    ```
    zwift_analytics:
      target: "{{ env_var('TARGET', 'dev') }}"
      outputs:
        dev:
          type: duckdb
          path: data/zwift_analytics.duckdb
          threads: 2
          
        prod:
          type: duckdb
          path: "md:zwift_analytics?motherduck_token={{ env_var('MOTHERDUCK_TOKEN') }}"
          threads: 2
    ```

1. Reconfigure pipeline in ``ingestion/zrapp.py``

    ```
    ...
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
    ...
    ```

Note, I also added rounding on the decimals to prevent schema changes:


    ```
    ...
    from decimal import Decimal, ROUND_HALF_UP

    def ingest_zrapp(endpoint, payload) -> LoadInfo:
        
        ...
        
        DECIMAL_QUANT = Decimal("0.0001")
        
        ...

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
        ...
    ```

## Tasks

- [x] **feat-0001/setup-ingestion-from-zrapp**
    - Rider data needs to be extracted from the ZwiftRacing.app API into a database
    - Extract from get riders, get clubs and post riders
    - Load all to a raw riders table in duckdb
    - Constrain decimals to be decimals

- [x] **feat-0002/setup-dbt-to-stage-data-in-dev**
    - Data needs to be modelled from raw to staging using dbt
    - Setup dbt project using local duckdb
    - Select, type and name columns

- [x] **feat-0003/add-motherduck-as-prod-storage**
    - Set up so production data is stored in MotherDuck
    - Configure credentials and dev/prod environments for dlt and dbt
