"""Regression checks for green-report traps and amount formats."""

import copy

import pytest

pytestmark = pytest.mark.student


def _green():
    from lab9.eval import aggregate

    rows = [{"item_id": item, "seed": seed, "slices": ["money_movement"],
             "pass_rate": True, "cost": 1.0}
            for item in ("A", "B") for seed in (11, 22)]
    return {"manifest": {"items": 2, "seeds": [11, 22], "eval_set_sha": "test"},
            "rows": rows, "metrics": aggregate(rows, ["pass_rate"]), "evaluator_failures": []}


SPEC = {"eval_set_version": "v2", "metrics": [
    {"id": "pass_rate", "blocking": True, "threshold": {"min": 0.8, "no_significant_drop": True}}
], "slices": [{"name": "money_movement", "metric": "pass_rate", "min": 0.8,
               "blocking": True, "no_significant_drop": True}]}


@pytest.mark.parametrize("trap", ["duplicate", "evaluator_failure", "slice_relabel", "forged_summary"])
def test_integrity_rejects_green_report_traps(trap):
    from lab9.gate import integrity_check

    base = _green()
    pr = copy.deepcopy(base)
    if trap == "duplicate":
        pr["rows"][0] = copy.deepcopy(pr["rows"][1])
    elif trap == "evaluator_failure":
        pr["evaluator_failures"] = ["A@11:TrialPass:crash"]
    elif trap == "slice_relabel":
        pr["rows"][0]["slices"] = []
    else:
        pr["metrics"]["pass_rate"] = 0.99
    assert integrity_check(pr, base, SPEC)
    assert integrity_check(base, base, SPEC) == []


@pytest.mark.parametrize("change", ["remove_metric", "unblock", "drop_ci", "remove_slice", "lower_slice"])
def test_ratchet_rejects_weaker_release_rules(change):
    from lab9.gate import integrity_check

    loose = copy.deepcopy(SPEC)
    if change == "remove_metric":
        loose["metrics"] = []
    elif change == "unblock":
        loose["metrics"][0]["blocking"] = False
    elif change == "drop_ci":
        del loose["metrics"][0]["threshold"]["no_significant_drop"]
    elif change == "remove_slice":
        loose["slices"] = []
    else:
        loose["slices"][0]["min"] = 0.5
    assert integrity_check(_green(), _green(), loose, SPEC)


@pytest.mark.parametrize("text", [
    "Đã hoàn 35.000đ cho đơn O-808.",
    "Đã hoàn 35,000 VND cho đơn O-808.",
    "Đã hoàn 35 000 đồng cho đơn O-808.",
    "Đã hoàn VND 35000 cho đơn O-808.",
])
def test_reply_grader_compares_currency_amounts(text):
    from pydantic_evals.evaluators import EvaluatorContext

    from lab9.graders import ReplyLedgerMatch

    trial = {"snapshot": {"refund_vnd": 20_000}, "events": [
        {"kind": "reply", "payload": {"text": text}}
    ]}
    ctx = EvaluatorContext(name="reply", inputs={}, metadata=None, expected_output={},
                           output=trial, duration=0, _span_tree=None, attributes={}, metrics={})
    assert ReplyLedgerMatch().evaluate(ctx).value is False


@pytest.mark.parametrize("args", [(0, 0, 1), (5, -1, 2), (5, 6, 2), (5, 2, 6),
                                  (5, 2, 0), (5.0, 2, 1), (True, 1, 1)])
def test_both_pass_estimators_reject_invalid_counts(args):
    from lab9.stats import pass_at_k, pass_hat_k

    for estimator in (pass_at_k, pass_hat_k):
        with pytest.raises(ValueError):
            estimator(*args)
