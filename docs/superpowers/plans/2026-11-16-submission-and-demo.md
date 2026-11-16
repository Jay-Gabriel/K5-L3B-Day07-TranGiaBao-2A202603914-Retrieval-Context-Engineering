# Hoàn thiện bài nộp và demo

Mục tiêu: sửa các sai lệch đã kiểm tra, đánh giá có thể tái lập, demo dễ trình bày cho người mới. Người dùng đã yêu cầu thực hiện toàn bộ; triển khai trực tiếp trong workspace để giữ các file bài làm chưa commit.

- [x] Cài môi trường riêng; kiểm tra Qdrant/model thật, PDF và corpus Day 6. Không in secret.
- [x] Kiểm thử lỗi controller, output dev/test và API demo; sửa model chọn search/answer, giữ lỗi riêng với abstention, lưu model/usage/cấu hình/trace.
- [x] Giữ kết quả cũ trong legacy; tạo benchmark v2 từ tài liệu, bỏ filter không có metadata; chia dev/test trước chạy, kiểm tra evidence và không đưa gold vào runtime.
- [x] Chạy ba retrieval và các cấu hình trên dev, chạy agent dev, chốt lựa chọn bằng chất lượng và thời gian; sau đó chạy baseline và cấu hình chọn trên test. Không thay đổi pipeline sau test.
- [x] Đọc từng câu trả lời/context/citation, ghi nhãn hỗ trợ bởi AI có lý do đối chiếu PDF, tách rõ việc sinh nhãn và chạy agent. Không gọi nhãn AI là nhãn đã được sinh viên duyệt.
- [x] Làm lại demo tiếng Việt: câu gợi ý, trạng thái, câu trả lời, đoạn nguồn và mở PDF đúng trang; nâng cao thu gọn; không hardcode điểm; xử lý lỗi, keyboard/mobile và render an toàn.
- [x] Chạy unit/integration, kiểm tra UI browser desktop/mobile; viết báo cáo khớp output và hướng dẫn cài/chạy bằng đường dẫn tương đối.

Kiểm tra rủi ro: API timeout/429 là lỗi; JSON sai là lỗi; thiếu credential có thông báo; citation không đồng nghĩa được hỗ trợ; cache phân biệt model; server chỉ phục vụ route được phép; câu hỏi HTML được hiển thị dưới dạng text.

Kết quả: 28 unit/HTTP tests pass; browser fixtures desktop/mobile pass; live demo Gemini 3.1 Flash Lite trả lời có nguồn. Dev chốt lexical_context; test model 3.5 có quota 429 (baseline 1/7 lỗi, cấu hình chọn 5/7 lỗi), giữ nguyên và báo rõ. Nhãn AI hỗ trợ đã đối chiếu PDF, chờ sinh viên xác nhận; quyền/nguồn tài liệu chưa được sinh viên xác nhận. Reviewer độc lập không còn blocker code. Không công bố lại kết quả test như một lần chạy ổn định.
