# Member Role Report — Task 2: Ingestion & Cleaning

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Hà Trung Dũng |
| MSSV | 2A202602948 |
| Khóa/Lớp | K4 |
| Tên nhóm | DaiDaiDi |
| Vai trò chính | Ingestion & Cleaning Owner |
| Repository | https://github.com/nhuY02/K4-L3-Day10-DaiDaiDi-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File/hàm | Input | Output | Trạng thái |
|---|---|---|---|---|
| Raw ingestion | `src/ingestion/crossref.py` | Crossref API/snapshot | `PaperRecord`, raw JSON | Hoàn thành |
| Cleaning/data modeling | `src/ingestion/cleaning.py` | `list[PaperRecord]` | Clean dataframe/CSV/JSON | Hoàn thành |

Hỗ trợ tích hợp bằng cách xác minh lại TASK2 sau merge và đảm bảo schema phù hợp retrieval/quality.

## 3. Kết quả theo vai trò

- Ingestion nạp đúng 24 records và có offline fallback.
- Cleaning tạo 24 rows, 24 unique `paper_id`.
- Có đầy đủ `age_days`, `summary_chars`, `authors_joined`, `categories_joined`, `text_for_embedding`.
- Output dùng trực tiếp cho Quality Gate, test set và ChromaDB.

Output cụ thể: `data/raw/crossref_records.json`, `data/clean/papers_clean.csv`, `data/clean/papers_clean.json`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Dữ liệu Crossref có field thiếu, abstract chứa JATS/XML và API có thể lỗi/rate-limit. Pipeline cần vừa tái lập được offline vừa tạo schema sạch ổn định.

### Cách triển khai
Parser chuẩn hóa DOI/title, bỏ JATS/HTML trong abstract, parse authors/categories/date và PDF URL. Fetch dùng retry cho lỗi mạng/429/5xx và fallback snapshot. Cleaning parse datetime UTC, dedup `paper_id`, tính `age_days` và tạo embedding text theo 5 phần cố định.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Crossref payload hoặc `crossref_response.json` |
| Output | `PaperRecord` và dataframe 16 cột |
| Phụ thuộc | `src/core/config.py`, `src/core/utils.py` |
| Module dùng output | Quality, test set, retrieval, pipelines |
| Lỗi cần xử lý | Missing field, malformed date, network/rate limit, duplicate DOI |

### Cách xác minh

```bash
python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(len(r))"
python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(len(df), df['paper_id'].is_unique)"
```

Kết quả thực tế: `24` records; `24 True`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Live API không đảm bảo luôn sẵn sàng.
- **Phương án:** Bắt buộc gọi live API hoặc ưu tiên snapshot và chỉ refresh khi được yêu cầu.
- **Đã chọn:** Dual-mode, bảo toàn snapshot tốt và fallback offline.
- **Lý do:** Reproducible và không làm lab phụ thuộc mạng/Crossref rate limit.
- **Bằng chứng:** Offline/no-overwrite/date/JATS checks PASS và 24 records được nạp ổn định.

## 6. Một lỗi/blocker đã xử lý

- **Triệu chứng:** Sau merge, `crossref.py`/`cleaning.py` trên `main` không còn đúng bản TASK2 đã test.
- **Nguyên nhân:** Merge conflict đã ghi đè một phần implementation.
- **Cách xử lý:** Restore hai file từ branch `task2-ingestion-cleaning`, sau đó chạy lại ingestion/cleaning tests.
- **Xác minh:** 24 raw → 24 clean, unique `paper_id=True`, baseline pipeline PASS.
- **Điều học được:** Sau merge phải regression-test module, không chỉ kiểm tra conflict đã hết.

## 7. Hiểu biết về luồng end-to-end

Crossref/snapshot được parse và lưu raw; cleaning tạo dataframe; MiniLM embed `text_for_embedding` và ChromaDB index. Test set gắn câu hỏi với ground-truth DOI để đo retrieval và answer metrics. Quality checks kiểm tra completeness/uniqueness/content, còn freshness dùng `age_days`. Ba trạng thái phải dùng cùng test set. Repair được xem là thành công khi rebuild từ raw tạo dữ liệu sạch, Quality/Freshness PASS và metrics trở baseline.

## 8. Phân tích kết quả

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| Hit Rate | 1.0000 | 0.7000 | 1.0000 | Data sạch hỗ trợ retrieval ổn định |
| Token F1 | 0.7383 | 0.3590 | 0.7383 | Nội dung bẩn làm answer quality giảm mạnh |
| Judge Accuracy | 0.8000 | 0.4000 | 0.8000 | Phục hồi hoàn toàn |
| Judge Score | 4.2000 | 2.9000 | 4.2000 | Phục hồi hoàn toàn |
| Quality | PASS | FAIL | PASS | Duplicate/blank bị phát hiện |
| Freshness | PASS | FAIL | PASS | Repair trả stale ratio về 0 |

Corruption làm dữ liệu mất uniqueness/completeness/freshness và kéo metric xuống. Rebuild từ raw bằng chính cleaning pipeline đưa signal và metric về baseline.

## 9. Điều học được và hướng cải thiện

1. Raw preservation là nền tảng để repair đáng tin cậy.
2. Cleaning schema phải phục vụ đồng thời retrieval và observability.
3. Chất lượng input có ảnh hưởng trực tiếp đến RAG metrics.

Nếu có thêm thời gian, tôi sẽ bổ sung unit test cho các payload Crossref thiếu field và các định dạng date khác nhau.

## 10. Cam kết

- [x] Nội dung phản ánh đúng Task 2.
- [x] Có thể giải thích luồng end-to-end.
- [x] Mọi kết luận có artifact/metric.
- [x] Không chứa secret.

**Họ và tên:** Hà Trung Dũng  
**Ngày xác nhận:** 2026-09-25
