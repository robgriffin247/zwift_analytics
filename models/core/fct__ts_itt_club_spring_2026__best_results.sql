with

results as (
    select 
        event,
        rider_id,
        rider,
        category,
        velo_before,
        velo_category,
        velo_start,
        velo_start_category,
        race_seconds,
        race_time,
        race_speed
    from {{ ref("fct__ts_itt_club_spring_2026__results") }}
),

best_efforts as (
    select * 
    from results 
    qualify row_number() over (partition by rider_id, event order by race_seconds)=1
)

select * from best_efforts
