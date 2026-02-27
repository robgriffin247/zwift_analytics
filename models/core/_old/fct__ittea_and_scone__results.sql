with

results as (
    select
        event_id,
        season_id,
        stage,
        stage_name,
        stage_distance,
        event_start_epoch,
        event_start_datetime,
        rider_id,
        rider,
        velo,
        velo_category,
        category_raced,
        race_seconds,
        race_time,
        race_speed
    from {{ ref("int__results") }}
    where season_id in (select season_id from {{ ref("stg__google_sheets__seasons") }} ) and 
        rider_id in (select rider_id from {{ ref("stg__google_sheets__riders") }})
),

categories as (
    select
        rider_id,
        season_id,
        category_raced as category
    from results
    qualify row_number() over (partition by season_id, rider_id order by category)=1
),

velo_cats as (
    select
        rider_id,
        season_id,
        velo as velo_first,
        velo_category as velo_first_category,
    from results
    qualify row_number() over (partition by rider_id, season_id order by event_start_epoch)=1
),

add_categories as (
    select
        results.*,
        categories.category,
        velo_cats.velo_first,
        velo_cats.velo_first_category,
    from results 
        left join categories using(rider_id, season_id)
        left join velo_cats using(rider_id, season_id)
),

add_best_effort as (
    select
        *,
        row_number() over (partition by rider_id, season_id, stage order by race_seconds)=1 as is_best_effort
    from add_categories
),

add_placings as (
    select *,
        case when is_best_effort then row_number() over (partition by season_id, stage, is_best_effort order by race_seconds) else null end as overall_placing,
        case when is_best_effort then row_number() over (partition by season_id, stage, category_raced, is_best_effort order by race_seconds) else null end as category_placing
    from add_best_effort
),

add_easter_eggs as (
    select * exclude(rider),
        case when rider_id=292691 then rider || '❤️England' else rider end as rider,
        case when rider_id=5083506 and event_id=5393497 then 0.5 else 1 end as effort_counter
    from add_placings
)

select * from add_easter_eggs order by season_id, stage, race_seconds