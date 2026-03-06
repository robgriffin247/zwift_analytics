with

constants as (
    select
        'AAAA' as series_id
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
    where event_id in (select event_id from {{ ref("stg_events") }} where series_id=(select series_id from constants))
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
        case when is_best_effort then row_number() over (partition by season_id, stage, is_best_effort, season_category order by race_milliseconds) else null end as season_cat_rank,
        case when is_best_effort then row_number() over (partition by season_id, stage, is_best_effort, category_raced order by race_milliseconds) else null end as stage_cat_rank,
    from best_efforts
),

select_cols as (
    select 
        season_id::int as season_id,
        season_id::int || '-' || stage as round_id,
        stage || '. ' || event as stage,
        event_id,
        event_start_epoch,
        event_distance,
        event_elevation,
        rider_id,
        rider,
        season_category,
        category_raced,
        overall_rank,
        season_cat_rank,
        stage_cat_rank,
        race_milliseconds,
        race_speed,
        velo_at_start,
        velo_category_at_start,
        is_best_effort,
    from add_ranks
)

select * from select_cols order by season_id, stage, race_milliseconds