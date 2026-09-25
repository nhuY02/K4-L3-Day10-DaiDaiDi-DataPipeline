# Phân công task — Data Pipeline & Data Observability

## Requirement chính

Lab yêu cầu xây dựng pipeline RAG cho dữ liệu Crossref: lưu dữ liệu thô, làm sạch, kiểm tra chất lượng bằng Great Expectations 1.x và Freshness SLA, tạo bộ đánh giá, chạy baseline, tiêm 6 dạng lỗi, rồi phục hồi từ dữ liệu thô và so sánh ba trạng thái.

Trong repo hiện tại, `src/retrieval/` và `src/evaluation/metrics.py` đã có phần lớn logic. Các TODO tập trung ở ingestion, quality, test set, báo cáo và hai pipeline điều phối.

Vì thời gian chỉ khoảng 30 phút, nên chia theo các module độc lập và ưu tiên đưa baseline chạy được trước. Đầu việc corruption/repair có thể tiếp tục sau khi có baseline.

## Task 1 — Dựng baseline pipeline

**Owner:** Bạn — Team Lead  
**Mục tiêu:** Nối các module thành baseline end-to-end và điều phối luồng corruption/repair sau khi các phần nền tảng sẵn sàng.  
**Requirement liên quan:** Baseline pipeline, sinh metrics và báo cáo pha 1; corruption flow, repair và báo cáo so sánh.  
**Files cần sửa:** `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`  
**Files không được sửa:** Các file trong `src/ingestion/`, `src/observability/`, `src/evaluation/`, `src/retrieval/`  
**Input/dependency:** Dùng các hàm do Task 2 và Task 3 cung cấp; giao diện đầu vào/đầu ra phải giữ theo chữ ký hiện có.  
**Output cần hoàn thành:** Hai pipeline điều phối các bước hiện có, ghi artifacts theo `Settings.paths` và có thể chạy qua hai script entrypoint.  
**Definition of Done:** `run_phase1.py` chạy đến hết khi các module phụ thuộc hoàn tất; corruption flow gọi được corruption, đánh giá dữ liệu lỗi, dựng lại dữ liệu từ raw và tạo báo cáo đối chiếu.  
**Ước lượng độ khó:** Cao; dành phần lớn thời gian cho baseline trước, rồi mới nối corruption/repair.

## Task 2 — Ingestion và làm sạch dữ liệu

**Owner:** Thành viên 2  
**Mục tiêu:** Nạp Crossref từ API hoặc snapshot offline, lưu raw records và tạo dataframe sạch.  
**Requirement liên quan:** Raw preservation, fallback offline, khử trùng lặp, tính `age_days`, tạo `text_for_embedding`.  
**Files cần sửa:** `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`  
**Files không được sửa:** `src/pipelines/`, `src/observability/`, `src/evaluation/`  
**Input/dependency:** Schema `PaperRecord` và cấu hình hiện có trong `src/core/`.  
**Output cần hoàn thành:** Hàm lấy/lưu/parse raw records và hàm tạo clean dataframe với các cột mà retrieval và quality gate cần.  
**Definition of Done:** Offline snapshot cho ra records; cleaning tạo dataframe không trùng `paper_id`, có `age_days` và `text_for_embedding`.  
**Ước lượng độ khó:** Trung bình.

## Task 3 — Quality gate và Freshness SLA

**Owner:** Thành viên 3  
**Mục tiêu:** Hoàn thiện kiểm định dữ liệu theo Great Expectations 1.x và báo cáo độ tươi.  
**Requirement liên quan:** Bốn expectation bắt buộc; cảnh báo khi tỷ lệ bản ghi có `age_days > 180` vượt 25%.  
**Files cần sửa:** `src/observability/quality.py`  
**Files không được sửa:** `src/pipelines/`, `src/ingestion/`, `src/evaluation/`  
**Input/dependency:** Nhận dataframe đã làm sạch từ Task 2; dùng cấu hình và đường dẫn trong `Settings`.  
**Output cần hoàn thành:** Quality check trả kết quả pass/fail và freshness report ghi ra đúng artifact.  
**Definition of Done:** Có row count, not-null, unique `paper_id`, summary length checks; ghi báo cáo baseline/corrupted và freshness theo cấu hình đường dẫn.  
**Ước lượng độ khó:** Trung bình đến cao do cần đúng API GX 1.x.

## Task 4 — Bộ test, corruption suite và báo cáo

**Owner:** Thành viên 4  
**Mục tiêu:** Sinh test set benchmark, triển khai 6 kiểu corruption và tạo báo cáo markdown.  
**Requirement liên quan:** 10 câu hỏi thuộc 4 nhóm; corruption log; báo cáo baseline và so sánh Baseline/Corrupted/Repaired.  
**Files cần sửa:** `src/evaluation/testset.py`, `src/ingestion/corruption.py`, `src/observability/reporting.py`  
**Files không được sửa:** `src/pipelines/`, `src/ingestion/cleaning.py`, `src/observability/quality.py`  
**Input/dependency:** Cần dataframe sạch từ Task 2; báo cáo so sánh nhận các metrics do pipeline cung cấp từ Task 1.  
**Output cần hoàn thành:** Test set 10 câu, corruption log đủ 6 lỗi, hai hàm sinh báo cáo markdown.  
**Definition of Done:** Các hàm ghi đúng artifact path từ tham số; corruption tạo dữ liệu thay đổi và log đủ 6 loại lỗi; báo cáo có bảng ba trạng thái.  
**Ước lượng độ khó:** Cao nếu làm trọn cả ba module trong 30 phút; ưu tiên test set và corruption trước, báo cáo sau.

## Dependency

- Task 2 phải hoàn thành phần schema/clean dataframe trước khi Task 3 chạy kiểm tra hoặc Task 4 sinh test set.
- Task 2 và Task 3 cung cấp đầu vào cho baseline ở Task 1.
- Task 4 cung cấp test set, corruption và báo cáo cho Task 1.
- Task 1 tích hợp cuối; các thành viên nên thống nhất chữ ký hàm và tên artifact trước khi code.

## File ownership

| File | Owner |
| ---- | ----- |
| `src/pipelines/phase1.py` | Team Lead |
| `src/pipelines/corruption_flow.py` | Team Lead |
| `src/ingestion/crossref.py` | Thành viên 2 |
| `src/ingestion/cleaning.py` | Thành viên 2 |
| `src/observability/quality.py` | Thành viên 3 |
| `src/evaluation/testset.py` | Thành viên 4 |
| `src/ingestion/corruption.py` | Thành viên 4 |
| `src/observability/reporting.py` | Thành viên 4 |

Không giao sửa retrieval trong vòng này vì các module embedding, Chroma index và QA hiện đã có code; chỉ xử lý nếu pipeline phát hiện lỗi tích hợp cụ thể.

## Team Lead task

Bạn nên sở hữu `phase1.py` và `corruption_flow.py`. Đây là điểm tích hợp các module, nên bạn có thể vừa code luồng tổng thể vừa kiểm tra hợp đồng đầu vào/đầu ra với từng thành viên mà ít phải sửa chung file.

## Execution order

1. Cả nhóm thống nhất chữ ký hàm, cột dataframe và đường dẫn artifacts; Task 2–4 bắt đầu song song trên các file được phân quyền.
2. Thành viên 2 hoàn tất raw loading và clean dataframe; Team Lead nối baseline theo giao diện đã thống nhất.
3. Thành viên 3 hoàn tất quality/freshness; thành viên 4 hoàn tất test set và corruption.
4. Team Lead nối corruption/repair flow và báo cáo.
5. Chạy hai script entrypoint, sửa lỗi tích hợp theo ownership đã chia.

Trong mốc 30 phút, mục tiêu thực tế là hoàn tất luồng baseline trước. Corruption/repair và bảng đối chiếu nên là phần tiếp theo nếu còn thời gian; nếu cần nộp ngay sau 30 phút thì nên ưu tiên test set, quality gate và corruption suite trước phần báo cáo mở rộng.
