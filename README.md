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

1. Prerequisites

    - Git
    - GitHub
    - uv
    - direnv
    - DuckDB
    - MotherDuck account
    - ZwiftRacing.app API token


1. Setup 

    ```
    git clone git@github.com:robgriffin247/zwift_analytics.git
    cd zwift_analytics
    uv init
    uv add black
    direnv allow
    echo ".env" >> .gitignore
    echo 'ZRAPP_API_KEY="<ZRAPP_API_KEY>"' >> .env
    ```
    
    - Replace ``<ZRAPP_API_KEY>`` with API key

    - Add ``./.envrc`` file:
        ```
        # Handle windows carriage-returns
        sed -i 's/\r$//' .env

        # Export .env variables
        set -a
        source .env
        set +a
        ```

1. Ingestion (feat-0001/setup-ingestion-from-zrapp)

    ```
    uv add httpx dlt dlt[duckdb]
    mkdir data
    echo "data/" >> .gitignore
    echo 'DLT_DESTINATION="duckdb"' >> .env
    ```


## Tasks

- [ ] feat-0001/setup-ingestion-from-zrapp