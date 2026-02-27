with 

source as (
    select
        series_id::varchar as series_id,
        season_id::varchar as season_id,
        event_id::int as event_id,
        start_epoch::int as event_start_epoch 
    from {{ref("events")}}
)

select * from source