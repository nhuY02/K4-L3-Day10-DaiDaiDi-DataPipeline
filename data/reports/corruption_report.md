# Corruption Report - Doi Chieu Baseline vs Corrupted vs Repaired

_Sinh tu dong luc 2026-09-25T10:32:27+00:00._

## 1. Bang So Sanh Hieu Nang 3 Trang Thai

| Chi so | Baseline | Corrupted | Repaired | Corrupted vs Baseline | Repaired vs Baseline |
| --- | --- | --- | --- | --- | --- |
| So cau hoi danh gia | 10 | 10 | 10 | 0.0000 (=) | 0.0000 (=) |
| Retrieval Hit Rate | 1.0000 | 0.7000 | 1.0000 | -0.3000 (xau di) | 0.0000 (=) |
| Mean Token F1 | 0.7383 | 0.3590 | 0.7383 | -0.3793 (xau di) | 0.0000 (=) |
| LLM Judge Accuracy | 0.8000 | 0.4000 | 0.8000 | -0.4000 (xau di) | 0.0000 (=) |
| Mean Judge Score (1-5) | 4.2000 | 2.9000 | 4.2000 | -1.3000 (xau di) | 0.0000 (=) |

## 2. Data Quality Gate

| Trang thai | Ket qua tong the | Expectation khong dat |
| --- | --- | --- |
| Corrupted | FAIL | `ExpectColumnValuesToBeUnique`, `ExpectColumnValueLengthsToBeBetween` |
| Repaired | PASS | - |

### Chi tiet expectations

| Trang thai | Expectation type | Column | Ket qua | Result |
| --- | --- | --- | --- | --- |
| Corrupted | `ExpectTableRowCountToBeBetween` | - | PASS | observed_value=24 |
| Corrupted | `ExpectColumnValuesToNotBeNull` | `paper_id` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |
| Corrupted | `ExpectColumnValuesToNotBeNull` | `title` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |
| Corrupted | `ExpectColumnValuesToNotBeNull` | `text_for_embedding` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |
| Corrupted | `ExpectColumnValuesToBeUnique` | `paper_id` | FAIL | element_count=24; unexpected_count=10; unexpected_percent=41.6667; partial_unexpected_list=10.1093/sleep/zsag091.0346, 10.20944/preprints202604.0339.v1, 10.2118/234689-pa, 10.21203/rs.3.rs-10423755/v1, 10.63646/kpqm1958, 10.1093/sleep/zsag091.0346, 10.20944/preprints202604.0339.v1, 10.2118/234689-pa, 10.21203/rs.3.rs-10423755/v1, 10.63646/kpqm1958; missing_count=0; missing_percent=0.0000; unexpected_percent_total=41.6667; unexpected_percent_nonmissing=41.6667; partial_unexpected_counts=value=10.1093/sleep/zsag091.0346; count=2, value=10.20944/preprints202604.0339.v1; count=2, value=10.2118/234689-pa; count=2, value=10.21203/rs.3.rs-10423755/v1; count=2, value=10.63646/kpqm1958; count=2; partial_unexpected_index_list=1, 2, 5, 8, 18, 19, 20, 21, 22, 23 |
| Corrupted | `ExpectColumnValueLengthsToBeBetween` | `summary` | FAIL | element_count=24; unexpected_count=6; unexpected_percent=25.0000; partial_unexpected_list=, , , , , ; missing_count=0; missing_percent=0.0000; unexpected_percent_total=25.0000; unexpected_percent_nonmissing=25.0000; partial_unexpected_counts=value=; count=6; partial_unexpected_index_list=1, 7, 8, 11, 19, 22 |
| Repaired | `ExpectTableRowCountToBeBetween` | - | PASS | observed_value=24 |
| Repaired | `ExpectColumnValuesToNotBeNull` | `paper_id` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |
| Repaired | `ExpectColumnValuesToNotBeNull` | `title` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |
| Repaired | `ExpectColumnValuesToNotBeNull` | `text_for_embedding` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |
| Repaired | `ExpectColumnValuesToBeUnique` | `paper_id` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; missing_count=0; missing_percent=0.0000; unexpected_percent_total=0.0000; unexpected_percent_nonmissing=0.0000; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |
| Repaired | `ExpectColumnValueLengthsToBeBetween` | `summary` | PASS | element_count=24; unexpected_count=0; unexpected_percent=0.0000; partial_unexpected_list=n/a; missing_count=0; missing_percent=0.0000; unexpected_percent_total=0.0000; unexpected_percent_nonmissing=0.0000; partial_unexpected_counts=n/a; partial_unexpected_index_list=n/a |

## 3. Freshness SLA

| Hang muc | Corrupted | Repaired |
| --- | --- | --- |
| So dong qua han | 9 | 0 |
| Tong so dong | 24 | 24 |
| Ty le qua han | 0.3750 | 0.0000 |
| Nguong tuoi (ngay) | 180 | 180 |
| Ty le qua han toi da | 0.2500 | 0.2500 |
| Dat Freshness SLA | FAIL | PASS |
| Bai moi nhat | 2026-08-27 | 2026-09-15 |

## 4. Phan Tich

- **Retrieval Hit Rate**: 1.0000 -> 0.7000 khi du lieu bi lam ban (giam 30.0%). Sau repair ve dung muc baseline (1.0000).
- **Mean Token F1**: 0.7383 -> 0.3590 khi du lieu bi lam ban (giam 51.4%). Sau repair ve dung muc baseline (0.7383).
- **LLM Judge Accuracy**: 0.8000 -> 0.4000 khi du lieu bi lam ban (giam 50.0%). Sau repair ve dung muc baseline (0.8000).
- **Mean Judge Score (1-5)**: 4.2000 -> 2.9000 khi du lieu bi lam ban (giam 31.0%). Sau repair ve dung muc baseline (4.2000).

**Ket luan:** Idempotent repair doc lai tu raw snapshot da khoi phuc hoan toan cac chi so ve muc baseline.
