# Blueprint CI/CD cho RAG và guardrails

Nhóm: EvalGuard

Người phụ trách: Nguyễn Hoàng Việt - 2A202602602

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy.
Nguồn kết quả: artifacts/ragas_50q.json, judge_results.json, guard_results.json.
Run timestamp: 2026-10-12T07:53:01.397231+00:00; guard models: deepseek-flash.
Models generation/evaluator/judge từ A/B: generation deepseek-flash (ragas_50q.json,
judge_results.json); evaluator deepseek-chat (ragas_50q.json); judge deepseek-chat
(judge_results.json).

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.
Request thực dừng sớm khi bị chặn; khác phép đo input layers chạy đủ hai tầng.

- **Presidio (Layer 1, local, ~11ms):** recognizers VN_CCCD (12/9 số), VN_PHONE
  (0[3-9] + 8 số) cùng EMAIL_ADDRESS, PHONE_NUMBER mặc định. Chỉ giữ 4 entity này:
  NER spaCy `en` gắn nhãn PERSON/LOCATION cho gần như mọi câu tiếng Việt và các
  recognizer US_* bắt nhầm "v2024", từng làm 7/8 câu sạch bị chặn.
  Failure action: chặn request, trả câu từ chối chuẩn, chỉ log bản `anonymized`.
- **NeMo input rail (Layer 2, `self check input`, deepseek-flash):** chặn jailbreak,
  prompt injection, giả danh quyền hạn, off-topic, yêu cầu dữ liệu người khác.
  Quyết định đọc từ `log.activated_rails[*].stop`, không dò từ khóa "xin lỗi"
  (câu sạch 102 chứa đúng cụm này và vẫn được cho qua).
- **RAG:** retrieval + generation như Phase A.
- **NeMo output rail (`self check output`):** chặn CCCD, SĐT/email cá nhân, lương
  cá nhân, credentials; câu bị chặn được thay bằng câu từ chối, câu an toàn giữ
  nguyên văn. Không thay RAGAS faithfulness.
- **Secrets:** API key chỉ nằm trong `.env` (gitignored) hoặc CI secret store, được
  NeMo đọc qua biến `OPENAI_API_KEY` (endpoint DeepSeek tương thích OpenAI,
  `base_url` trong `guardrails/config.yml`).
- **Fallback:** nếu LLM của rail lỗi/timeout thì **fail closed** (trả câu từ chối và
  log `rail_error`), không cho request đi thẳng vào RAG. Presidio vẫn chạy local.
- **Cấu hình DeepSeek:** NeMo 0.10 chỉ dùng chat API cho tên model `gpt-*`, nên
  `guardrails/config.py` đăng ký engine `deepseek` → ChatOpenAI. Self check gọi
  `max_tokens=3`; chế độ reasoning ăn hết 3 token và trả chuỗi rỗng (bị hiểu là
  chặn), nên config đặt `thinking: disabled`.

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Số mẫu timed: 20; warm-up: 2;
phương pháp: linear.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 10.99 | 14.56 | 16.63 | Đo Task 12, rất nhỏ so với budget |
| NeMo input | 660.13 | 928.65 | 947.09 | Đo Task 12, chiếm ~99% thời gian |
| Input guard sequential | 671.12 | 938.77 | 957.87 | Đo Task 12, vượt target 500ms |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer budget target: 500ms; kết quả thực tế/budget_ok: P95 938.77ms, false.
Bottleneck là một round-trip LLM của NeMo self check input (P50 660ms) tới API
DeepSeek ngoài mạng; Presidio chỉ ~15ms ở P95. Hướng giảm: model guard nhỏ/local
(classifier jailbreak hoặc LLM self-host gần app), cache quyết định cho câu lặp lại,
chạy Presidio và NeMo song song vì hai tầng độc lập. Mỗi thay đổi phải đo lại với
cùng protocol (2 warm-up, ≥20 mẫu, linear).
RAG, NeMo output và full guard giữ “chưa đo”. Kế hoạch: trong cùng event loop, ghi
`perf_counter` tại từng ranh giới (sau Presidio, sau NeMo input, sau retrieval,
sau generation, sau output rail) cho ≥20 câu sạch và ≥20 câu bị chặn, 2 warm-up,
báo P50/P95/P99 riêng cho request chạy hết và request short-circuit.

## CI gates đề xuất

- RAGAS faithfulness ≥0.75, avg_score ≥0.65 trên 50 câu.
- Attacks ≥18/20 cho CI đề xuất; clean 8/8 allowed; output cases đúng.
- Full guard P95 <500ms chỉ áp dụng sau khi thực sự đo full guard.

Mốc bắt buộc lab vẫn attacks ≥15/20; bonus ≥18/20 kèm clean controls đạt.

Job đề xuất (workflow **chưa triển khai**), chạy khi PR đổi `src/`, `guardrails/`,
`data/` hoặc `fixtures/`:

1. `python -m pytest -q` (unit test mock, không tốn API).
2. `python scripts/run_experiments.py --phase c --live --latency-samples 20` với
   secret `OPENAI_API_KEY`; phase a/b chạy nightly vì tốn API hơn.
3. `python scripts/check_lab.py` kiểm schema/metadata.
4. Một script gate (cần viết thêm) đọc artifacts và `sys.exit(1)` khi
   `adversarial.passed < MIN_ATTACKS_BLOCKED` (18), `clean.passed < 8`, có output case
   sai, hoặc RAGAS dưới ngưỡng. `MIN_*` là biến đề xuất; runner hiện tại chưa kiểm
   tra ngưỡng nên tự nó không phải quality gate. Gate latency chỉ bật sau khi đo
   full guard, và tạm thời chỉ cảnh báo vì input guard P95 hiện là 938.77ms.

## Monitoring và cải tiến

- **Block rate theo layer** (presidio / nemo_input / nemo_output) theo giờ; cảnh báo
  khi lệch >2x so với trung bình 7 ngày (dấu hiệu tấn công hoặc rail hỏng).
- **False positive:** cho người dùng bấm "bị chặn nhầm"; mẫu ngẫu nhiên 1% request bị
  chặn gửi reviewer HR/Security xem hàng tuần. Câu chặn nhầm đã xác nhận được thêm
  vào `clean_set` để CI bắt hồi quy. Cảnh báo khi FP rate ước lượng >2%.
- **Latency:** log `presidio_ms`, `nemo_input_ms`, `nemo_output_ms` mỗi request;
  cảnh báo khi P95 trượt 15 phút >1000ms hoặc tỉ lệ `rail_error` >1%.
- **Drift:** theo dõi phân bố chủ đề câu hỏi (embedding cluster) so với test set;
  cụm mới lớn thì bổ sung câu vào test set 50q và chạy lại RAGAS.
- **Privacy:** log chỉ lưu bản anonymized từ Presidio; không lưu raw input bị chặn
  vì PII. Người xử lý: chủ sở hữu guardrails (Security) và chủ sở hữu RAG (nhóm AI).
- **Giới hạn:** bộ 50/20/8/4 rất nhỏ; 20/20 và 8/8 không chứng minh tỉ lệ thật trên
  production, nhất là với tấn công đa lượt, mã hóa (base64), hoặc CCCD có dấu cách.

RAGAS mean/worst distribution: avg_score trung bình 0.7305 (50 câu); worst
distribution adversarial 0.6283, metric yếu nhất context_precision.
Cohen’s κ: 1.0.
Attacks passed: 20/20; clean false_positive_rate: 0.0.

Cải tiến có thể kiểm tra:

1. Mở rộng regex CCCD/SĐT cho dạng có dấu cách/chấm và +84 (thêm biến thể vào
   adversarial set, kỳ vọng vẫn 8/8 clean).
2. Thay NeMo self check bằng classifier nhỏ cho input; mục tiêu input guard P95
   <500ms mà vẫn ≥18/20 attacks.
3. Cải thiện context_precision cho câu adversarial (rerank/lọc chunk), đo lại
   avg_score adversarial (hiện 0.6283).
4. Thêm 20 câu sạch dễ nhầm (có "mật khẩu", "lương", số hiệu chính sách) để đo FP
   chặt hơn bộ 8 câu.
