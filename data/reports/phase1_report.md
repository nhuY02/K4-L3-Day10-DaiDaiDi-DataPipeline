# Phase 1 Report - Baseline Pipeline (Du Lieu Sach)

_Sinh tu dong luc 2026-09-25T10:31:17+00:00._

## 1. Nguon Du Lieu & Cau Hinh

| Hang muc | Gia tri |
| --- | --- |
| `source` | Crossref REST API |
| `records_loaded` | 24 |
| `records_cleaned` | 24 |
| `raw_response_path` | D:\AI_Thuc_Chien\25_9_2026\K4-L3-Day10-DaiDaiDi-DataPipeline\data\raw\crossref_response.json |
| `raw_records_path` | D:\AI_Thuc_Chien\25_9_2026\K4-L3-Day10-DaiDaiDi-DataPipeline\data\raw\crossref_records.json |
| `run_date` | 2026-09-25T10:30:52.530844+00:00 |

## 2. Ket Qua Danh Gia RAG (Baseline)

| Chi so | Gia tri |
| --- | --- |
| So cau hoi danh gia | 10 |
| Retrieval Hit Rate | 1.0000 |
| Mean Token F1 | 0.7383 |
| LLM Judge Accuracy | 0.8000 |
| Mean Judge Score (1-5) | 4.2000 |

### Ragas

| Metric | Gia tri |
| --- | --- |
| `skipped` | Set RUN_RAGAS=1 to enable the slower Ragas pass. |

## 3. Data Quality (Great Expectations 1.x)

**Trang thai tong the:** PASS

| Expectation type | Column | Ket qua | Result |
| --- | --- | --- | --- |
| `ExpectTableRowCountToBeBetween` | - | PASS | observed_value=24 |
| `ExpectColumnValuesToNotBeNull` | `paper_id` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |
| `ExpectColumnValuesToNotBeNull` | `title` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |
| `ExpectColumnValuesToNotBeNull` | `text_for_embedding` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |
| `ExpectColumnValuesToBeUnique` | `paper_id` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; missing_count=0; missing_percent=0.0000; unexpected_percent_total=0.0000; unexpected_percent_nonmissing=0.0000; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |
| `ExpectColumnValueLengthsToBeBetween` | `summary` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; missing_count=0; missing_percent=0.0000; unexpected_percent_total=0.0000; unexpected_percent_nonmissing=0.0000; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |

## 4. Freshness SLA

| Hang muc | Gia tri |
| --- | --- |
| Bai moi nhat | 2026-09-15 |
| Bai cu nhat | 2026-04-01 |
| So dong qua han | 0 |
| Tong so dong | 24 |
| Ty le qua han | 0.0000 |
| Nguong tuoi (ngay) | 180 |
| Ty le qua han toi da | 0.2500 |
| Dat Freshness SLA | PASS |

## 5. Nhan Xet

- Data quality gate: **PASS**
- Freshness SLA: **PASS** (0/24 dong qua 180 ngay).
- Baseline RAG: Hit Rate 1.0000, Token F1 0.7383 tren 10 cau hoi. Day la moc de doi chieu o Phase 2.
