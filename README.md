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
    echo ".env" >> .gitignore
    echo 'ZRAPP_API_KEY="<ZRAPP_API_KEY>"' >> .env
    ```

    - Replace ``<ZRAPP_API_KEY>`` with your API key

1. Ingestion (feat-0001/setup-ingestion-from-zrapp)



## Tasks

- [ ] feat-0001/setup-ingestion-from-zrapp