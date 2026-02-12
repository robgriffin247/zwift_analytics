with

best_results as (
    select 
        stage,
        stage_name,
        rider_id,
        rider,
        category,
        velo_first,
        velo_first_category,
        race_seconds
    from {{ ref("fct__ts_itt_club_spring_2026__results") }}
    where is_best_effort
),

leaderboard as (
    select 
        rider_id, 
        rider,
        category,
        velo_first,
        velo_first_category,    
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
