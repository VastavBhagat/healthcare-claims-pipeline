with claims as (
    select * from {{ ref('stg_cms_claims') }}
),

providers as (
    select distinct
        provider_npi,
        provider_name,
        provider_first_name,
        provider_type,
        provider_state,
        'Y'                         as medicare_participation_indicator,
        _loaded_at                  as updated_at,
        _loaded_at,
        _source_file,
        _pipeline_run_id
    from claims
    where provider_npi is not null
)

select * from providers
