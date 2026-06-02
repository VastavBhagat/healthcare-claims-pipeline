with source as (
    select * from {{ source('cms_raw', 'RAW_CLAIMS') }}
),

cleaned as (
    select
        rndrng_npi                          as provider_npi,
        rndrng_prvdr_last_org               as provider_name,
        rndrng_prvdr_first                  as provider_first_name,
        rndrng_prvdr_type                   as provider_type,
        upper(trim(rndrng_prvdr_state_cd))  as state_code,
        hcpcs_cd                            as procedure_code,
        hcpcs_desc                          as procedure_description,
        tot_benes                           as total_beneficiaries,
        tot_srvcs                           as total_services,
        avg_sbmtd_chrg                      as avg_submitted_charge,
        avg_mdcr_alowd_amt                  as avg_allowed_amount,
        avg_mdcr_pymt_amt                   as avg_payment_amount,

        -- derived columns
        round(avg_mdcr_pymt_amt / nullif(avg_submitted_charge, 0) * 100, 2)
                                            as payment_to_charge_ratio,

        -- metadata
        _loaded_at,
        _source_file,
        _pipeline_run_id

    from source
    where provider_npi is not null
      and avg_mdcr_pymt_amt is not null
)

select * from cleaned