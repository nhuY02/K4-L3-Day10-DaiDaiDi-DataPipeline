# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
|---|---|
| Khóa/Lớp | K4 |
| Tên nhóm | DaiDaiDi |
| Repository | https://github.com/nhuY02/K4-L3-Day10-DaiDaiDi-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
|---:|---|---|---|---|
| 1 | Trần Thị Như Ý | 2A202602372 | Team Lead / Pipeline Integration | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| 2 | Hà Trung Dũng | 2A202602948 | Ingestion & Cleaning | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py` |
| 3 | Nguyễn Minh Hiển | 2A202602759 | Quality & Freshness | `src/observability/quality.py` |
| 4 | Nguyễn Huy Hùng | 2A202602990 | Evaluation, Corruption & Reporting | `src/evaluation/testset.py`, `src/ingestion/corruption.py`, `src/observability/reporting.py` |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thiện pipeline RAG end-to-end cho dữ liệu Crossref: ingestion có offline fallback, cleaning và tạo `text_for_embedding`, kiểm tra chất lượng bằng Great Expectations 1.x, Freshness SLA, test set 10 câu, ChromaDB index, baseline evaluation, 6 kịch bản corruption và repair từ raw records. Baseline xử lý 24 raw records thành 24 clean records, Quality Gate PASS và Freshness PASS. Kết quả baseline đạt `retrieval_hit_rate=1.000`, `mean_token_f1=0.7383`, `judge_accuracy=0.8000`, `mean_judge_score=4.2000`.

Sau corruption, Quality Gate FAIL do duplicate `paper_id` và summary không đạt độ dài; Freshness FAIL với stale ratio `0.375 > 0.25`. Các metric giảm xuống lần lượt `0.7000`, `0.3590`, `0.4000`, `2.9000`. Repair dựng lại dữ liệu từ raw records và đưa toàn bộ metric về đúng baseline, đồng thời Quality/Freshness trở lại PASS. Giới hạn chính là corpus nhỏ 24 records và cảnh báo cleanup từ package `multiprocess`, nhưng không làm hai pipeline thất bại.

## 3. Kiến trúc và luồng dữ liệu

```text
Crossref API / local snapshot
    -> raw response + raw records
    -> cleaning + data modeling
    -> MiniLM embeddings + ChromaDB
    -> fixed evaluation set
    -> baseline metrics + quality/freshness
    -> 6 corruption scenarios
    -> re-index + re-evaluate
    -> repair từ raw records
    -> Baseline / Corrupted / Repaired report
```

| Khối | Input | Xử lý chính | Output/artifact | Owner |
|---|---|---|---|---|
| Ingestion | Crossref/snapshot | Parse, retry, offline fallback | `data/raw/` | Hà Trung Dũng |
| Cleaning | Raw records | Normalize, dedup, `age_days`, embedding text | `data/clean/` | Hà Trung Dũng |
| Embedding/index | Clean dataframe | MiniLM + ChromaDB | `data/chroma/`, `data/embeddings/` | Trần Thị Như Ý |
| Evaluation | Clean dataframe | 10 câu, 4 `question_type`, metrics | `data/eval/`, `data/results/` | Nguyễn Huy Hùng |
| Observability | Clean/corrupted dataframe | GX 1.x + Freshness SLA | `data/quality/` | Nguyễn Minh Hiển |
| Corruption/repair | Baseline clean/raw | 6 corruption, rebuild từ raw | corrupted/repaired artifacts | Nguyễn Huy Hùng + Trần Thị Như Ý |
| Orchestration | Các module trên | Chạy đúng thứ tự end-to-end | reports + metrics | Trần Thị Như Ý |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
|---|---|
| `LLM_PROVIDER` | openai |
| `LLM_MODEL` | gpt-4o-mini |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày; stale ratio tối đa 25% |
| Random seed | `20261010` |

### Lệnh cài đặt và chạy

```bash
python -m pip install -e .
python script/run_phase1.py
python script/run_corruption_flow.py
```

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
|---|---|---|---|
| Baseline pipeline | Thành công | 2026-09-25 | `baseline_metrics.json`, `phase1_report.md` |
| Corruption flow | Thành công | 2026-09-25 | `corruption_log.json`, `corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
|---|---|
| Source | Crossref REST API, fallback `data/raw/crossref_response.json` |
| Query | `agentic retrieval augmented generation large language model` |
| Filter | `from-pub-date:<run_date-180d>,has-abstract:true` |
| Số record | 24 |
| Retry/fallback | Retry lỗi 429/5xx; lỗi mạng dùng snapshot local |

### Raw và clean schema

Các trường chính: `paper_id`, `title`, `summary`, `authors`, `categories`, `published`, `updated`, `abs_url`, `pdf_url`. Clean dataframe bổ sung `authors_joined`, `categories_joined`, `summary_chars`, `age_days`, `text_for_embedding`.

### Quy tắc cleaning

| Quy tắc | Quality dimension | Kết quả | Cách xác minh |
|---|---|---|---|
| Xóa JATS/HTML và normalize whitespace | Validity | PASS | 24 clean rows |
| Loại record thiếu DOI/title/date hợp lệ | Completeness | Không làm giảm snapshot chuẩn | 24 raw → 24 clean |
| Dedup theo `paper_id` | Uniqueness | 24 unique IDs | `df["paper_id"].is_unique=True` |
| Tính `age_days` | Freshness | Có trên toàn bộ clean data | Freshness report |
| Tạo `text_for_embedding` 5 phần | Retrieval readiness | PASS | Clean JSON/CSV |

`text_for_embedding` gồm Title, Authors, Published, Categories và Summary. `paper_id` dùng DOI làm document identity; `age_days=(run_date-published).days`.

## 6. Evaluation setup

| Thành phần | Cấu hình |
|---|---|
| Số câu hỏi | 10 |
| `question_type` | `summary`, `authors`, `date`, `categories` |
| Ground-truth doc ID | DOI/`paper_id` của document tạo câu hỏi |
| Embedding model | `all-MiniLM-L6-v2` |
| Vector store | ChromaDB, collection baseline/corrupted/repaired riêng |
| Retrieval `top_k` | 4 |
| LLM provider/model | openai/gpt-4o-mini |
| Test set chung | `data/eval/test_set.json` |

Cùng một test set được dùng cho ba trạng thái để thay đổi metric phản ánh thay đổi dữ liệu, không phải thay đổi đề đánh giá.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn | Trạng thái |
|---|---|---|
| Raw | `data/raw/` | Có |
| Clean | `data/clean/` | Có |
| Embeddings/index | `data/embeddings/`, `data/chroma/` | Có |
| Evaluation set | `data/eval/test_set.json` | Có |
| Baseline metrics | `data/results/baseline_metrics.json` | Có |
| Quality/freshness | `data/quality/` | Có |
| Baseline report | `data/reports/phase1_report.md` | Có |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
|---|---:|---|
| `retrieval_hit_rate` | 1.0000 | Ground-truth document được retrieval đầy đủ |
| `mean_token_f1` | 0.7383 | Mức khớp token trung bình của câu trả lời |
| `judge_accuracy` | 0.8000 | 80% câu được judge đánh giá đúng |
| `mean_judge_score` | 4.2000 | Điểm judge trung bình trên thang 1–5 |
| Ragas | Không chạy mặc định | Chỉ chạy khi bật `RUN_RAGAS=1` |

## 8. Data quality và freshness

### Quality checks

| Check | Kỳ vọng | Baseline |
|---|---|---|
| Row count | 5–5000 | PASS, 24 |
| Not-null | `paper_id`, `title`, `text_for_embedding` | PASS |
| Unique | `paper_id` | PASS |
| Summary length | >= 30 ký tự | PASS |

### Freshness

| Thuộc tính | Giá trị |
|---|---|
| Freshness đo tại | Clean dataframe |
| Ngưỡng tuổi | 180 ngày |
| Stale ratio tối đa | 25% |
| Baseline | PASS, stale ratio 0.0000 |
| Corrupted | FAIL, stale ratio 0.3750 |
| Repaired | PASS, stale ratio 0.0000 |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Signal/tác động |
|---|---|---|
| Drop latest records | Bỏ các bài mới nhất | Giảm dữ liệu tươi/retrieval coverage |
| Blank summary | Xóa summary | Summary-length expectation FAIL |
| Inject text noise | Chèn chuỗi rác | Làm embedding/retrieval kém |
| Truncate title | Cắt ngắn title | Phá khả năng lookup theo title |
| Stale date | Lùi published khoảng 5 năm | Freshness FAIL |
| Duplicate rows | Nhân bản row còn lại | Unique `paper_id` FAIL |

Corruption giữ tổng số dòng `24 → 24`, có 5 duplicated IDs và 6 blank summaries ở dữ liệu cuối. Log đầy đủ tại `data/results/corruption_log.json`.

Repair không sửa trực tiếp dữ liệu bẩn mà đọc lại `data/raw/crossref_records.json`, chạy lại cleaning và rebuild index, vì vậy khôi phục từ nguồn đã bảo toàn.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 1.0000 | 0.7000 | 1.0000 | Giảm 30%, phục hồi hoàn toàn |
| `mean_token_f1` | 0.7383 | 0.3590 | 0.7383 | Giảm 51.4%, phục hồi hoàn toàn |
| `judge_accuracy` | 0.8000 | 0.4000 | 0.8000 | Giảm 50%, phục hồi hoàn toàn |
| `mean_judge_score` | 4.2000 | 2.9000 | 4.2000 | Giảm 31%, phục hồi hoàn toàn |
| Quality Gate | PASS | FAIL | PASS | Corruption bị phát hiện |
| Freshness | PASS | FAIL | PASS | 0% → 37.5% → 0% stale |

Hai chuỗi bằng chứng chính:

1. Corruption → duplicate/blank/stale signals xuất hiện → retrieval và answer metrics giảm rõ rệt.
2. Rebuild từ raw → Quality/Freshness trở lại PASS → toàn bộ metrics trở đúng baseline.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Sau merge, phần TASK2 bị ghi đè một phần và report đọc schema cũ của quality payload.
- **Nguyên nhân:** Resolve conflict làm thay đổi code đã test; `reporting.py` dùng key cũ (`expectations`, `threshold_days`).
- **Cách xử lý:** Restore bản TASK2 đã PASS, đồng bộ reporting với `results` và `freshness_threshold_days`, sửa bảng Freshness bị lặp.
- **Cách xác minh:** Chạy lại cả `run_phase1.py` và `run_corruption_flow.py`; metrics repaired khớp baseline.

## 12. Giới hạn và hướng cải thiện

| Giới hạn | Ảnh hưởng | Hướng cải thiện |
|---|---|---|
| Corpus chỉ 24 records | Benchmark còn nhỏ | Tăng corpus và giữ test set cố định |
| Cảnh báo cleanup `multiprocess` trên Windows | Nhiễu console nhưng exit code vẫn thành công | Pin/upgrade dependency và kiểm tra lại |
| HF Hub chạy unauthenticated | Rate limit thấp hơn | Dùng `HF_TOKEN` nếu cần tải nhiều model |

## 13. Checklist trước khi nộp

- [ ] Điền đủ họ tên/MSSV và LLM provider/model thực tế.
- [x] Phân công khớp module và commit thực tế.
- [x] Hai pipeline đã chạy lại thành công.
- [x] Ba trạng thái dùng cùng evaluation set.
- [x] Metrics khớp artifacts.
- [x] Quality/Freshness khớp report.
- [x] Artifacts và reports đã sinh đầy đủ.
- [x] Không đưa `.env`, API key hoặc secret vào báo cáo.
