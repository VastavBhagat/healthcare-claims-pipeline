with procedures as (
    select * from {{ ref('stg_cms_procedures') }}
),

stats as (
    select
        procedure_code,
        sum(total_claims)       as total_claims,
        sum(total_payment)      as total_payment,
        avg(avg_payment)        as avg_payment_national
    from {{ ref('int_claims_by_procedure') }}
    group by procedure_code
),

final as (
    select
        p.procedure_code,
        p.procedure_description,
        p.drug_indicator,
        p.procedure_category,
        s.total_claims,
        s.total_payment,
        round(s.avg_payment_national, 2)    as avg_payment_national
    from procedures p
    left join stats s on p.procedure_code = s.procedure_code
)

select * from final
