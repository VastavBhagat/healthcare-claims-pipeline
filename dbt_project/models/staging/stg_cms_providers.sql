with source as (
    select * from {{ source('cms', 'cms_providers') }}
),

cleaned as (
    select
        npi                                                 as provider_npi,
        initcap(nppes_provider_last_org_name)              as provider_name,
        initcap(nppes_provider_first_name)                 as provider_first_name,
        initcap(nppes_provider_city)                       as provider_city,
        upper(nppes_provider_state)                        as provider_state,
        nppes_provider_zip::varchar                        as provider_zip,
        lower(nppes_credentials)                           as credentials,
        lower(provider_type)                               as provider_type,
        medicare_participation_indicator,
        updated_at::timestamp_ntz                          as updated_at,
        _loaded_at,
        _source_file,
        _pipeline_run_id
    from source
    where npi is not null
)

select * from cleaned
