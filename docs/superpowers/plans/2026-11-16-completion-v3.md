# Hoàn thiện bài nộp v3

Người dùng yêu cầu hoàn tất toàn bộ và tiếp tục push vào repo Jay-Gabriel. Phạm vi đang thực hiện là phần bắt buộc; câu hỏi về bonus đang chờ trả lời. Không hứa điểm chấm 100/100.

- [x] Rà rubric: nhãn AI có đối chiếu nguồn được phép; không tự đặt điều kiện sinh viên phải tự ký nhãn.
- [x] Giữ nguyên kết quả v2 và báo cáo lịch sử, không thay điểm lỗi bằng kết quả model khác.
- [x] Tạo v3: dev cũ 17 câu, test mới 7 câu, cùng corpus Day 6; model Gemini 3.1 Flash Lite.
- [x] Sửa CER để giữ evidence đã gửi khi answer API lỗi; thêm kiểm thử hồi quy.
- [x] Bổ sung chi phí ước tính theo pricing chính thức và cơ sở free-tier; tách khỏi hóa đơn thực.
- [x] Chạy 5 retrieval dev và 3 agent dev; đọc/chấm từng trace/context/PDF, chốt theo tiêu chí đã công bố.
- [x] Sau chốt chạy baseline và cấu hình chọn trên toàn bộ test mới; đối chiếu 5+2 câu cho mỗi cấu hình.
- [x] Hoàn thiện báo cáo, cách chạy, nguồn, giới hạn; xác nhận quyền tài liệu từ thông tin thực, không gán giấy phép giả.
- [ ] Kiểm tra độc lập, unit/UI/live demo, commit và push; xác nhận SHA GitHub.

V3 dev: baseline7/15, hybrid11/15, lexical14/15; cả3 không lỗi. Sau freeze lexical, test baseline1/5+2/2; lexical5/5+2/2, citation6/6, không lỗi. Nguồn/quyền: đã ghi chính xác provenance và giới hạn xác minh; chưa có phản hồi nguồn từ người dùng. Không được tự nâng trạng thái thành permission_verified.
