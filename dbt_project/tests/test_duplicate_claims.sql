-- Detects duplicate claim_id values submitted within a 30-day window
-- for the same provider and procedure. Returns rows that fail the check.

with claim_pairs as (
    select
        a.claim_id          as claim_id_a,
        b.claim_id          as claim_id_b,
        a.provider_npi,
        a.procedure_code,
        a.service_date      as date_a,
        b.service_date      as date_b,
        abs(datediff('day', a.service_date, b.service_date)) as days_apart
    from {{ ref('fct_claims') }} a
    join {{ ref('fct_claims') }} b
        on  a.provider_npi   = b.provider_npi
        and a.procedure_code = b.procedure_code
        and a.claim_id       < b.claim_id
    where abs(datediff('day', a.service_date, b.service_date)) <= 30
)

select * from claim_pairs
