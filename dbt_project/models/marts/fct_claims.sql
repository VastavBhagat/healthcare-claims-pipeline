with claims as (
    select * from {{ ref('stg_cms_claims') }}
),

provider_stats as (
    select * from {{ ref('int_claims_by_provider') }}
),

procedure_stats as (
    select * from {{ ref('int_claims_by_procedure') }}
),

final as (
    select
        c.claim_id,
        c.provider_npi,
        c.procedure_code,
        c.place_of_service,
        c.type_of_service,
        c.provider_state,
        c.service_date,
        c.submitted_amount,
        c.allowed_amount,
        c.payment_amount,
        c.service_count,
        c.beneficiary_count,
        -- anomaly flag: payment > 3 standard deviations from provider's average
        case
            when ps.stddev_payment > 0
             and c.payment_amount > ps.avg_payment_per_claim + (3 * ps.stddev_payment)
            then true
            else false
        end                                                 as is_payment_anomaly,
        c._loaded_at,
        c._source_file,
        c._pipeline_run_id
    from claims c
    left join provider_stats ps
        on c.provider_npi = ps.provider_npi
        and c.provider_state = ps.provider_state
)

select * from final
