-- One row per rider per event; not per series/season (so if an event is used in >1 series/season, it is one row here)
with

zr_results as (
    select
        rider_id,
        rider,
        category_raced,
        race_seconds,
        velo_at_start,
        velo_at_finish,
        velo_90_day_max,
        _dlt_parent_id as dlt_event_id
    from {{ ref("stg_zr_results") }}
),

zr_events as (
    select
        event_id,
        event_start_epoch,
        event,
        event_distance,
        event_elevation,
        _dlt_id as dlt_event_id
    from {{ ref("stg_zr_events") }}
),

velo_cats as (
    select
        category,
        womens,
        min,
        max
    from {{ ref("stg_velo_categories")}}
),

add_event_data_to_results as (
    select
        zr_events.event_id,
        zr_events.event_start_epoch,
        zr_events.event,
        zr_events.event_distance,
        zr_events.event_elevation,
        zr_results.* exclude(dlt_event_id)
    from zr_results
        left join zr_events using(dlt_event_id)
),

add_velo_cats as (
    select
        add_event_data_to_results.*,
        velo_start.category as velo_category_at_start,
        velo_finish.category as velo_category_at_finish,
        velo_90.category as velo_category_90_day_max,
    from add_event_data_to_results
        left join (select * from velo_cats where not womens) as velo_start
            on add_event_data_to_results.velo_at_start between velo_start.min and velo_start.max
        left join (select * from velo_cats where not womens) as velo_finish
            on add_event_data_to_results.velo_at_finish between velo_finish.min and velo_finish.max
        left join (select * from velo_cats where not womens) as velo_90
            on add_event_data_to_results.velo_90_day_max between velo_90.min and velo_90.max
),

select_cols as (
    select
        event_id,
        event_start_epoch,
        event,
        event_distance,
        event_elevation,
        rider_id,
        last(rider) over (partition by rider_id order by event_start_epoch rows between unbounded preceding and unbounded following) as rider,
        category_raced,
        (race_seconds*1000)::int as race_milliseconds,
        (event_distance/race_seconds) * 3600 as race_speed,
        velo_at_start,
        velo_at_finish,
        velo_90_day_max,
        velo_category_at_start,
        velo_category_at_finish,
        velo_category_90_day_max
    from add_velo_cats
    )

select * from select_cols