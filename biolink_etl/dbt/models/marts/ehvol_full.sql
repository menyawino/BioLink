/*
    Mart/View: ehvol_full

    Purpose:
    - Expose the fully cleaned, typed, and renamed dataset.
    - Derived from 'ehvol_cleaned' staging model.

    This is the primary dataset for Superset exploration.
*/

{{ config(materialized='view') }}

select * from {{ ref('ehvol_cleaned') }}
