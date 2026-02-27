with source as (
    select
        season_id::int as season_id,
        league_id::int as league_id
    from {{ source("google_sheets", "seasons") }}
)

select * from source