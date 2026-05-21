import pytest


def test_public_memory_surface_exports_models_only():
    from sona.runtime.memory import Episode, Goal

    assert Episode.__name__ == "Episode"
    assert Goal.__name__ == "Goal"


def test_public_memory_surface_hides_internal_goal_inference():
    with pytest.raises(ImportError):
        exec(
            "from sona.runtime.memory import GoalInferenceKernel",
            {},
            {},
        )


def test_advanced_memory_surface_exports_retrieval_kernel():
    from sona.runtime.memory.advanced import RetrievalKernel

    assert RetrievalKernel.__name__ == "RetrievalKernel"


def test_internal_memory_surface_exports_goal_inference_kernel():
    from sona.runtime.memory.internal import GoalInferenceKernel

    assert GoalInferenceKernel.__name__ == "GoalInferenceKernel"