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

### 4.1 Dashboard và trace

- [Dashboard Grafana](screenshots/grafana-dashboard.png) hiển thị traffic, error rate, p95, request đang xử lý, instance và chi phí mock.
- [Trace chậm](screenshots/jaeger-slow-trace.png), ID `d4e2c8d1e2781e38f0b6cfe3d7381b8d`. Request mất **1716,21 ms**. Span `chat mock-llm-small` mất **1690,95 ms** (98,53% tổng thời gian), nằm trong span `agent.run`.
- [Trace lỗi](screenshots/jaeger-error-trace.png), ID `d6bd732fd894cfa17e99f2b6cccef518`. Request trả **503** sau **102,97 ms**. Jaeger ghi sự kiện `exception` trên span gọi LLM.

Dòng log tương ứng lần lượt là sự kiện HTTP của trace chậm và lỗi mô phỏng upstream của trace lỗi.

```jsonl
{"ts":"2026-11-25T08:11:44.718614+00:00","level":"INFO","service":"observable-agent","instance":"8e015aec3c2d","event":"http_request","trace_id":"d4e2c8d1e2781e38f0b6cfe3d7381b8d","span_id":"76a8bbc22be45a32","request_id":"45b996b759e9","method":"POST","route":"/ask","status":200,"ms":1715.6}
{"ts":"2026-11-25T08:11:44.475864+00:00","level":"INFO","service":"observable-agent","instance":"72ff820c6d76","event":"llm_error","trace_id":"d6bd732fd894cfa17e99f2b6cccef518","span_id":"b4355db068c91872","request_id":"bca63aeccab0","error":"Upstream LLM error: 503 Service Unavailable (mock)"}
```

### 4.2 Cảnh báo Prometheus

Đặt `MOCK_ERROR_RATE=0.2` và `MOCK_SLOW_RATE=0.3` trên stack local rồi gửi request liên tục đến `/ask`. Thời gian bên dưới tính từ lúc bắt đầu gửi request sau khi stack báo healthy, với chu kỳ thăm dò 2 giây. [Ảnh hai cảnh báo cùng firing](screenshots/prometheus-alert-firing.png)

| Thay đổi | Alert | Thời gian quan sát | Panel liên quan |
| --- | --- | --- | --- |
| Tăng xác suất lỗi mock lên 20% | `AgentHighErrorRate` | 86,6 giây | Error rate |
| Tăng xác suất request chậm lên 30% | `AgentHighLatencyP95` | 143,0 giây | Latency p95 |

Rule lỗi yêu cầu tỷ lệ lỗi trên 5% trong 1 phút. Rule độ trễ yêu cầu p95 trên 1 giây trong 2 phút. Dữ liệu được scrape và đánh giá theo chu kỳ nên thời điểm quan sát có thể muộn hơn thời gian `for` của rule. `LLMCostBurnRateHigh` đã firing từ lượt load test trước thí nghiệm.

## 5. Benchmark scaling

Locust headless chạy 100 user, ramp 10 user/giây và thời lượng 2 phút. Số bên dưới lấy từ dòng `POST /ask` trong hai CSV.

| Số instance | Request | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Thất bại |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 7068 | 59.15 | 190 | 320 | 1700 | 73 (1.03%) |
| 3 | 7142 | 59.89 | 190 | 220 | 1700 | 65 (0.91%) |

Tăng từ một lên ba instance giữ RPS gần như nhau ở tải này và giảm p95 quan sát được. Cả hai lượt còn p99 ở khoảng 1,7 giây, phù hợp với việc mock chủ động thêm 1,5 giây vào một phần request. Locust dùng cùng số user và khoảng chờ giữa các tác vụ, nên đây là phép so sánh ở một cấu hình tải cố định.
