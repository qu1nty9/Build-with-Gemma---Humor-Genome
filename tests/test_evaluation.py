from evaluation.compare_models import mechanism_jaccard, mechanism_names


def record(*mechanisms: str) -> dict:
    return {
        "status": "ok",
        "result": {"mechanisms": [{"mechanism": mechanism} for mechanism in mechanisms]},
    }


def test_mechanism_names_ignores_failed_records() -> None:
    assert mechanism_names({"status": "error"}) == set()


def test_mechanism_jaccard() -> None:
    left = record("misdirection", "irony")
    right = record("misdirection", "incongruity")
    assert mechanism_jaccard(left, right) == 1 / 3


def test_mechanism_jaccard_is_none_for_two_empty_results() -> None:
    assert mechanism_jaccard(record(), record()) is None

