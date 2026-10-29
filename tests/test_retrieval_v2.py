import hashlib
import json

from app.retrieval.contracts import RetrievedEvidence
from app.retrieval.storage import canonical_value
from evals.retrieval_v2.fixtures import author_suite
from evals.retrieval_v2.runner import SUITE, load_suite, score, suite_identity


def test_v2_fixtures_are_fresh_valid_and_reproducible():
    records, cases = load_suite()
    assert len(records) == 96 and len(cases) == 40
    assert sum(c.category == "no_answer" for c in cases) == 10
    assert sum(bool(c.required_groups) for c in cases) == 12
    authored_records, authored_cases = author_suite()
    assert canonical_value(records) == canonical_value(authored_records)
    # Authoring omits default empty required_groups; validation supplies it.
    from evals.retrieval_v2.runner import Case

    assert cases == [Case.model_validate(c) for c in authored_cases]
    old = json.loads((SUITE.parent / "retrieval/cases.json").read_bytes())
    assert not {c.query.text for c in cases} & {c["query"]["text"] for c in old}


def test_v2_no_answer_and_alternate_required_groups():
    records, cases = load_suite()
    by_id = {r.evidence_id: r for r in records}

    def hits(*ids):
        return [
            RetrievedEvidence(record=by_id[key], score=1, rank=i, retriever="test")
            for i, key in enumerate(ids, 1)
        ]

    negative = next(c for c in cases if c.category == "no_answer")
    assert score([], negative)["correct_abstention"]
    assert score(hits("V2-01-a"), negative)["false_retrieval"]
    assert score([], negative)["recall_at_k"] is None
    assert score([], negative)["mrr"] is None
    multi = next(c for c in cases if c.category == "multi_chunk")
    assert score(hits("V2-01-alt", "V2-01-b"), multi)["required_group_recall"] == 1
    assert score(hits("V2-01-a", "V2-01-alt"), multi)["required_group_recall"] == 0.5


def test_v2_pre_result_freeze_hashes():
    plan = json.loads((SUITE / "plan.json").read_bytes())
    assert suite_identity(*load_suite()) == plan["suite_identity"]
    for name, expected in plan["scorer_source_sha256"].items():
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        assert (
            hashlib.sha256(
                (root / name).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            == expected
        )
