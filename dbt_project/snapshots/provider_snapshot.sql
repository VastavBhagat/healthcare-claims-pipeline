{% snapshot provider_snapshot %}

{{
    config(
        target_schema='SNAPSHOTS',
        unique_key='provider_npi',
        strategy='timestamp',
        updated_at='updated_at',
        invalidate_hard_deletes=True,
    )
}}

select
    provider_npi,
    provider_name,
    provider_first_name,
    provider_city,
    provider_state,
    provider_zip,
    credentials,
    provider_type,
    medicare_participation_indicator,
    updated_at
from {{ ref('stg_cms_providers') }}

{% endsnapshot %}
