with 

source as (
    select
        event_id::int as event_id,
        to_timestamp(time::int) as event_start_epoch,
        distance::float as event_distance,
        elevation::int as event_elevation,
        title::varchar as event,
        _dlt_id::varchar as _dlt_id
    from {{ source("zwift_racing", "event_results")}}
)

select * from source