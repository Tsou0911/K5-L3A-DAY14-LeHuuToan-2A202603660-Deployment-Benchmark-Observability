# Deployment — Day 14

**Trạng thái** — Đã kiểm tra image và agent với Redis trên máy local. Chưa có URL public hoặc ảnh dashboard cloud.

Service triển khai dùng thư mục `06-lab-complete/`, Dockerfile multi-stage và cấu hình `railway.toml`. Cấu hình health check là `/health`. Agent nhận cổng từ `PORT` và cần một Redis service để `/ready` báo sẵn sàng và `/ask` xử lý câu hỏi.

| Biến môi trường | Giá trị cần đặt khi triển khai |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `REDIS_URL` | Biến tham chiếu tới URL kết nối Redis của project |
| `AGENT_API_KEY` | Secret riêng do người deploy tạo |
| `RATE_LIMIT_PER_MINUTE` | `10` |
| `DAILY_BUDGET_USD` | `1.0` |
| `PORT` | Giá trị do nền tảng cấp, mặc định của image là `8000` |

## Kiểm tra URL sau khi deploy

Chạy từ PowerShell sau khi `BASE` và `AGENT_API_KEY` có trong môi trường. Cột kết quả kỳ vọng lần lượt là `200`, `200`, `401`, `200`.

```powershell
curl.exe -sS -o NUL -w '%{http_code}\n' "$env:BASE/health"
curl.exe -sS -o NUL -w '%{http_code}\n' "$env:BASE/ready"
'{"question":"Hello"}' | curl.exe -sS -o NUL -w '%{http_code}\n' -H 'Content-Type: application/json' --data-binary '@-' "$env:BASE/ask"
'{"question":"Hello"}' | curl.exe -sS -o NUL -w '%{http_code}\n' -H 'Content-Type: application/json' -H "X-API-Key: $env:AGENT_API_KEY" --data-binary '@-' "$env:BASE/ask"
```
