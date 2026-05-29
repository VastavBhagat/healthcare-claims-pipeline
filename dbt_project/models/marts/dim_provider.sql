with providers as (
    select * from {{ ref('stg_cms_providers') }}
),

stats as (
    select * from {{ ref('int_claims_by_provider') }}
),

final as (
    select
        p.provider_npi,
        p.provider_name,
        p.provider_first_name,
        p.provider_city,
        p.provider_state,
        p.provider_zip,
        p.credentials,
        p.provider_type,
        p.medicare_participation_indicator,
        s.total_claims,
        s.total_payment,
        s.avg_payment_per_claim,
        s.first_service_date,
        s.last_service_date
    from providers p
    left join stats s on p.provider_npi = s.provider_npi
)

select * from final
