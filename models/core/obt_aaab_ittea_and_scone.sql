with

constants as (
    select
        'AAAB' as series_id
),

results as (
    select
        event_id,
        event_start_epoch,
        replace(event, 'Zwift TT Club Racing - ', '') as event,
        event_distance,
        event_elevation,
        rider_id,
        rider,
        category_raced,
        race_milliseconds,
        race_speed,
        velo_at_start,
        velo_at_finish,
        velo_90_day_max,
        velo_category_at_start,
        velo_category_at_finish,
        velo_category_90_day_max
    from {{ ref("int_results") }}
    where rider_id in (select rider_id from {{ ref("stg_riders") }} where series_id=(select series_id from constants))
        and event_id in (select event_id from {{ ref("stg_events") }} where series_id=(select series_id from constants))
),

events as (
    select
        series_id,
        season_id,
        stage,
        event_id,
    from {{ ref("stg_events") }}
    where series_id=(select series_id from constants)
),

events_details_on_results as (
    select
        events.*,
        results.* exclude(event_id)
    from results left join events using(event_id)
),

derive_category as (
    select
        *,
        first(category_raced) over (partition by season_id, rider_id order by category_raced) as season_category
    from events_details_on_results
),

best_efforts as (
    select
        *,
        row_number() over (partition by season_id, rider_id, stage order by race_milliseconds)=1 as is_best_effort
    from derive_category
),

add_ranks as (
    select
        *,
        case when is_best_effort then row_number() over (partition by season_id, stage, is_best_effort order by race_milliseconds) else null end as overall_rank,
        case when is_best_effort then row_number() over (partition by season_id, stage, is_best_effort, category_raced order by race_milliseconds) else null end as category_rank
    from best_efforts
),

easter_eggs as (
    select * exclude(rider),
        case when rider_id=292691 then rider || '❤️England' else rider end as rider,
        case when rider_id=5083506 and event_id=5393497 then 0.5 else 1 end as effort_counter
    from add_ranks
),

select_cols as (
    select 
        season_id,
        stage,
        event_id,
        event_start_epoch,
        event,
        event_distance,
        event_elevation,
        rider_id,
        rider,
        season_category,
        category_raced,
        overall_rank,
        category_rank,
        race_milliseconds,
        race_speed,
        velo_at_start,
        velo_category_at_start,
        effort_counter,
        is_best_effort,
    from easter_eggs
)

select * from select_cols order by season_id, stage, race_milliseconds