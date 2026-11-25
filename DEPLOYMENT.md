# Deployment — Day 14

**URL public** — [Agent Day 14 trên Railway](https://agent-production-69904596.up.railway.app/health)

**Triển khai ngày 25/11/2026** — Project `day14-agent`, environment `production`, chạy service `agent` và `Redis`. Bản triển khai lấy các tệp runtime từ `06-lab-complete/` của commit `0719a14`. [Project Railway](https://railway.com/project/54ee9315-d17e-424d-99f6-c2de71aa5797)

Service triển khai dùng thư mục `06-lab-complete/`, Dockerfile multi-stage và cấu hình `railway.toml`. Cấu hình health check là `/health`. Agent nhận cổng từ `PORT` và cần một Redis service để `/ready` báo sẵn sàng và `/ask` xử lý câu hỏi.

| Biến môi trường | Giá trị cần đặt khi triển khai |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `REDIS_URL` | `${{Redis.REDIS_URL}}`, tham chiếu service Redis |
| `AGENT_API_KEY` | Secret được tạo khi triển khai, xem trong Variables của service `agent` |
| `RATE_LIMIT_PER_MINUTE` | `10` |
| `DAILY_BUDGET_USD` | `1.0` |
| `PORT` | `8000`, cùng cổng đích của domain Railway |

## Kiểm tra URL sau khi deploy

Kết quả quan sát qua URL HTTPS public. [Ảnh tổng hợp kết quả HTTP](screenshots/test.png)

| Request | HTTP |
| --- | --- |
| `GET /health` | 200 |
| `GET /ready` | 200 |
| `POST /ask`, thiếu API key | 401 |
| `POST /ask`, có API key hợp lệ | 200 |

Để kiểm tra lại bằng PowerShell, đặt `AGENT_API_KEY` trong môi trường trước khi chạy.

```powershell
$env:BASE='https://agent-production-69904596.up.railway.app'
curl.exe -sS -o NUL -w '%{http_code}\n' "$env:BASE/health"
curl.exe -sS -o NUL -w '%{http_code}\n' "$env:BASE/ready"
'{"question":"Hello"}' | curl.exe -sS -o NUL -w '%{http_code}\n' -H 'Content-Type: application/json' --data-binary '@-' "$env:BASE/ask"
'{"question":"Hello"}' | curl.exe -sS -o NUL -w '%{http_code}\n' -H 'Content-Type: application/json' -H "X-API-Key: $env:AGENT_API_KEY" --data-binary '@-' "$env:BASE/ask"
```
