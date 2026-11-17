# Judge audit

Hai CSV được chấm theo nhãn người, với `FAIL` là lớp dương. Ngưỡng đạt là κ ≥ 0,60, precision ≥ 0,80 và recall ≥ 0,70.

| Tiêu chí | n | TP / FP / FN / TN | κ | Precision | Recall | Tỷ lệ FAIL quan sát → hiệu chỉnh | Quyết định |
|---|---:|---|---:|---:|---:|---|---|
| `tone_ok` | 100 | 24 / 4 / 6 / 66 | 0,757 | 0,857 | 0,800 | 28% → 30% | Đạt chuẩn để đánh giá giọng điệu. |
| `helpful` | 100 | 9 / 0 / 21 / 70 | 0,375 | 1,000 | 0,300 | 9% → 30% | Loại khỏi gate. |

### Đối chiếu bất đồng

| Case | Judge / người | Nhãn sau audit | Căn cứ | Sửa rubric |
|---|---|---|---|---|
| H-008 | PASS / FAIL | FAIL (người) | Cụm “em”, “nha”, “anh check” làm giọng điệu quá suồng sã khi thông báo hoàn tiền. | Thêm ví dụ phân biệt giọng thân thiện với cách xưng hô và tiểu từ suồng sã. |
| H-017 | PASS / FAIL | FAIL (người) | “Dạ” không bù được cách gọi “bạn ơi” kèm “rồi nha” trong ngữ cảnh xử lý tiền. | Đánh giá cả câu và bổ sung ví dụ có lời mở đầu lịch sự nhưng giọng tổng thể quá thân mật. |
| H-029 | PASS / FAIL | FAIL (người) | “Không cần nhắn thêm” gạt thắc mắc của khách trong lúc yêu cầu vẫn đang xử lý. | Chấm FAIL nếu câu trả lời ngăn khách liên hệ lại bằng giọng dứt khoát hoặc thiếu tôn trọng. |
| H-042 | FAIL / PASS | PASS (người) | Câu trả lời ngắn, lịch sự, nêu đủ kết quả và thời gian chờ. | Cho PASS với giọng điệu lịch sự dù chủ ngữ là đơn hàng và không gọi trực tiếp “anh/chị”. |
| H-051 | FAIL / PASS | PASS (người) | Từ “refund” dễ hiểu trong ngữ cảnh và cách nói vẫn lịch sự. | Chấm thuật ngữ theo độ dễ hiểu và giọng tổng thể. |
| H-081 | FAIL / PASS | PASS (người) | Lời từ chối giải thích căn cứ chính sách và giữ phép lịch sự. | Giọng điệu có thể PASS khi lời từ chối ngắn. Bước tiếp theo thuộc tiêu chí helpfulness. |
| HL-015 | PASS / FAIL | FAIL (người) | Reply báo 55.000đ, ledger ghi 40.000đ. | Dùng grader code đối chiếu ledger trước khi đánh giá sự hữu ích. |
| HL-016 | PASS / FAIL | FAIL (người) | Reply xin lỗi dài và báo 55.000đ, ledger ghi 35.000đ. | Xác thực tiền bằng code. Đánh giá độ hữu ích theo thông tin và bước tiếp theo mà khách cần. |

Judge `helpful` bỏ sót 21 trong 30 lỗi. Precision 1,000 chỉ phản ánh 9 lỗi judge đã gắn cờ. Hiệu chỉnh Rogan–Gladen ước lượng lại tỷ lệ lỗi toàn tập, không phục hồi nhãn của từng ca bỏ sót. Giữ phép chấm tiền và approval bằng code.

Dữ liệu là replay công khai. Sau khi chỉnh rubric, cần nhãn người mới trên một tập held-out để đo xem việc sửa rubric có cải thiện khả năng tổng quát hay không.

```powershell
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
```
