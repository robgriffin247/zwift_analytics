with 

source as (
    select
        rider_id::int as rider_id,
        trim(name::varchar) as rider,
        category::varchar as category_raced,
        time::float as race_seconds,
        case when rating_before::float>0 then rating_before::float else null end as velo_at_start,
        case when rating::float>0 then rating::float else null end as velo_at_finish,
        case when rating_max90::float>0 then rating_max90::float else null end as velo_90_day_max,
        _dlt_parent_id::varchar as _dlt_parent_id
    from {{ source("zwift_racing", "event_results__results")}}
    -- remove DNFs
    where not (rating_delta is null and gap is null and gap__v_double is null and position is not null and time::int=time)
)

select * from source