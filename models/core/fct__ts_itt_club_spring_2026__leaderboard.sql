with

best_results as (
    select 
        event,
        rider_id,
        rider,
        category,
        velo_start,
        velo_start_category,
        race_seconds
    from {{ ref("fct__ts_itt_club_spring_2026__best_results") }}
),

leaderboard as (
    select 
        rider_id, 
        rider,
        category,
        velo_start,
        velo_start_category,    
        count(*) as races, 
        sum(race_seconds) as total_seconds
    from best_results
    group by all
    order by races desc, total_seconds
),

formatted_leaderboard as (
    select 
        *,
        {{ format_seconds_to_time("total_seconds") }} as total_time
    from leaderboard
)

select * from formatted_leaderboard
