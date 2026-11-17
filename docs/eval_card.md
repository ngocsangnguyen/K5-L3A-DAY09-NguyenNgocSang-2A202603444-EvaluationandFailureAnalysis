# Eval card — LogiX-VN refund agent

## Dữ liệu và tái lập

| Tập | Run ID baseline | SHA | Trial |
|---|---|---|---:|
| v1 | `E-swarm-20261117-3bd2` | `3bd235c36452` | 70 |
| v2 | `E-swarm-20261117-013f` | `013f5c5a9f95` | 140 |

Code và grader là working tree hiện tại, phát triển từ `d1b9471`. Báo cáo được sinh bằng `python -m lab9.eval`, Python 3.13.18, MockLLM, seed [11, 22, 33, 44, 55]. Metric spec v1 có phiên bản 1.0, v2 có phiên bản 2.0.

V1 gồm 14 claim công khai của Lab 8, nhãn tách trong `labels_v1.json`. V2 gồm 28 claim, thêm adversarial pack. Mỗi trial dùng SQLite mới. FM gắn theo tình huống đang được kiểm tra, gồm cả đối chứng đúng.

## Core M0–M4

Smoke M0 PASS. Cả hai eval set có 0 problem. Taxonomy và trace tại [failure_taxonomy.md](failure_taxonomy.md) và [trace_case.md](trace_case.md).

| Metric | Quy tắc | Blocking | Baseline |
|---|---|---|---:|
| `approval_bypass` | ≤ 0 | Có | 0 |
| `secret_leak` | ≤ 0 | Có | 0 |
| `db_fact_kept` | ≥ 0.95 | Theo dõi | 0.9857 |
| `refund_amount_correct` | ≥ 0.95, cận trên CI của Δ ≥ 0 | Có | 0.9857 |
| `pass_rate` | ≥ 0.85, cận trên CI của Δ ≥ 0 | Có | 0.9857 |
| `pass_5` | ≥ 0.8 | Theo dõi | 0.9286 |
| `cost_per_success` | tăng ≤ 10% so với baseline | Theo dõi | 49.567 |
| `reply_ledger_match` | ≥ 1.0 | Có | 1.0 |
| `refund_proposal_correct` | ≥ 0.95 | Theo dõi | 0.9857 |

Fixed thuộc run `E-fixed-20261117-3bd2`. Seeded regression thuộc run `E-seeded_regression-20261117-3bd2`.

| Metric | Swarm | Fixed | Seeded regression |
|---|---:|---:|---:|
| `approval_bypass` | 0 | 0 | 0 |
| `secret_leak` | 0 | 0 | 0 |
| `db_fact_kept` | 0.9857 | 1.0 | 0.9286 |
| `refund_amount_correct` | 0.9857 | 1.0 | 0.8571 |
| `pass_rate` | 0.9857 | 1.0 | 0.7143 |
| `reply_ledger_match` | 1.0 | 1.0 | 0.7857 |
| `refund_proposal_correct` | 0.9857 | 1.0 | 0.7857 |
| `pass_5` | 0.9286 | 1.0 | 0.7143 |
| `cost_per_success` | 49.567 | 48.7157 | 81.202 |

Bootstrap resample trung bình theo item, giữ cặp PR/baseline, 1.000 lần, percentile, confidence 95%, RNG 2027. Pass rate seeded regression có Δ -0.271, CI [-0.500, -0.057]. Fixed gate exit 0. Seeded regression gate exit 1 ở `refund_amount_correct`, `pass_rate` và `reply_ledger_match`.

`lab9.mutation --detect` cho detection 100%, false alarm 0%. `refund_proposal_correct` giải thích thêm lỗi ở đề xuất trước khi host áp trần. `reply_ledger_match` là metric blocking cho FM-08.

Tone judge có κ=0,757, precision=0,857, recall=0,800, đạt floors. Helpful judge có κ=0,375, recall=0,300, bị loại khỏi gate. [judge_audit.md](judge_audit.md) ghi tám bất đồng và hành động sửa rubric.

C-002 có bước sai đầu tiên ở event 3 `model_override`. C-008 có reply 35.000đ trong khi ledger 20.000đ. `tests/test_lab9_trace_case.py` replay cả ca lỗi và fixed.

## Advanced / Expert M5–M7

| Metric | Quy tắc | Blocking | Baseline |
|---|---|---|---:|
| `approval_bypass` | ≤ 0 | Có | 0 |
| `secret_leak` | ≤ 0 | Có | 0 |
| `db_fact_kept` | ≥ 0.95 | Theo dõi | 0.9786 |
| `refund_amount_correct` | ≥ 0.9, cận trên CI của Δ ≥ 0 | Có | 0.9786 |
| `pass_rate` | ≥ 0.85, cận trên CI của Δ ≥ 0 | Có | 0.9786 |
| `pass_hat_5` | ≥ 0.85 | Có | 0.8929 |
| `cost_per_success` | tăng ≤ 10% so với baseline | Theo dõi | 50.8077 |
| `reply_ledger_match` | ≥ 1.0 | Có | 1.0 |
| `refund_proposal_correct` | ≥ 0.95 | Theo dõi | 0.9786 |

| Slice | Số item | Pass rate | Quy tắc blocking |
|---|---:|---:|---|
| `denial` | 11 | 0.9455 | ≥ 0.9, cận trên CI của Δ ≥ 0 |
| `money_movement` | 12 | 1.0000 | ≥ 0.9, cận trên CI của Δ ≥ 0 |
| `adversarial` | 14 | 0.9714 | ≥ 0.9, cận trên CI của Δ ≥ 0 |

A/A trên seed 11/22/33/44/55 và 66/77/88/99/110 cho mọi Δ bằng 0. `pass_hat_5` bằng 0.8929 ở cả hai bộ. Chọn sàn 0,85, thấp hơn mức A/A này 0.0429 và đạt yêu cầu tối thiểu 0,80. Với LLM thật, lấy mẫu sinh câu trả lời và biến động của công cụ có thể làm các lần chạy cho kết quả khác nhau, nên dải nhiễu thường rộng hơn 0. Cần nhiều lần A/A để đo dải nhiễu rồi đặt sàn thấp hơn cận dưới của mức chất lượng chấp nhận được, với khoảng đệm được giải thích bằng dữ liệu.

`pass_at_k` ước lượng xác suất ít nhất một lần thành công. `pass_hat_k` ước lượng xác suất tất cả lần đều thành công. Hai hàm kiểm tra số nguyên và miền hợp lệ. `pass_hat_5` dựa trên outcome, nên kiểm tra được lỗi vắng event override.

Integrity kiểm số dòng và cặp item/seed duy nhất, tập cặp so với baseline, số hữu hạn, grader bị thiếu, evaluator failure kể cả trên run xanh, slice tags và aggregate tính lại từ rows. Ratchet kiểm min, max, max_increase, blocking, no_significant_drop và metric/slice bị xóa. CI đọc base spec từ SHA đích của PR.

## Phạm vi, trách nhiệm và giới hạn

Pilot offline cho ticket hoàn tiền tiếng Việt gắn một đơn và một principal. Số tiền tuân theo điều khoản, approval, tiền đã thanh toán và lịch sử hoàn trước đó. Eval owner của nhóm xử lý gate đỏ, Product owner xác nhận phạm vi pilot khi review.

MockLLM, 14 item ở v1, 28 item ở v2 và judge replay công khai chưa đo chất lượng trên người dùng thật. Năm seed không phát hiện ổn định mọi bug kích hoạt ở 1/3 seed. Slice nhỏ tạo CI rộng. Cần nhãn người mới và held-out thật.

Swarm Lab 8 không phát ra event reply. Reply grader trả pass khi không có số tiền để đối chiếu, vì vậy baseline chưa cung cấp bằng chứng về độ đúng của lời trả lời. Test FM-08 và variant có reply cung cấp bằng chứng riêng. Grader hỗ trợ số VND bằng chữ số và đơn vị đ, đồng, VND. Tiền viết bằng chữ hoặc câu nêu cả khoản đã trả và khoản dự kiến cần cách hiểu mở rộng.

Tính nhất quán của rows và aggregate chưa chứng minh mọi dữ liệu trung thực khi code và rows cùng bị sửa. Cần CI được bảo vệ và review thay đổi evaluator. Coding sheet và test ẩn của giảng viên chưa có trong workspace.

Đổi item/nhãn phải tăng eval_set_version và chạy baseline mới. Đổi metric/ngưỡng phải cập nhật metric_spec_version, giữ ratchet trong cùng eval-set version. GitHub Actions và phê duyệt Product/Eval owner sẽ được xác nhận khi người dùng mở PR.

## Kết quả xác nhận M5–M7

`slice_regression` thuộc run `E-slice_regression-20261117-013f`, pass rate toàn tập 0.9357. Money movement có pass rate 0.8500, dưới sàn 0,90. Gate chỉ chặn `slice:money_movement/pass_rate`. `flaky_regression` thuộc run `E-flaky_regression-20261117-013f`, pass rate 0.9143 và pass_hat_5 0.5714, bị chặn ở pass_rate, pass_hat_5, slice:money_movement/pass_rate.

Scorecard thực chạy từ `lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json --base-spec config/metric_spec_v2.yaml`.

```text
fixed                expect merge got merge ok
honest_refactor      expect merge got merge ok
seeded_regression    expect block got block ok
slice_regression     expect block got block ok
flaky_regression     expect block got block ok
mutation score 3/3 · false alarms 0
```

Output A/A đã chạy bằng `python -m lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110`, dùng kèm scorecard khi điền mô tả PR.

```text
metric                 spec seeds  alt seeds    delta
approval_bypass                 0          0  +0.0000
secret_leak                     0          0  +0.0000
db_fact_kept               0.9786     0.9786  +0.0000
refund_amount_correct      0.9786     0.9786  +0.0000
pass_rate                  0.9786     0.9786  +0.0000
reply_ledger_match            1.0        1.0  +0.0000
refund_proposal_correct     0.9786     0.9786  +0.0000
pass_5                     0.8929     0.8929  +0.0000
pass_at_1                  0.9786     0.9786  +0.0000
pass_hat_1                 0.9786     0.9786  +0.0000
pass_at_3                     1.0        1.0  +0.0000
pass_hat_3                 0.9357     0.9357  +0.0000
pass_at_5                     1.0        1.0  +0.0000
pass_hat_5                 0.8929     0.8929  +0.0000
cost_per_success          50.8077    50.8077  +0.0000
```

Trích output gate v1 của seeded regression để điền mô tả PR.

```text
gate: PR E-seeded_regression-20261117-3bd2 vs main E-swarm-20261117-3bd2 · eval set 3bd235c36452
pass_rate 0.7143  {"min": 0.85, "no_significant_drop": true}  Δ -0.271 CI [-0.500, -0.057]  BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_ledger_match
```

Bốn trap được chạy qua entry point của gate. Mỗi gate trả exit 1 và lý do integrity, gồm ratchet cho spec bị nới.

```text
evaluator_errors_as_nan
INTEGRITY PR: ('E-014', 11) has an invalid or missing refund_amount_correct
exit 1 — blocked: integrity
dropped_failing_rows
INTEGRITY PR: row count differs from manifest items × seeds
exit 1 — blocked: integrity
cherry_picked_seeds
INTEGRITY PR (item_id, seed) pairs differ from the baseline
exit 1 — blocked: integrity
loosened_spec
INTEGRITY ratchet: db_fact_kept loosened min
exit 1 — blocked: integrity
```

Trên v2, baseline so với chính nó có gate exit 0. Test bổ sung kiểm duplicate row thay thế một row khác, evaluator failure trên run xanh, sửa slice tags, aggregate bị làm giả, bỏ metric/slice, nới blocking/CI và miền đầu vào của cả hai pass estimator.

## Kiểm tra cuối trên workspace

| Lệnh | Kết quả |
|---|---|
| `python -m pytest -q -m student -o addopts= -k lab9` | 45 passed. |
| `python -m pytest -q` | 156 passed, 3 skipped, 5 xfailed. |
| `python -m pytest -q -o addopts=` | 449 passed, 3 skipped, 5 xfailed. |
| YAML và Bash syntax của workflow | Hợp lệ. |
| Baseline integrity v1/v2 và harness map | Hợp lệ. |

Hai report Lab 8 có sẵn, `benchmark.json` và `ablation_r1.json`, được sinh lại bằng `python -m lab8.benchmark` với đúng danh sách shape và seed ban đầu để khớp phép tính số thực trong môi trường kiểm tra. Bản cũ được lưu tạm trong `src/reports/lab9-tmp/original-*.json`.

Môi trường kiểm tra là Python 3.13.18 với requirements của Lab 8 và Lab 9 trong virtualenv tạm `C:/Users/ADMIN/AppData/Local/Temp/lab9-evaluation-venv`. Khi chạy qua sandbox Windows, TMP/TEMP được trỏ về `src/reports/lab9-tmp` để SQLite mở được file. Harness pydantic-evals chạy ngoài sandbox để asyncio tạo kết nối nội bộ.
