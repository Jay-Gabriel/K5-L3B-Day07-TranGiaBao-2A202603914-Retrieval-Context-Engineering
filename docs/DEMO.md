# Trình bày demo trong 3–5 phút

Khởi động theo [RUN.md](../RUN.md), mở http://127.0.0.1:8502. Chỉ chạy demo sau khi dừng benchmark để tránh tranh quota API.

1. **Giới thiệu nguồn.** Thẻ tài liệu ghi tên bài giảng, tác giả, 52 trang PDF và 81 đoạn được index. Mở tài liệu để thấy dữ liệu gốc. Đây là bài tập tra cứu tài liệu lịch sử, không phải công cụ chỉ định điều trị.
2. **Đặt câu hỏi.** Chọn “Tìm thông tin”. Câu gợi ý được điền vào ô, chưa tự gửi; đọc câu hỏi rồi bấm “Tìm câu trả lời”. UI giữ nguyên câu đã gửi để người xem biết agent đang trả lời điều gì.
3. **Theo dõi agent.** Phần “Agent đang làm gì?” hiển thị query do model chọn ở từng lượt. Khi kho dữ liệu trả kết quả thật, UI hiện nguyên văn các đoạn và số trang ngay, trước khi có câu trả lời. Không có tiến trình dựng sẵn, không hiển thị suy nghĩ nội bộ của model.
4. **Đối chiếu bằng chứng.** Nhãn “CHỈ TÌM ĐƯỢC” là đoạn retrieval tìm ra nhưng chưa nằm trong context hiện tại; “ĐÃ GỬI MODEL” là đoạn đã nằm trong context; “ĐƯỢC TRÍCH DẪN” là nguồn model chọn để trả lời. Bấm “Nguồn · trang…” trong câu trả lời để đi đến đoạn trích, sau đó mở đúng trang PDF. Không gọi một câu trả lời là đúng chỉ vì ID citation hợp lệ.
5. **Thử thiếu dữ liệu.** Chọn “Câu hỏi mới”, rồi “Thử câu thiếu dữ liệu”. Câu hỏi về giá tái khám không có trong bài giảng; agent cần từ chối thay vì suy đoán giá. Vẫn xem được những đoạn nó đã tìm.
6. **Phân biệt lỗi.** Lỗi API/quota được ghi “Lỗi xử lý”, tách khỏi “Chưa đủ bằng chứng”. Các đoạn đã lấy được vẫn giữ trên UI; không có câu trả lời thay thế giả.
7. **Nếu cần trình bày thí nghiệm.** Mở “Kết quả đánh giá”. Điểm được đọc từ file summary đã chấm, kèm ghi chú nhãn AI hỗ trợ/chờ sinh viên duyệt. Phần tùy chọn retrieval được thu gọn để người mới không phải chọn thuật toán trước khi hỏi.

Câu trả lời model có thể thay đổi giữa các lần gọi. Dùng trace lưu trong báo cáo để trình bày kết quả của lần benchmark cụ thể; không kể lại một câu trả lời khác với file trace. Lỗi trích xuất/font trong đoạn nguyên văn vẫn có thể nhìn thấy trên UI; mở PDF để đối chiếu.
