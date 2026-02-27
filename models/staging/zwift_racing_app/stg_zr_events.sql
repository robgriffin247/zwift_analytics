with 

source as (
    select
        event_id::int as event_id,
        distance::float as event_distance,
        title::varchar as event,
        _dlt_id::varchar as _dlt_id
    from {{ source("zwift_racing", "event_results")}}
)

select * from source