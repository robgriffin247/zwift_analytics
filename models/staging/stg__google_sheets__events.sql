with source as (
    select
        event_id::int as event_id,
        event_start_epoch::int as event_start_epoch,
        league_id::int as league_id
    from {{ source("google_sheets", "events") }}
)

select * from source