with

results as (
    select
        event_id,
        stage,
        stage_name,
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
    where league_id in (3165) and rider_id in (select rider_id from {{ ref("stg__google_sheets__riders") }})
),

categories as (
    select
        rider_id,
        category_raced as category
    from results
    qualify row_number() over (partition by rider_id order by category desc)=1
),

velo_cats as (
    select
        rider_id,
        velo as velo_first,
        velo_category as velo_first_category,
    from results
    qualify row_number() over (partition by rider_id order by event_start_epoch)=1
),

add_categories as (
    select
        results.*,
        categories.category,
        velo_cats.velo_first,
        velo_cats.velo_first_category,
    from results 
        left join categories using(rider_id)
        left join velo_cats using(rider_id)
),

add_best_effort as (
    select
        *,
        row_number() over (partition by rider_id, stage order by race_seconds)=1 as is_best_effort
    from add_categories
)

select * from add_best_effort order by rider, stage