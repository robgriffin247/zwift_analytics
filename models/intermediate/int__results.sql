with
gs_events as (
    select 
        league_id,
        event_id
    from {{ ref("stg__google_sheets__events")}}
),

zr_events as (
    select
        event_id,
        event_start_epoch,
        event_distance,
        event,
        _dlt_id
    from {{ ref("stg__zwift_racing__events")}}
),

velo_cats as (
    select
        category,
        womens,
        min,
        max
    from {{ ref("stg__seeds__velo_categories")}}
),

results as (
    select
        rider,
        rider_id,
        category_raced,
        race_seconds,
        velo_before,
        velo_after,
        velo_90_day_max,
        _dlt_parent_id
    from {{ ref("stg__zwift_racing__results") }}
),

stages as (
    select
        event,
        stage_name,
        stage
    from {{ ref("int__stages") }}
),

results_with_event_details as (
    select 
        gs_events.league_id,
        zr_events.* exclude(_dlt_id),
        stages.stage,
        stages.stage_name,
        results.* exclude(_dlt_parent_id),
        zr_events.event_distance / results.race_seconds * 3600 as race_speed
    from results
        left join zr_events on results._dlt_parent_id=zr_events._dlt_id
        left join gs_events using(event_id)
        left join stages using(event)
),

results_with_velo_cats as (
    select
        results_with_event_details.*,
        velo_cats.category as velo_category
    from results_with_event_details
        left join (select * from velo_cats where not womens) as velo_cats on results_with_event_details.velo_before between velo_cats.min and velo_cats.max
)

select * from results_with_velo_cats