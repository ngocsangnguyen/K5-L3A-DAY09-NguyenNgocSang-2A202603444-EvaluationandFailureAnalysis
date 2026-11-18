"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item
from lab9.graders import GRADERS


def _finite(value: object) -> bool:
    return isinstance(value, int) or isinstance(value, float) and isfinite(value)


def _report_problems(report: dict, name: str, spec: dict) -> tuple[list[str], dict]:
    problems = []
    manifest = report["manifest"]
    seeds = manifest["seeds"]
    rows, metrics = report["rows"], report["metrics"]
    if not seeds or len(seeds) != len(set(seeds)):
        problems.append(f"{name}: manifest seeds must be nonempty and unique")
    if not rows or len(rows) != manifest["items"] * len(seeds):
        problems.append(f"{name}: row count differs from manifest items × seeds")
    if report.get("evaluator_failures"):
        problems.append(f"{name}: evaluator_failures is nonempty")
    for metric, value in metrics.items():
        if value is not None and not _finite(value):
            problems.append(f"{name}: {metric} has a non-finite or non-numeric summary")

    graded = [m["id"] for m in spec["metrics"] if m["id"] in GRADERS]
    index = {}
    for row in rows:
        key = (row["item_id"], row["seed"])
        if key in index:
            problems.append(f"{name}: duplicate row {key}")
        index[key] = frozenset(row.get("slices") or [])
        for metric in graded:
            if not _finite(row.get(metric)):
                problems.append(f"{name}: {key} has an invalid or missing {metric}")
    if (len({item for item, _ in index}) != manifest["items"]
            or {seed for _, seed in index} != set(seeds)):
        problems.append(f"{name}: row items or seeds differ from the manifest")

    if not problems:
        actual_costs = all("cost" in row for row in rows)
        if any(not _finite(row.get("cost", 0)) or row.get("cost", 0) < 0 for row in rows):
            problems.append(f"{name}: invalid row cost")
        else:
            summaries = aggregate([{"cost": 0, **row} for row in rows], graded, spec.get("pass_k", []))
            required = set(graded) | {f"pass_hat_{k}" for k in spec.get("pass_k", [])} | {
                f"pass_at_{k}" for k in spec.get("pass_k", [])
            }
            for metric, value in summaries.items():
                if metric == "cost_per_success" and not actual_costs:
                    continue
                if metric in required or metric in metrics:
                    if metric not in metrics or metrics[metric] != value:
                        problems.append(f"{name}: {metric} summary differs from rows")
    return problems, index


def _ratchet(spec: dict, base_spec: dict) -> list[str]:
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []
    problems = []
    for section in ("metrics", "slices"):
        def key(entry):
            if section == "metrics":
                return entry["id"]
            return f"slice:{entry['name']}/{entry['metric']}"

        current = {key(entry): entry for entry in spec.get(section, [])}
        for previous in base_spec.get(section, []):
            identifier = key(previous)
            if identifier not in current:
                problems.append(f"ratchet: {identifier} was removed")
                continue
            entry = current[identifier]
            old, new = previous, entry
            if section == "metrics":
                old, new = previous.get("threshold", {}), entry.get("threshold", {})
            if previous.get("blocking") and not entry.get("blocking"):
                problems.append(f"ratchet: {identifier} no longer blocks")
            if old.get("no_significant_drop") and not new.get("no_significant_drop"):
                problems.append(f"ratchet: {identifier} dropped no_significant_drop")
            for threshold in ("min", "max", "max_increase"):
                if threshold not in old:
                    continue
                value = new.get(threshold)
                if not _finite(value) or (value < old[threshold] if threshold == "min" else value > old[threshold]):
                    problems.append(f"ratchet: {identifier} loosened {threshold}")
    return problems


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems, pr_rows = _report_problems(pr, "PR", spec)
    base_problems, base_rows = _report_problems(base, "baseline", spec)
    problems.extend(base_problems)
    if pr_rows.keys() != base_rows.keys():
        problems.append("PR (item_id, seed) pairs differ from the baseline")
    elif pr_rows != base_rows:
        problems.append("PR slice tags differ from the baseline")
    if base_spec is not None:
        problems.extend(_ratchet(spec, base_spec))
    return problems


def _paired_ci(a: dict[str, float], b: dict[str, float], spec: dict) -> tuple[float, float, float]:
    keys = sorted(a.keys() & b.keys())
    bootstrap = spec.get("bootstrap", {})
    return stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                  n_resamples=bootstrap.get("n_resamples", 1000),
                                  rng=bootstrap.get("rng", 2027),
                                  confidence=bootstrap.get("confidence", 0.95))


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    for entry in spec.get("slices", []):
        name, metric = entry["name"], entry["metric"]
        identifier = f"slice:{name}/{metric}"
        a, b = per_item(pr, metric, name), per_item(base, metric, name)
        value = sum(a.values()) / len(a) if a else None
        failed = value is None or ("min" in entry and value < entry["min"])
        note = ""
        if entry.get("no_significant_drop"):
            if a and a.keys() == b.keys():
                d, lo, hi = _paired_ci(a, b, spec)
                note = f" Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                failed = failed or hi < 0
            else:
                failed = True
                note = " missing paired item scores"
        verdict = "ok"
        if failed:
            verdict = "BLOCK" if entry.get("blocking") else "warn"
            if entry.get("blocking"):
                blocked.append(identifier)
        display = f"{value:.4f}" if value is not None else "missing"
        lines.append(f"  {identifier:<34} {display} (n={len(a)}){note} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            if not a or a.keys() != b.keys():
                verdict = "fail"
                note = "missing paired item scores"
            else:
                d, lo, hi = _paired_ci(a, b, spec)
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                if hi < 0:
                    verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
