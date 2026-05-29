with claims as (
    select * from {{ ref('stg_cms_claims') }}
),

aggregated as (
    select
        provider_npi,
        provider_state,
        count(distinct claim_id)                            as total_claims,
        sum(service_count)                                  as total_services,
        sum(beneficiary_count)                              as total_beneficiaries,
        sum(submitted_amount)                               as total_submitted,
        sum(allowed_amount)                                 as total_allowed,
        sum(payment_amount)                                 as total_payment,
        avg(payment_amount)                                 as avg_payment_per_claim,
        stddev(payment_amount)                              as stddev_payment,
        min(service_date)                                   as first_service_date,
        max(service_date)                                   as last_service_date
    from claims
    group by provider_npi, provider_state
)

select * from aggregated
