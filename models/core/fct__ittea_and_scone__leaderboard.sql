with

best_results as (
    select 
        season_id,
        stage,
        stage_name,
        rider_id,
        rider,
        category,
        velo_first,
        velo_first_category,
        race_seconds
    from {{ ref("fct__ittea_and_scone__results") }}
    where is_best_effort
),

leaderboard as (
    select 
        season_id,
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

add_gap as (
    select *,
        total_seconds - min(total_seconds) over (partition by races order by races desc, total_seconds) as gap 
    from leaderboard
),

formatted_leaderboard as (
    select 
        * exclude(gap),
        row_number() over (partition by season_id order by races desc, total_seconds) as overall_rank,
        row_number() over (partition by season_id, category order by races desc, total_seconds) as category_rank,
        {{ format_seconds_to_time("total_seconds") }} as total_time,
        case when gap=0 then ' ' else '+ ' || {{ format_seconds_to_time("gap", false) }} end as gap
    from add_gap
)

select * from formatted_leaderboard order by races desc, total_seconds