with

round_first_race as (
  select 
    event,
    event_start_epoch,
    event_distance
  from {{ ref("stg__zr__events") }}
  qualify row_number() over (partition by event order by event_start_epoch)=1
)

select 
    event, 
    replace(event, 'Zwift TT Club Racing - ', '') as stage_name, 
    row_number() over (order by event_start_epoch) as stage,
    event_distance as stage_distance
from round_first_race