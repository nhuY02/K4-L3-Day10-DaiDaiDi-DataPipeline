# Member Role Report — Task 1: Pipeline Integration

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Trần Thị Như Ý |
| MSSV | 2A202602372 |
| Khóa/Lớp | K4 |
| Tên nhóm | DaiDaiDi |
| Vai trò chính | Team Lead / Pipeline Integration |
| Repository | https://github.com/nhuY02/K4-L3-Day10-DaiDaiDi-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File phụ trách | Input | Output | Trạng thái |
|---|---|---|---|---|
| Baseline orchestration | `src/pipelines/phase1.py` | Raw/clean/quality/testset modules | Baseline artifacts + metrics/report | Hoàn thành |
| Corruption/repair orchestration | `src/pipelines/corruption_flow.py` | Baseline artifacts + corruption module | Corrupted/repaired metrics + report | Hoàn thành |

Hỗ trợ chính ngoài phạm vi là tích hợp contract giữa các module và chạy nghiệm thu end-to-end.

## 3. Kết quả theo vai trò

- `python script/run_phase1.py` chạy thành công: 24 raw → 24 clean, Quality Gate PASS, Hit Rate 1.000, Token F1 0.7383.
- `python script/run_corruption_flow.py` chạy thành công và tạo bảng Baseline/Corrupted/Repaired.
- Output chính: `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json`, `phase1_report.md`, `corruption_report.md`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Nối ingestion, cleaning, observability, test set, vector index và evaluation thành hai flow chạy đúng thứ tự, không phá contract giữa các module.

### Cách triển khai
Baseline ưu tiên raw snapshot đã bảo toàn, clean dữ liệu, chạy Quality/Freshness, tạo/reuse test set, build Chroma index, evaluate rồi sinh report. Corruption flow chỉ chạy sau khi baseline artifacts tồn tại; sau corruption, dữ liệu repaired được dựng lại từ raw records rồi đánh giá bằng cùng test set.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | `Settings.paths`, raw/clean data, test set |
| Output | Metrics, answers, embeddings, Markdown reports |
| Phụ thuộc | Tasks 2–4 |
| Module dùng output | Evaluation/reporting và bước nộp bài |
| Lỗi cần xử lý | Thiếu baseline artifact, dataframe rỗng, Quality Gate baseline fail |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

Kết quả thực tế: cả hai flow hoàn tất và repaired metrics bằng baseline.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần so sánh ba trạng thái công bằng.
- **Phương án:** Tạo lại test set mỗi lần hoặc reuse một test set cố định.
- **Đã chọn:** Reuse `data/eval/test_set.json`.
- **Lý do:** Tránh thay đổi đề đánh giá làm sai ý nghĩa so sánh.
- **Bằng chứng:** Repaired trở đúng toàn bộ baseline metrics.

## 6. Một lỗi/blocker đã xử lý

- **Triệu chứng:** `corruption_flow.py` không được phép chạy khi baseline metrics chưa có.
- **Nguyên nhân:** Corruption evaluation phụ thuộc baseline và fixed test set.
- **Cách xử lý:** Kiểm tra required artifacts trước khi chạy và yêu cầu chạy Phase 1 trước.
- **Xác minh:** Sau `run_phase1.py`, corruption flow chạy đến cuối và sinh comparison report.
- **Điều học được:** Orchestration cần kiểm tra precondition thay vì để lỗi xuất hiện sâu trong pipeline.

## 7. Hiểu biết về luồng end-to-end

Crossref được parse thành raw records, cleaning tạo schema retrieval-ready, MiniLM tạo embedding và ChromaDB index. Evaluation dùng ground-truth `paper_id` để đo retrieval hit và câu trả lời. Quality Gate kiểm tra cấu trúc/nội dung, còn Freshness theo dõi tuổi dữ liệu. Cùng test set được giữ nguyên để so sánh công bằng. Repair thành công khi data quality/freshness trở lại PASS và metrics repaired trở về baseline.

## 8. Phân tích kết quả

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| Hit Rate | 1.0000 | 0.7000 | 1.0000 | Repair phục hồi hoàn toàn |
| Token F1 | 0.7383 | 0.3590 | 0.7383 | Corruption tác động mạnh |
| Judge Accuracy | 0.8000 | 0.4000 | 0.8000 | Phục hồi về baseline |
| Judge Score | 4.2000 | 2.9000 | 4.2000 | Phục hồi về baseline |
| Quality | PASS | FAIL | PASS | Gate phát hiện dữ liệu lỗi |
| Freshness | PASS | FAIL | PASS | Stale ratio 37.5% ở corrupted |

Corruption → quality/freshness xấu đi → agent metrics giảm. Rebuild từ raw → signals trở lại PASS → metrics trở đúng baseline.

## 9. Điều học được và hướng cải thiện

1. Pipeline cần contract và precondition rõ giữa các module.
2. Fixed evaluation set là bắt buộc khi đo tác động dữ liệu.
3. Repair nên rebuild từ nguồn tin cậy thay vì chỉnh trực tiếp dữ liệu lỗi.

Nếu có thêm thời gian, tôi sẽ thêm pytest/CI cho hai entrypoint và kiểm tra artifacts tự động.

## 10. Cam kết

- [x] Nội dung phản ánh đúng Task 1.
- [x] Có thể giải thích luồng end-to-end.
- [x] Kết luận có metrics/artifacts đối chiếu.
- [x] Không chứa secret.

**Họ và tên:** Trần Thị Như Ý 
**Ngày xác nhận:** 2026-09-25
