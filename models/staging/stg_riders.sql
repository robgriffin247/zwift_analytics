with 

source as (
  select * 
  from {{ source("zrapp", "riders")}}
),

select_type_and_rename as (
  select
    rider_id::int as rider_id,
    name::varchar as rider,
    club__id::int as club_id,
    club__name::varchar as club,
    race__max90__rating::decimal as velo_90_day_peak,
    race__max90__mixed__category::varchar as velo_90_day_peak_category,
    race__max90__mixed__number::varchar as velo_90_day_peak_category_number,
    zp_category::varchar as zwift_category,
    zp_ftp::int as ftp_watts,
    weight::decimal as weight_kg,
    power__w5::int as watts_5s,
    power__w15::int as watts_15s,
    power__w30::int as watts_30s,
    power__w60::int as watts_60s,
    power__w120::int as watts_120s,
    power__w300::int as watts_300s,
    power__w1200::int as watts_1200s,
    power__wkg5::decimal as watts_kg_5s,
    power__wkg15::decimal as watts_kg_15s,
    power__wkg30::decimal as watts_kg_30s,
    power__wkg60::decimal as watts_kg_60s,
    power__wkg120::decimal as watts_kg_120s,
    power__wkg300::decimal as watts_kg_300s,
    power__wkg1200::decimal as watts_kg_1200s,
    race__finishes::int as races,
    race__wins::int as race_wins,
    race__podiums::int as race_podiums,
    handicaps__profile__flat::decimal as handicap_flat,
    handicaps__profile__rolling::decimal as handicap_rolling,
    handicaps__profile__hilly::decimal as handicap_hilly,
    handicaps__profile__mountainous::decimal as handicap_mountainous,
    phenotype__scores__sprinter::decimal as phenotype_sprinter,
    phenotype__scores__puncheur::decimal as phenotype_puncheur,
    phenotype__scores__pursuiter::decimal as phenotype_pursuiter,
    phenotype__scores__climber::decimal as phenotype_climber,
    phenotype__scores__tt::decimal as phenotype_tt,
    _dlt_load_id::decimal as _dlt_load_id
  from source
)

select * from select_type_and_rename