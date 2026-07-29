import pytest

from tools.release.promote_0153 import validate_current_checks


def test_pr_checks_must_belong_to_current_head_and_all_succeed() -> None:
    head = "a" * 40
    passing = {
        "headRefOid": head,
        "statusCheckRollup": [
            {"name": "python", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"name": "native", "status": "COMPLETED", "conclusion": "SUCCESS"},
        ],
    }
    validate_current_checks(passing, head)
    validate_current_checks(
        {
            "headRefOid": head,
            "statusCheckRollup": [
                {"context": "legacy-status", "state": "SUCCESS"},
            ],
        },
        head,
    )

    stale = {**passing, "headRefOid": "b" * 40}
    with pytest.raises(RuntimeError, match="earlier head SHA"):
        validate_current_checks(stale, head)

    failed = {
        **passing,
        "statusCheckRollup": [
            {"name": "native", "status": "COMPLETED", "conclusion": "FAILURE"}
        ],
    }
    with pytest.raises(RuntimeError, match="incomplete or unsuccessful"):
        validate_current_checks(failed, head)

    ambiguous = {
        **passing,
        "statusCheckRollup": [{"name": "native"}],
    }
    with pytest.raises(RuntimeError, match="incomplete or unsuccessful"):
        validate_current_checks(ambiguous, head)


def test_pr_without_certification_checks_is_not_mergeable() -> None:
    with pytest.raises(RuntimeError, match="no certification checks"):
        validate_current_checks({"headRefOid": "a" * 40, "statusCheckRollup": []}, "a" * 40)
