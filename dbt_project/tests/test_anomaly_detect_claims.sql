-- Flags claims where payment_amount deviates more than 3 standard deviations
-- from the provider's historical average. Returns rows that fail the check.

with provider_stats as (
    select
        provider_npi,
        avg(payment_amount)     as avg_payment,
        stddev(payment_amount)  as stddev_payment
    from {{ ref('fct_claims') }}
    group by provider_npi
),

anomalies as (
    select
        f.claim_id,
        f.provider_npi,
        f.payment_amount,
        ps.avg_payment,
        ps.stddev_payment,
        (f.payment_amount - ps.avg_payment) / nullif(ps.stddev_payment, 0) as z_score
    from {{ ref('fct_claims') }} f
    join provider_stats ps on f.provider_npi = ps.provider_npi
    where ps.stddev_payment > 0
      and f.payment_amount > ps.avg_payment + (3 * ps.stddev_payment)
)

select * from anomalies
