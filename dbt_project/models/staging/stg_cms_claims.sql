with source as (
    select * from {{ source('cms_raw', 'RAW_CLAIMS') }}
),

cleaned as (
    select
        md5(rndrng_npi || hcpcs_cd || rndrng_prvdr_state_cd)
                                            as claim_id,
        rndrng_npi                          as provider_npi,
        rndrng_prvdr_last_org               as provider_name,
        rndrng_prvdr_first                  as provider_first_name,
        rndrng_prvdr_type                   as provider_type,
        upper(trim(rndrng_prvdr_state_cd))  as provider_state,
        hcpcs_cd                            as procedure_code,
        hcpcs_desc                          as procedure_description,
        tot_benes                           as beneficiary_count,
        tot_srvcs                           as service_count,
        avg_sbmtd_chrg                      as submitted_amount,
        avg_mdcr_alowd_amt                  as allowed_amount,
        avg_mdcr_pymt_amt                   as payment_amount,
        rndrng_prvdr_type                   as place_of_service,
        'B'                                 as type_of_service,
        _loaded_at::date                    as service_date,
        round(avg_mdcr_pymt_amt / nullif(avg_sbmtd_chrg, 0) * 100, 2)
                                            as payment_to_charge_ratio,
        _loaded_at,
        _source_file,
        _pipeline_run_id
    from source
    where rndrng_npi is not null
      and avg_mdcr_pymt_amt is not null
)

select * from cleaned
