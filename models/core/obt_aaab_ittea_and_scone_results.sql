with

events as (
    select
        series_id,
        season_id,
        event_id,
        event_start_epoch
    from {{ ref("stg_events") }}
    where series_id='AAAB'
),

riders as (
    select
        series_id,
        season_id,
        rider_id
    from {{ ref("stg_riders") }}
    where series_id='AAAB'
),

results as (
    select
        *
    from {{ ref("int_results") }}
    where event_id in (select event_id from events) and rider_id in (select rider_id from riders)
)

-- approach to this should be to get all results, merge in series and season data for events and riders, then restrict
select * from results
