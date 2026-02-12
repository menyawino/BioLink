/*
    Mart: patients table — maps cleaned EHVol staging data into the
    canonical patients schema used by the BioLink backend and Superset.
*/

{{ config(materialized='table') }}

with stg as (

    select * from {{ ref('ehvol_cleaned') }}

)

select
    -- include every column produced by the staging model so any CSV with extra
    -- columns is preserved into the mart. Keep the dna_id filter to avoid
    -- creating rows without an identifier.
    stg.*
from stg
where stg.dna_id is not null
