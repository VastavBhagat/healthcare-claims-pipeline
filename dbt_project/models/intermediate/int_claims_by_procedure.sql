with claims as (
    select * from {{ ref('stg_cms_claims') }}
),

aggregated as (
    select
        procedure_code,
        provider_state,
        count(distinct claim_id)                            as total_claims,
        sum(service_count)                                  as total_services,
        sum(submitted_amount)                               as total_submitted,
        sum(allowed_amount)                                 as total_allowed,
        sum(payment_amount)                                 as total_payment,
        avg(payment_amount)                                 as avg_payment,
        avg(allowed_amount)                                 as avg_allowed,
        -- used downstream for anomaly detection baseline
        stddev(payment_amount)                              as stddev_payment
    from claims
    group by procedure_code, provider_state
)

select * from aggregated
