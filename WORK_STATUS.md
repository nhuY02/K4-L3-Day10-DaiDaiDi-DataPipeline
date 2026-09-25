# WORK STATUS

## Mục tiêu hiện tại

- Hoàn thiện Task 3 — Quality gate bằng Great Expectations 1.x và Freshness SLA, giữ nguyên cấu trúc/hợp đồng code hiện có.

## Việc đã hoàn thành

- Hoàn thiện `run_data_quality_checks` bằng API Great Expectations 1.x với ephemeral context và Pandas DataFrame batch.
- Cài đủ bốn loại expectation bắt buộc: row count 5–5000, not-null cho ba cột quan trọng, unique `paper_id`, và `summary` dài tối thiểu 30 ký tự.
- Hoàn thiện `build_freshness_report`: thống kê ngày mới/cũ nhất, số/tỷ lệ stale, ngưỡng 180 ngày và cờ `is_fresh` theo mức tối đa 25%.
- Ghi quality/freshness artifacts bằng `core.utils.write_json` và các đường dẫn trong `Settings`.
- Có xử lý thiếu cột/dữ liệu tuổi không hợp lệ theo hướng quality gate fail thay vì làm sập pipeline.
- `python -m py_compile src/observability/quality.py` đã pass; `git diff --check` không báo lỗi nội dung.
- Đã chạy kiểm thử tích hợp thật bằng Great Expectations 1.23.1 và pandas 3.0.6 trong `.venv` trên snapshot 24 bản ghi.
- Baseline quality pass đủ 6 phép kiểm tra; corrupted quality fail đúng 4 lỗi được tiêm; trường hợp thiếu cột `summary` bị phát hiện mà không làm crash.
- Baseline freshness pass với stale ratio 1/24 (khoảng 4.17%); boundary đúng 25% pass, trên 25% fail, và `age_days` không hợp lệ bị đánh dấu fail.
- Các artifact kiểm thử được ghi trong thư mục tạm và đã tự động dọn, không làm bẩn `data/quality/`.

## Việc đang làm

- Không có.

## File đã sửa/tạo

- Sửa `src/observability/quality.py`.
- Cập nhật `WORK_STATUS.md`.

## Quyết định quan trọng

- Chỉ sửa file thuộc ownership Task 3; không thay đổi ingestion, pipeline, evaluation hay retrieval.
- Giữ nguyên hai chữ ký hàm public; helper và hằng số mới đều là nội bộ module.
- Ánh xạ report name chứa `baseline`/`corrupt` vào path cấu hình tương ứng; tên khác ghi vào `data/quality/<name>_quality_report.json`.
- `is_fresh` chỉ true khi có dữ liệu, toàn bộ `age_days` hợp lệ và stale ratio không vượt quá 25%.

## Lỗi/vấn đề còn tồn tại

- Chưa có clean dataframe do Task 2 tạo, nên chưa chạy được lệnh nghiệm thu end-to-end trên `data/clean/papers_clean.json`.

## Bước tiếp theo cần làm

- Khi Task 2 tạo clean dataframe, chạy lệnh nghiệm thu CP1 trong `docs/CHECKPOINTS.md` để sinh quality/freshness artifact chính thức trong `data/quality/`.
