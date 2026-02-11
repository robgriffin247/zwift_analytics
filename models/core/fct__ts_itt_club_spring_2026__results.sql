with

results as (
    select
        event_id,
        event,
        event_start_epoch,
        rider_id,
        rider,
        velo_before,
        velo_category,
        category_raced,
        race_seconds,
        {{ format_seconds_to_time("race_seconds") }} as race_time,
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
        velo_before as velo_start,
        velo_category as velo_start_category,
    from results
    qualify row_number() over (partition by rider_id order by event_start_epoch)=1
),

add_categories as (
    select
        results.*,
        categories.category,
        velo_cats.velo_start,
        velo_cats.velo_start_category,
    from results 
        left join categories using(rider_id)
        left join velo_cats using(rider_id)
)

select * from add_categories