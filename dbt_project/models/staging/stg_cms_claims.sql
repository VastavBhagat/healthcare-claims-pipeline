with source as (
    select * from {{ source('cms', 'cms_claims') }}
),

cleaned as (
    select
        claim_id,
        npi                                         as provider_npi,
        hcpcs_code                                  as procedure_code,
        lower(place_of_service)                     as place_of_service,
        lower(type_of_service)                      as type_of_service,
        upper(nppes_provider_state)                 as provider_state,
        service_date::date                          as service_date,
        submitted_charge_amount::float              as submitted_amount,
        medicare_allowed_amount::float              as allowed_amount,
        medicare_payment_amount::float              as payment_amount,
        line_srvc_cnt::int                          as service_count,
        bene_unique_cnt::int                        as beneficiary_count,
        -- row-level audit columns
        _loaded_at,
        _source_file,
        _pipeline_run_id
    from source
    where claim_id is not null
      and npi is not null
)

select * from cleaned
