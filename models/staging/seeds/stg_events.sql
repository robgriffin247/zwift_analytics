with 

source as (
    select
        series_id::varchar as series_id,
        season_id::varchar as season_id,
        stage::varchar as stage,
        event_id::int as event_id,
    from {{ref("events")}}
)

select * from source