# Benchmark & Observability Report — Day 14

**Họ tên** — Lê Hữu Toàn

**Ngày chạy** — 25/11/2026

**Môi trường** — Windows PowerShell, Python 3.13 cho benchmark develop, Docker Desktop Linux cho stack observability.

## 1. SLO

| SLI | Mục tiêu | Lý do |
| --- | --- | --- |
| p95 latency của `/ask` | ≤ 500 ms | Đo mức phản hồi mà phần lớn request thực tế đạt được. |
| Tỷ lệ lỗi của `/ask` | ≤ 2% | Cho phép một lượng lỗi mock nhỏ và phát hiện khi dịch vụ xuống cấp. |
| Accuracy | ≥ 85% trong CI | Phát hiện phiên bản trả lời kém trước khi merge. Bản sửa kiến thức được kiểm tra riêng với ngưỡng 100%. |

## 2. Benchmark hiệu năng

Mỗi lượt gửi 300 request đến agent v2. Số liệu chi tiết nằm trong `reports/load_v2_*.json`.

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Tỷ lệ lỗi | SLO |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 4.51 | 202.8 | 236.8 | 1678.6 | 0.67% | PASS |
| 10 | 32.27 | 202.3 | 233.2 | 1723.0 | 0.67% | PASS |
| 50 | 105.39 | 215.4 | 353.6 | 1718.0 | 1.33% | PASS |
| 100 | 60.81 | 338.5 | 3036.1 | 3250.2 | 1.00% | FAIL |

RPS tăng đến concurrency 50 rồi giảm ở mức 100 trong lần đo này. p95 và p99 cùng tăng mạnh ở mức 100, phù hợp với hiện tượng request phải chờ lâu hơn khi có nhiều request đồng thời.

| `MOCK_SLOW_RATE` | Trung bình (ms) | p95 (ms) | p99 (ms) |
| --- | --- | --- | --- |
| 0 | 203.5 | 232.0 | 251.5 |
| 0.03 | 262.4 | 248.2 | 1726.9 |
| 0.1 | 330.3 | 1692.6 | 1715.7 |

Ở mức 3% mô phỏng chậm, p99 tăng mạnh trong khi p95 vẫn gần mức cơ sở. Ở mức 10%, p95 cũng tăng. Trung bình trộn request nhanh và chậm nên che bớt tác động lên nhóm người dùng chờ lâu.

## 3. Eval chất lượng

Khi chạy eval, tắt lỗi và request chậm ngẫu nhiên của mock để đo chất lượng nội dung.

| Chỉ số | v1 | v2 trước sửa | v2 sau sửa |
| --- | --- | --- | --- |
| Accuracy | 4.35% (1/23) | 91.30% (21/23) | 100% (23/23) |
| Token trung bình | 57.7 | 109.0 | 112.4 |
| Tổng chi phí mock (USD) | 0.000413 | 0.000760 | 0.000780 |
| Chi phí mock mỗi câu đúng (USD) | 0.00041295 | 0.00003619 | 0.00003391 |
| Quality gate của lệnh eval | FAIL | PASS | PASS, 0 regression |

| Câu trả lời thiếu | Nội dung thêm vào knowledge base |
| --- | --- |
| `security-02` | JWT là token có chữ ký và thời điểm hết hạn. |
| `scaling-03` | Kubernetes HPA điều chỉnh số pod dựa trên CPU, memory hoặc custom metrics. |

Retrieval làm tăng số token và tổng chi phí mock so với v1, đồng thời giảm chi phí trên mỗi câu đúng vì số câu đúng tăng mạnh. Job `.github/workflows/eval.yml` chạy chất lượng trên pull request và nhánh `main`.

## 4. Observability

`http_requests_total` là counter, `agent_in_flight_requests` là gauge và `http_request_duration_seconds` là histogram. Agent dùng route template để nhóm request. Nếu gắn từng đường dẫn thực vào label thì mỗi đường dẫn mới có thể tạo time series mới và tăng bộ nhớ Prometheus. Histogram `agent_question_length_chars` ghi phân bố độ dài câu hỏi theo bucket cố định.

Chất lượng câu trả lời có thể giảm dù latency và tỷ lệ lỗi vẫn tốt. Để phát hiện, chạy eval định kỳ với golden dataset và dùng accuracy cùng số regression làm điều kiện phát hành.
