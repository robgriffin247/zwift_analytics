with 

source as (
    select * from {{ source("zrapp", "riders")}}
)

select * from source