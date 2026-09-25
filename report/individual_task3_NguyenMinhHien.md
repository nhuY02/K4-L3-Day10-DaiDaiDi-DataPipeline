# Member Role Report — Task 3: Quality Gate & Freshness SLA

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Minh Hiển |
| MSSV | 2A202602759 |
| Khóa/Lớp | K4 |
| Tên nhóm | DaiDaiDi |
| Vai trò chính | Observability Owner |
| Repository | https://github.com/nhuY02/K4-L3-Day10-DaiDaiDi-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File/hàm | Input | Output | Trạng thái |
|---|---|---|---|---|
| Data Quality Gate | `src/observability/quality.py` | Clean/corrupted dataframe | Quality report JSON | Hoàn thành |
| Freshness SLA | `build_freshness_report()` | `published`, `age_days` | Freshness report | Hoàn thành |

Hỗ trợ tích hợp bằng cách xác minh quality/freshness payload cho reporting và pipeline.

## 3. Kết quả theo vai trò

- Great Expectations 1.x chạy bằng ephemeral context.
- Baseline: 6 validation results, 0 failed, overall PASS.
- Corrupted: FAIL ở unique `paper_id` và summary length.
- Freshness: baseline stale ratio 0%; corrupted 37.5% > 25%; repaired 0%.

Output chính: `data/quality/baseline_quality_report.json`, `corrupted_quality_report.json`, `repaired_quality_report.json`, `freshness_report.json`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Pipeline cần phát hiện lỗi dữ liệu trước khi coi dataset là đủ an toàn cho retrieval, đồng thời cần tách lỗi chất lượng nội dung khỏi lỗi dữ liệu cũ.

### Cách triển khai
Sử dụng GX 1.x `gx.get_context(mode="ephemeral")`, Pandas datasource/dataframe asset và batch toàn dataframe. Các expectation gồm row count, not-null cho ba cột bắt buộc, unique `paper_id`, summary length >=30. Freshness tính stale ratio từ `age_days > 180` và FAIL khi ratio >25%.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | DataFrame từ cleaning/corruption |
| Output | Dict `success/results` + JSON report |
| Phụ thuộc | `Settings`, `age_days`, clean schema |
| Module dùng output | Baseline pipeline, corruption flow, reporting |
| Lỗi cần xử lý | Missing column, empty dataframe, GX exception |

### Cách xác minh

```bash
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); print(run_data_quality_checks(df,s,'test')['success'])"
```

Kết quả baseline: `True`, 6 checks, 0 failed.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** GX có API cũ và API 1.x mới.
- **Phương án:** Dùng `context.sources...` cũ hoặc Data Source API mới.
- **Đã chọn:** GX 1.x ephemeral context.
- **Lý do:** Đúng requirement, không sinh cấu hình/file rác.
- **Bằng chứng:** Quality Gate chạy thành công trong cả baseline/corrupted/repaired.

## 6. Một lỗi/blocker đã xử lý

- **Triệu chứng:** Reporting ban đầu không hiển thị đúng chi tiết expectations.
- **Nguyên nhân:** Reporting đọc schema cũ (`expectations`) trong khi quality trả `results`.
- **Cách xử lý:** Phối hợp integration để đồng bộ contract `results`, `expectation_type`, `column`, `result`.
- **Xác minh:** Corruption report hiển thị đầy đủ PASS/FAIL từng expectation.
- **Điều học được:** Observability payload phải có schema ổn định cho downstream reporting.

## 7. Hiểu biết về luồng end-to-end

Raw Crossref được clean rồi index vào ChromaDB. Test set dùng DOI làm ground-truth doc ID để đo retrieval hit và answer metrics. Quality Gate kiểm tra tính hợp lệ/completeness/uniqueness, còn Freshness theo dõi tuổi dữ liệu. Cùng test set giúp so sánh ba trạng thái công bằng. Repair thành công khi Quality/Freshness PASS trở lại và metrics repaired bằng baseline.

## 8. Phân tích kết quả

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| Hit Rate | 1.0000 | 0.7000 | 1.0000 | Quality degradation đi cùng retrieval degradation |
| Token F1 | 0.7383 | 0.3590 | 0.7383 | Giảm mạnh khi dữ liệu bẩn |
| Judge Accuracy | 0.8000 | 0.4000 | 0.8000 | Phục hồi hoàn toàn |
| Judge Score | 4.2000 | 2.9000 | 4.2000 | Phục hồi hoàn toàn |
| Quality | PASS | FAIL | PASS | Hai expectation fail ở corrupted |
| Freshness | PASS | FAIL | PASS | 0% → 37.5% → 0% |

Duplicate/blank summary làm Quality Gate FAIL; stale-date đưa stale ratio vượt 25%. Sau repair, cả observability signals và agent metrics đều về baseline.

## 9. Điều học được và hướng cải thiện

1. Data quality và freshness là hai signal khác nhau và bổ sung cho nhau.
2. Quality Gate cần fail an toàn thay vì crash khi schema lỗi.
3. Observability có giá trị khi liên hệ được với RAG metrics.

Nếu có thêm thời gian, tôi sẽ lưu freshness report riêng cho baseline/corrupted/repaired thay vì dùng chung một path.

## 10. Cam kết

- [x] Nội dung phản ánh đúng Task 3.
- [x] Có thể giải thích luồng end-to-end.
- [x] Kết luận có artifact/metric.
- [x] Không chứa secret.

**Họ và tên:** Nguyễn Minh Hiển
**Ngày xác nhận:** 2026-09-25
