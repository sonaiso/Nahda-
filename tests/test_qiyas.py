"""Tests for the Qiyas (analogical reasoning) pipeline and API endpoint."""

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.qiyas_pipeline import DaalType
from app.services.qiyas_pipeline import QiyasTransferInput
from app.services.qiyas_pipeline import _evaluate_preconditions
from tests.auth_helpers import get_auth_headers


# ---------------------------------------------------------------------------
# Unit tests — pipeline internals
# ---------------------------------------------------------------------------


def test_daal_type_values() -> None:
    """DaalType enum must contain the six canonical values and nothing else."""
    expected = {"mutabaqa", "tadammun", "iltizam", "nass", "zahir", "mafhum"}
    assert {d.value for d in DaalType} == expected


def test_daal_type_no_aliases() -> None:
    """DaalForm and DaalFunction must not exist as DaalType members."""
    member_names = {m.name for m in DaalType}
    assert "DAALFORM" not in member_names
    assert "DAALFUNCTION" not in member_names
    # Also verify as attribute access
    assert not hasattr(DaalType, "DaalForm")
    assert not hasattr(DaalType, "DaalFunction")


def test_preconditions_valid_illa_in_both() -> None:
    transfer = QiyasTransferInput(
        asl_text="لا كتاب في البيت",
        asl_judgment="prohibit:كتاب",
        far_text="لا مجلة في البيت المطبوع",
        illa_description="المطبوع",
        daal_type=DaalType.MUTABAQA,
    )
    passes, rationale, confidence = _evaluate_preconditions(transfer)
    assert passes is True
    assert confidence > 0


def test_preconditions_empty_illa() -> None:
    transfer = QiyasTransferInput(
        asl_text="لا كتاب في البيت",
        asl_judgment="prohibit:كتاب",
        far_text="لا مجلة في البيت",
        illa_description="",
        daal_type=DaalType.MUTABAQA,
    )
    passes, rationale, confidence = _evaluate_preconditions(transfer)
    assert passes is False
    assert confidence == 0.0


def test_preconditions_mafhum_without_explicit_illa() -> None:
    """Mafhum transfers should be allowed even when illa is not literally in texts."""
    transfer = QiyasTransferInput(
        asl_text="الكتاب مكتوب",
        asl_judgment="allow:كتاب",
        far_text="الصحيفة مطبوعة",
        illa_description="الطباعة الرقمية",  # words not in either text
        daal_type=DaalType.MAFHUM,
    )
    passes, rationale, confidence = _evaluate_preconditions(transfer)
    assert passes is True
    assert confidence > 0.30


def test_preconditions_nass_highest_confidence() -> None:
    transfer = QiyasTransferInput(
        asl_text="النص موجود",
        asl_judgment="allow:نص",
        far_text="الآية النص محفوظة",
        illa_description="النص",
        daal_type=DaalType.NASS,
    )
    passes_nass, _, conf_nass = _evaluate_preconditions(transfer)

    transfer_iltizam = QiyasTransferInput(
        asl_text="النص موجود",
        asl_judgment="allow:نص",
        far_text="الآية النص محفوظة",
        illa_description="النص",
        daal_type=DaalType.ILTIZAM,
    )
    passes_iltizam, _, conf_iltizam = _evaluate_preconditions(transfer_iltizam)

    assert passes_nass and passes_iltizam
    assert conf_nass > conf_iltizam


# ---------------------------------------------------------------------------
# Integration tests — API endpoint
# ---------------------------------------------------------------------------

TEXT = "لا كتاب في البيت"
VALID_TRANSFER = {
    "asl_text": TEXT,
    "asl_judgment": "prohibit:كتاب",
    "far_text": "لا مجلة في البيت",
    "illa_description": "المطبوع الورقي",
    "daal_type": "mutabaqa",
    "evidence": [
        {"text": "الكتاب والمجلة كلاهما مطبوع ورقي", "source": "nass", "strength": "zanni"}
    ],
}


def test_qiyas_transfer_valid() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        resp = client.post(
            "/qiyas/transfer",
            json={"text": TEXT, "transfers": [VALID_TRANSFER]},
            headers=headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"]
    assert len(data["transfers"]) == 1
    transfer = data["transfers"][0]
    assert transfer["transfer_state"] == "valid"
    assert transfer["transferred_judgment"] == "prohibit:كتاب"
    assert transfer["daal_type"] == "mutabaqa"
    assert data["metrics"]["valid_count"] == 1
    assert data["metrics"]["suspend_count"] == 0


def test_qiyas_transfer_suspend_on_empty_asl_judgment() -> None:
    """Transfer must be suspended when asl_judgment is empty (not 422)."""
    bad_transfer = {**VALID_TRANSFER, "asl_judgment": " "}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        resp = client.post(
            "/qiyas/transfer",
            json={"text": TEXT, "transfers": [bad_transfer]},
            headers=headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    transfer = data["transfers"][0]
    assert transfer["transfer_state"] == "suspend"
    assert data["metrics"]["suspend_count"] == 1


def test_qiyas_transfer_suspend_on_empty_illa_description() -> None:
    """Transfer must be suspended when illa_description is empty (not 422)."""
    bad_transfer = {**VALID_TRANSFER, "illa_description": ""}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        resp = client.post(
            "/qiyas/transfer",
            json={"text": TEXT, "transfers": [bad_transfer]},
            headers=headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    transfer = data["transfers"][0]
    assert transfer["transfer_state"] == "suspend"
    assert data["metrics"]["suspend_count"] == 1


def test_qiyas_transfer_multiple() -> None:
    second_transfer = {
        "asl_text": TEXT,
        "asl_judgment": "prohibit:كتاب",
        "far_text": "لا صحيفة في البيت",
        "illa_description": "المطبوع",
        "daal_type": "tadammun",
        "evidence": [],
    }
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        resp = client.post(
            "/qiyas/transfer",
            json={"text": TEXT, "transfers": [VALID_TRANSFER, second_transfer]},
            headers=headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["transfers"]) == 2
    assert data["metrics"]["transfer_count"] == 2


def test_qiyas_transfer_invalid_daal_type() -> None:
    bad = {**VALID_TRANSFER, "daal_type": "unknown_type"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        resp = client.post(
            "/qiyas/transfer",
            json={"text": TEXT, "transfers": [bad]},
            headers=headers,
        )
    assert resp.status_code == 422


def test_qiyas_transfer_requires_auth() -> None:
    with TestClient(create_app()) as client:
        resp = client.post(
            "/qiyas/transfer",
            json={"text": TEXT, "transfers": [VALID_TRANSFER]},
        )
    assert resp.status_code == 401


def test_qiyas_transfer_empty_text_rejected() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        resp = client.post(
            "/qiyas/transfer",
            json={"text": "   ", "transfers": [VALID_TRANSFER]},
            headers=headers,
        )
    assert resp.status_code == 422


def test_qiyas_transfer_empty_transfers_rejected() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        resp = client.post(
            "/qiyas/transfer",
            json={"text": TEXT, "transfers": []},
            headers=headers,
        )
    assert resp.status_code == 422


def test_qiyas_transfer_daal_links_recorded() -> None:
    """Evidence items must be reflected in the daal_links output."""
    evidence = [
        {"text": "دليل أول", "source": "nass", "strength": "qat_i"},
        {"text": "دليل ثان", "source": "naql", "strength": "zanni"},
    ]
    transfer_with_evidence = {**VALID_TRANSFER, "evidence": evidence}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        resp = client.post(
            "/qiyas/transfer",
            json={"text": TEXT, "transfers": [transfer_with_evidence]},
            headers=headers,
        )
    assert resp.status_code == 200
    links = resp.json()["transfers"][0]["daal_links"]
    assert len(links) == 2
    assert links[0]["evidence_text"] == "دليل أول"
    assert links[0]["strength"] == "qat_i"


def test_qiyas_transfer_with_existing_run_id() -> None:
    """Providing run_id anchors transfers to an existing run instead of
    creating a new inference pass."""
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)

        # Create a run first via the infer endpoint
        infer_resp = client.post("/infer", json={"text": TEXT}, headers=headers)
        assert infer_resp.status_code == 200
        existing_run_id = infer_resp.json()["run_id"]

        # Now anchor Qiyas to that existing run
        resp = client.post(
            "/qiyas/transfer",
            json={
                "text": TEXT,
                "run_id": existing_run_id,
                "transfers": [VALID_TRANSFER],
            },
            headers=headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    # The returned run_id must be the same as the one we supplied
    assert data["run_id"] == existing_run_id
    assert data["metrics"]["valid_count"] == 1


def test_qiyas_transfer_unknown_run_id_returns_404() -> None:
    """Supplying an unknown run_id must return 404."""
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        resp = client.post(
            "/qiyas/transfer",
            json={
                "text": TEXT,
                "run_id": "00000000-0000-0000-0000-000000000000",
                "transfers": [VALID_TRANSFER],
            },
            headers=headers,
        )
    assert resp.status_code == 404
