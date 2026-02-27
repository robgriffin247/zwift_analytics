with 

source as (
    select
        series_id::varchar as series_id,
        season_id::varchar as season_id,
        rider_id::int as rider_id
    from {{ref("riders")}}
)

select * from source