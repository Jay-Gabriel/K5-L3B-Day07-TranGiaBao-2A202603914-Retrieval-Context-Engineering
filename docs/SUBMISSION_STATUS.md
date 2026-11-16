# Trạng thái bài làm

Đã sửa và kiểm tra code, xuất đúng payload Day 6, tạo benchmark v2, chạy dev và chốt cấu hình trước test, chạy toàn bộ test cho baseline và cấu hình chọn, đọc trace/PDF và cập nhật báo cáo. Code review độc lập không còn blocker được phát hiện. 28 kiểm thử code/HTTP và browser fixtures desktop/mobile đã qua.

Demo đang dùng Gemini 3.1 Flash Lite; đã kiểm tra trực tiếp trả lời đúng câu hỏi biểu hiện lâm sàng với citation trang 3. Model benchmark Gemini 3.5 Flash Lite chạm quota 500 request/ngày. Kết quả test giữ cả lỗi: baseline 1/7, cấu hình chọn 5/7. Chưa thể coi kết quả này là một lần đánh giá test ổn định hoặc kết luận cấu hình chọn thắng trên test. Không lấy điểm dev hay demo thay điểm test.

Trước khi nộp, sinh viên cần:

- Đọc và xác nhận nhãn AI hỗ trợ, lưu bản xác nhận riêng; không tự nhận nhãn hiện tại đã được sinh viên duyệt.
- Bổ sung nguồn truy cập hợp lệ và xác nhận quyền dùng/chia sẻ tài liệu. URL ứng viên chưa truy cập được để kiểm tra byte gốc.
- Khi cần một lần test ổn định, chờ quota reset hoặc chuẩn bị chiến dịch model/benchmark mới đúng quy trình; giữ cả lần lỗi. Nếu đã điều chỉnh từ test, cần test mới.
- Repo cá nhân: https://github.com/Jay-Gabriel/K5-L3B-Day07-TranGiaBao-2A202603914-Retrieval-Context-Engineering. Cấp quyền người chấm và nộp link theo hướng dẫn lớp. Không push vào repo đề bài; không đưa `.env` lên Git.

Cách chạy: [RUN.md](../RUN.md). Kịch bản demo: [DEMO.md](DEMO.md). Báo cáo: [2A202603914_TranGiaBao.md](../report/individual/2A202603914_TranGiaBao.md).
