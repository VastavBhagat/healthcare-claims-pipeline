with source as (
    select * from {{ source('cms', 'cms_procedures') }}
),

cleaned as (
    select
        hcpcs_code                                  as procedure_code,
        initcap(hcpcs_description)                  as procedure_description,
        lower(hcpcs_drug_indicator)                 as drug_indicator,
        lower(hcpcs_category)                       as procedure_category
    from source
    where hcpcs_code is not null
)

select * from cleaned
