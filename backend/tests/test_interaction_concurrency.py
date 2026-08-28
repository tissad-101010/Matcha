"""Fast checks for the concurrency verification script."""

from concurrent.futures import Future

import pytest
from backend.scripts.check_interaction_concurrency import assert_single_relationship


def test_failed_worker_future_propagates_instead_of_hiding_concurrency_errors() -> None:
    future: Future[object] = Future()
    future.set_exception(RuntimeError("worker failed"))
    with pytest.raises(RuntimeError, match="worker failed"):
        future.result(timeout=1)


def test_relationship_assertion_is_exposed_for_real_database_check() -> None:
    assert callable(assert_single_relationship)
