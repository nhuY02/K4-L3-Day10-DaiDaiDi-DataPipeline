# Member Role Report — Task 4: Evaluation, Corruption & Reporting

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Huy Hùng |
| MSSV | 2A202602990 |
| Khóa/Lớp | K4 |
| Tên nhóm | DaiDaiDi |
| Vai trò chính | Evaluation, Corruption & Reporting Owner |
| Repository | https://github.com/nhuY02/K4-L3-Day10-DaiDaiDi-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File/hàm | Input | Output | Trạng thái |
|---|---|---|---|---|
| Benchmark test set | `src/evaluation/testset.py` | Clean dataframe | 10-question test set | Hoàn thành |
| Corruption suite | `src/ingestion/corruption.py` | Clean dataframe | Corrupted data + log | Hoàn thành |
| Markdown reporting | `src/observability/reporting.py` | Metrics/quality/freshness | Phase 1 + comparison reports | Hoàn thành |

Hỗ trợ integration để đảm bảo corruption giữ 24 rows và report phản ánh đúng payload thực tế.

## 3. Kết quả theo vai trò

- Test set gồm 10 câu thuộc `summary`, `authors`, `date`, `categories`.
- Corruption log ghi đủ 6 scenario và output vẫn 24 rows.
- Corrupted data có 5 duplicated IDs và 6 blank summaries; stale ratio 37.5%.
- Reports hiển thị bảng Baseline/Corrupted/Repaired và chi tiết expectations.

Output: `data/eval/test_set.json`, `data/results/corruption_log.json`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Cần một benchmark cố định để đo chất lượng, một bộ corruption có chủ đích để tạo silent failure, và report biến artifacts thành bằng chứng định lượng dễ kiểm tra.

### Cách triển khai
Test set chọn document có đủ metadata và tạo câu hỏi/ground truth/doc IDs. Corruption dùng seed cố định, lần lượt drop latest, blank summary, inject noise, truncate title, stale date và duplicate rows; cuối cùng rebuild `text_for_embedding`. Reporting đọc metrics, quality và freshness để sinh bảng so sánh.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Clean dataframe, evaluation metrics, quality/freshness dict |
| Output | Test set JSON, corruption log/data, Markdown reports |
| Phụ thuộc | Task 2 clean schema, Task 3 observability, Task 1 orchestration |
| Module dùng output | Evaluation pipeline và phần nộp bài |
| Lỗi cần xử lý | Thiếu field, row count thay đổi ngoài ý muốn, report schema mismatch |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

Kết quả: test set 10 câu; corruption 24→24; comparison report sinh thành công.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Drop rows làm số lượng corrupted dataset giảm, khó đối chiếu với tín hiệu nghiệm thu.
- **Phương án:** Chấp nhận row count giảm hoặc duplicate đúng số row đã drop.
- **Đã chọn:** Duplicate số row tương ứng để giữ `len(corrupted)==24`.
- **Lý do:** Vẫn giữ semantics của cả drop-latest và duplicate, đồng thời so sánh ba trạng thái thuận tiện.
- **Bằng chứng:** Input rows 24, output rows 24, 5 duplicated IDs và Quality Gate FAIL.

## 6. Một lỗi/blocker đã xử lý

- **Triệu chứng:** Bản đầu corruption cho 22 rows và report Freshness bị lặp dòng.
- **Nguyên nhân:** Tỷ lệ drop/duplicate không cân bằng; formatting report dùng danh sách freshness không đúng.
- **Cách xử lý:** Duplicate đúng số record đã drop, stale-date lùi khoảng 5 năm, sửa reporting để mỗi freshness metric chỉ xuất hiện một lần.
- **Xác minh:** Corruption flow hoàn tất, stale ratio corrupted 0.375, report có Quality FAIL/Freshness FAIL và repaired PASS.
- **Điều học được:** Corruption benchmark phải deterministic và report phải khớp artifact thật.

## 7. Hiểu biết về luồng end-to-end

Crossref được lưu raw, clean rồi embed/index. Test set gắn mỗi câu với ground-truth `paper_id`; retrieval hit kiểm tra doc đúng có được lấy về không, còn Token F1/judge đánh giá câu trả lời. Quality Gate phát hiện lỗi cấu trúc/nội dung, Freshness phát hiện dữ liệu cũ. Cùng test set giúp đo riêng tác động của corruption. Repair thành công khi rebuild từ raw đưa Quality/Freshness và metrics về baseline.

## 8. Phân tích kết quả

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| Hit Rate | 1.0000 | 0.7000 | 1.0000 | Coverage retrieval giảm 30% |
| Token F1 | 0.7383 | 0.3590 | 0.7383 | Metric giảm mạnh nhất theo tỷ lệ |
| Judge Accuracy | 0.8000 | 0.4000 | 0.8000 | Giảm 50% |
| Judge Score | 4.2000 | 2.9000 | 4.2000 | Giảm 31% |
| Quality | PASS | FAIL | PASS | Duplicate + blank summary bị bắt |
| Freshness | PASS | FAIL | PASS | Stale ratio 37.5% ở corrupted |

Các corruption text/identity/date cùng làm giảm retrieval và answer quality. Repair từ raw loại các lỗi tổng hợp và phục hồi toàn bộ metrics.

## 9. Điều học được và hướng cải thiện

1. Benchmark phải deterministic mới so sánh được nhiều trạng thái.
2. Corruption nên vừa đủ mạnh để tạo signal nhưng vẫn kiểm soát được.
3. Report phải lấy số liệu từ artifact thay vì hard-code kết luận.

Nếu có thêm thời gian, tôi sẽ thêm test tự động kiểm tra đủ 6 scenario, 24 output rows và schema report.

## 10. Cam kết

- [x] Nội dung phản ánh đúng Task 4.
- [x] Có thể giải thích luồng end-to-end.
- [x] Mọi kết luận có artifact/metric.
- [x] Không chứa secret.

**Họ và tên:** Nguyễn Huy Hùng  
**Ngày xác nhận:** 2026-09-25
