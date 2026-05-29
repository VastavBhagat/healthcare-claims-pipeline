with claims as (
    select * from {{ ref('stg_cms_claims') }}
),

region_stats as (
    select
        provider_state,
        count(distinct claim_id)            as total_claims,
        count(distinct provider_npi)        as total_providers,
        sum(payment_amount)                 as total_payment,
        avg(payment_amount)                 as avg_payment_per_claim,
        sum(beneficiary_count)              as total_beneficiaries
    from claims
    group by provider_state
)

select * from region_stats
