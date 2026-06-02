with claims as (
    select * from {{ ref('stg_cms_claims') }}
),

procedures as (
    select distinct
        procedure_code,
        procedure_description,
        'N'                         as drug_indicator,
        type_of_service             as procedure_category
    from claims
    where procedure_code is not null
)

select * from procedures
