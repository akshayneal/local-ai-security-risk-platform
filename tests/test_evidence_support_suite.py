import json

from evals.evidence_support_v1.build_suite import build
from evals.evidence_support_v1.runner import (
    DIRECTORY,
    identity,
    load_suite,
    ranking_metrics,
    validate_suite,
)


def test_fresh_suite_frozen_before_candidates_and_generator_reproduces():
    assert identity() == json.loads((DIRECTORY / "freeze.json").read_bytes())
    validate_suite()
    generated = build()
    for name, expected in zip(
        ("corpus.json", "cases.json", "registry_current.json"), generated, strict=True
    ):
        assert json.loads((DIRECTORY / name).read_bytes()) == expected
    records, cases, gate = load_suite()
    assert len(records) == 55 and len(cases) == 43
    assert len({c["category"] for c in cases}) == 14
    assert sum(c["gold"]["relationship"] == "directly_supports" for c in cases) == 18
    assert any(not gate(r) and r.status == "current" for r in records)
    assert any(r.effective_date and r.effective_date.year == 2030 for r in records)
    assert any(r.expiration_date for r in records)


def test_group_recall_does_not_require_all_alternatives_but_requires_all_components():
    _, cases, _ = load_suite()
    multiple = next(c for c in cases if c["category"] == "multiple_sufficient")
    one = multiple["gold"]["required_evidence_groups"][0][0]
    assert ranking_metrics(multiple, [one])["support_sufficient_at_k"] is True
    chunks = next(c for c in cases if c["category"] == "multi_chunk")
    first, second = chunks["gold"]["required_evidence_groups"]
    assert ranking_metrics(chunks, first)["support_sufficient_at_k"] is False
    assert ranking_metrics(chunks, first)["required_group_recall"] == 0.5
    assert ranking_metrics(chunks, first + second)["support_sufficient_at_k"] is True


def test_no_answer_is_not_scored_as_a_successful_ranking_support_decision():
    _, cases, _ = load_suite()
    case = next(c for c in cases if c["category"] == "no_answer")
    metrics = ranking_metrics(case, ["UNRELATED"])
    assert metrics["relevant_recall_at_k"] is None
    assert metrics["support_sufficient_at_k"] is None
