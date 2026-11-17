# Trace case từ C-002 tới regression test

| Trường | Bằng chứng |
|---|---|
| Trial | `seeded_regression C-002@11` thuộc run `E-seeded_regression-20261117-3bd2`, report `src/reports/eval_seeded_regression.json`. |
| Triệu chứng | Trạng thái `resolved` và ledger 20.000đ trong khi nhãn yêu cầu `denied` và 0đ. `TrialPass`, `RefundAmountCorrect` và `DbFactKept` đều phát hiện sai lệch. |
| Bước sai đầu tiên | Event 3, `model_override`, payload `{"delay_days": 5}`. |
| Căn cứ | Event 1 handoff chỉ truyền phạm vi quyền và công cụ allowlist. Event 2 investigator đọc đúng đơn `O-202`, `delay_days=2` từ DB. Event 3 đổi số ngày sang lời ticket. Event 4 mới tạo quote sai 20.000đ và event 6 thông báo đã hoàn số đó. |
| Failure mode | FM-03 · ticket_trust. |
| Đối chứng | `fixed C-002@11` thuộc run `E-fixed-20261117-3bd2`. Event 3 là `quote` với `amount_vnd=0`, event 4 trả lời từ chối. Ledger không có khoản hoàn. |
| Regression test | `tests/test_lab9_trace_case.py::test_c002_keeps_db_delay_and_does_not_refund` kiểm cùng claim và seed trên hai shape. Assertions về giữ nguyên DB và số tiền đúng trả true trên fixed, false trên seeded_regression. |
| Phạm vi bằng chứng | Trace chứng minh vị trí thay đổi dữ kiện và hậu quả trên fixture công khai. Nó chưa đo mức phổ biến của lỗi trên người dùng thật. |

### Trường hợp FM-08

`misreport C-008@11` dùng quote 35.000đ nhưng host chỉ ghi 20.000đ theo approval. Event 4 `reply` vẫn báo hoàn 35.000đ. Grader Lab 8 chấm outcome PASS vì ledger và proposal đúng nhãn. `ReplyLedgerMatch` chấm false khi đối chiếu số tiền trong câu trả lời với ledger.

`tests/test_lab9_trace_case.py::test_c008_reply_matches_committed_refund_after_approval_cap` replay cùng ca trên `fixed` và công tắc `misreport` sẵn có. Cả hai ledger đều ghi 20.000đ. Reply grader trả true trên fixed và false trên ca báo sai tiền.

```powershell
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
python -m pytest -q -m student -o addopts= -k lab9_trace_case
```
