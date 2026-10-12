# Nhóm thực hiện K4 Track 3A

Tên nhóm: {{Tên nhóm}}

Repo chung: {{Link repo}}

Trưởng nhóm/người nộp: {{Họ tên và MSSV}}

Ngày lab/deadline áp dụng: {{Ngày giờ theo thông báo lớp}} — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: {{Commit SHA}}

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |
| 2 | Nguyễn Hoàng Việt | 2A202602602 | Phase C (`src/phase_c_guard.py`: pii_scan, check_input_rail, check_output_rail, run_adversarial_suite, measure_p95_latency) + Blueprint (`doc/reports/blueprint.md`) | `artifacts/guard_results.json`, `doc/reports/blueprint.md` |
| 3 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |

Người tích hợp/chạy batch/nộp link: {{Họ tên, công việc và bằng chứng}}.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: {{Phiên bản thực tế}}.
Virtualenv/dependencies/imports: {{Lệnh và kết quả}}.
Models/Qdrant/50 answers đã chuẩn bị: {{Bằng chứng và giới hạn/fallback}}.
Nếu cài full NeMo chưa thành công, ghi lỗi thực tế; không dùng unit test pass
hoặc pip resolve để khẳng định runtime đã chạy.

## INDIVIDUAL

Sao chép mẫu cho mỗi thành viên; tiêu đề họ tên không dấu-MSSV.

### NguyenHoangViet-2A202602602

- Phần được giao và phần thực tế đã làm: Phase C + Task 13. Trong
  `src/phase_c_guard.py` implement `pii_scan` (Presidio, lọc chỉ VN_CCCD/VN_PHONE/
  EMAIL_ADDRESS/PHONE_NUMBER), `check_input_rail`/`check_output_rail` (NeMo, đọc
  `activated_rails[*].stop`), `run_adversarial_suite` (Presidio → NeMo, một
  `asyncio.run`), `measure_p95_latency` (2 warm-up, 20 mẫu, linear). Cấu hình
  `guardrails/config.yml` + `guardrails/config.py` để NeMo 0.10 chạy DeepSeek.
  Viết `doc/reports/blueprint.md`.
- Bằng chứng: `artifacts/guard_results.json` (live, 2026-10-12T07:53:01Z,
  deepseek-flash), `doc/reports/blueprint.md`, commit Phase C của tôi trên repo chung.
- Cách kiểm tra: `python -m pytest tests/test_phase_c.py -q` → 12 passed (mock).
  Live: `python scripts/run_experiments.py --phase c --live --latency-samples 20` →
  attacks 20/20 blocked (4 presidio, 16 nemo_input), clean 8/8 allowed (FP 0.0),
  output 4/4 đúng; input guard P50/P95/P99 = 671.12/938.77/957.87ms.
- Điều đã học: Presidio PatternRecognizer cho định dạng VN; NeMo self check
  input/output với Colang 1.0 và prompt policy; quyết định chặn phải lấy từ log rail
  chứ không từ chữ "xin lỗi" (câu sạch 102 chứa cụm này); P95 nội suy tuyến tính,
  warm-up loại khỏi mẫu, đo tuần tự khác request short-circuit.
- Giới hạn/cách xử lý: (1) NER spaCy `en` gắn PERSON cho tiếng Việt và US_* bắt nhầm
  "v2024" làm 7/8 câu sạch bị chặn → lọc entity, kiểm lại 8/8 bằng chạy Presidio
  thật. (2) NeMo 0.10 gọi completions API cho model không phải `gpt-*` (DeepSeek
  422) → đăng ký engine `deepseek` = ChatOpenAI. (3) deepseek-flash dùng hết
  `max_tokens=3` cho reasoning, trả rỗng → mọi câu bị chặn; đặt `thinking: disabled`.
  (4) Input guard P95 938.77ms vượt budget 500ms; bottleneck là LLM call của NeMo,
  ghi trong blueprint, chưa tối ưu.
- Nguồn/AI hỗ trợ nếu có: Claude Code hỗ trợ implement, debug cấu hình DeepSeek và
  soạn blueprint; tôi tự kiểm chứng bằng unit test, chạy live và đối chiếu số trong
  `artifacts/guard_results.json`.

- Phần được giao và phần thực tế đã làm: {{Nhiệm vụ, file/hàm, mục đích}}.
- Bằng chứng: {{Commit/PR và artifacts/reports liên quan}}.
- Cách kiểm tra: {{Unit mock hoặc live experiment, lệnh và kết quả}}.
- Điều đã học: {{Khái niệm và cách thể hiện trong bài}}.
- Giới hạn/cách xử lý: {{Vấn đề và kiểm chứng}}.
- Nguồn/AI hỗ trợ nếu có: {{Công cụ, phạm vi, cách tự kiểm chứng}}.

## Cập nhật sau khi nộp

{{Ghi phiên bản nộp; nếu sửa sau deadline, ghi commit/thời điểm/lý do và thông báo
coach cho phép áp dụng bản cập nhật. Nếu không có cập nhật, ghi rõ không có.}}
