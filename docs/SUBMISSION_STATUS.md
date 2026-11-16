# Trạng thái bài làm

## Phần bắt buộc đã hoàn tất về code và bằng chứng đánh giá

- Corpus Day 6: 52 trang PDF, 81 chunk, Qdrant/embedding thật tương thích.
- V3: 24 câu, chia 17 dev và 7 test mới trước lựa chọn cấu hình; v2 lỗi quota giữ nguyên trong lịch sử.
- So sánh 5 cấu hình retrieval, gồm TF-IDF, dense và Hybrid; chạy/chấm 3 cấu hình agent trên dev (51 case, không lỗi provider).
- Khóa TF-IDF top-6/budget6000 từ dev; chạy baseline và cấu hình chọn trên cùng toàn bộ test mới (14 case, không lỗi provider).
- Cấu hình chọn: **5/5 câu có đáp án đúng và đủ, 6/6 citation hỗ trợ, 2/2 câu thiếu bằng chứng từ chối đúng**. Baseline: 1/5 câu có đáp án đúng, 2/2 abstention đúng. Không gọi điểm test nhỏ là bảo đảm đúng mọi câu hỏi.
- Nhãn hoàn tất bằng AI hỗ trợ đọc từng answer/context/citation với bản PDF, có lý do và nguồn gốc. Không tự nhận sinh viên/con người đã chấm. Phần cơ bản không yêu cầu chữ ký sinh viên cho nhãn.
- CER giữ evidence đã gửi ngay cả khi answer lỗi; semantic refusals được chấm riêng với runtime status. Usage/chi phí ước tính có nguồn pricing, không gọi ước tính là hóa đơn.
- Code review độc lập không còn blocker code được phát hiện. Unit/HTTP tests, UI fixtures desktop/mobile và live demo được kiểm tra riêng với benchmark.

## Nguồn/quyền tài liệu và phần tùy chọn

Đã xác minh tác giả, trang gốc, hash và kiểm tra nguồn lịch sử. Dữ liệu là bản người dùng cung cấp từ Day 6 và yêu cầu dùng/nộp; điều này không tự chứng minh giấy phép mở từ tác giả. Không tự ghi CC/public-domain hoặc “giảng viên đã cho phép” khi chưa có thông tin. Xem [DATA_NOTICE.md](../DATA_NOTICE.md). Câu hỏi liệu tài liệu được lớp/giảng viên cung cấp/cho phép hay tự tải từ web đang chờ người dùng xác nhận; đây là thông tin thực không thể tự bịa.

**Bonus chưa thực hiện.** Phần bắt buộc tối đa 85 điểm. Bonus 15 điểm yêu cầu tài liệu≥100 trang, xử lý/index multimodal và benchmark nâng cao riêng đạt ≥90%; không cộng bonus dựa trên test 7 câu cơ bản. Không bảo đảm điểm chấm100/100 hoặc tự nhận đã nộp trên hệ thống lớp khi chỉ mới push GitHub.

Repo cá nhân: https://github.com/Jay-Gabriel/K5-L3B-Day07-TranGiaBao-2A202603914-Retrieval-Context-Engineering. Repo public để người chấm truy cập. Chủ repo nộp link theo hướng dẫn lớp; `.env`, cache và lịch sử cục bộ không được đưa vào Git.

[Cách chạy](../RUN.md) · [Kịch bản demo](DEMO.md) · [Báo cáo](../report/individual/2A202603914_TranGiaBao.md)
