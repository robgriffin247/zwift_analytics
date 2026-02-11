with source as (
    select
        rider_id::int as rider_id,
    from {{ source("google_sheets", "riders") }}
)

select * from source