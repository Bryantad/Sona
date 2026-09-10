from contextlib import contextmanager

import pytest

from sona.proof import ProofDiagnostic, verify_receipt_payload


def test_proof_diagnostic_survives_context_manager_exception_propagation():
    @contextmanager
    def passthrough():
        yield

    with pytest.raises(ProofDiagnostic) as caught, passthrough():
        verify_receipt_payload({"schema": 1}, b"not canonical\r\n")
    assert caught.value.diagnostic_id == "PROOF-VERIFY-004"
    assert caught.value.__traceback__ is not None
