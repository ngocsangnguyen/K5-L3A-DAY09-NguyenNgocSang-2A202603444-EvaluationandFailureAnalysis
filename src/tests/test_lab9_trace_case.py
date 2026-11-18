"""Regression checks derived from the C-002 and C-008 trace cases."""

import pytest

pytestmark = pytest.mark.student


@pytest.fixture(autouse=True)
def restore_shape_registry():
    from lab8.shapes import SHAPES

    original = SHAPES.copy()
    yield
    SHAPES.clear()
    SHAPES.update(original)


def test_c002_keeps_db_delay_and_does_not_refund():
    from lab9.trace_case import investigate

    for shape, expected_pass in (("fixed", True), ("seeded_regression", False)):
        case = investigate(shape, "C-002", 11)
        trial, label = case["trial"], case["label"]
        override = any(event["kind"] == "model_override" for event in trial["events"])
        assert (not override) is expected_pass
        assert (trial["snapshot"]["refund_vnd"] == label["refund_vnd"]) is expected_pass
        assert trial["lab8_pass"] is expected_pass


def test_c008_reply_matches_committed_refund_after_approval_cap(monkeypatch):
    from pydantic_evals.evaluators import EvaluatorContext

    from lab8.shapes import SHAPES
    from lab9.graders import ReplyLedgerMatch
    from lab9.trace_case import investigate
    from lab9.variant_agent import make_shape

    monkeypatch.setitem(SHAPES, "test_misreport", make_shape("test_misreport", {"no_override", "misreport"}))
    for shape, expected_match in (("fixed", True), ("test_misreport", False)):
        case = investigate(shape, "C-008", 11)
        trial = case["trial"]
        assert trial["lab8_pass"] is True
        assert trial["snapshot"]["refund_vnd"] == 20_000
        ctx = EvaluatorContext(name=shape, inputs={}, metadata=None, output=trial,
                               expected_output=case["label"], duration=0, _span_tree=None,
                               attributes={}, metrics={})
        assert ReplyLedgerMatch().evaluate(ctx).value is expected_match
