import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_blob_service(mocker):
    mock = MagicMock()
    mocker.patch(
        "ingestion.upload_to_blob.BlobServiceClient.from_connection_string",
        return_value=mock,
    )
    return mock


@pytest.fixture
def sample_cms_record():
    return {
        "npi": "1234567890",
        "claim_id": "CLM-001",
        "hcpcs_code": "99213",
        "place_of_service": "Office",
        "service_date": "2023-01-15",
        "submitted_charge_amount": "150.00",
        "medicare_allowed_amount": "85.00",
        "medicare_payment_amount": "68.00",
        "line_srvc_cnt": "1",
        "bene_unique_cnt": "1",
        "nppes_provider_state": "CA",
    }
