with
round_first_race as (
  select 
    event,
    event_start_epoch
  from {{ ref("stg__zwift_racing__events") }}
  qualify row_number() over (partition by event order by event_start_epoch)=1
)

select 
    event, 
    replace(event, 'Zwift TT Club Racing - ', '') as round_name, 
    row_number() over (order by event_start_epoch) as round 
from round_first_race