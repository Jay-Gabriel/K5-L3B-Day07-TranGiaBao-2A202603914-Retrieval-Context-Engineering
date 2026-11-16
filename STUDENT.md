# Thông tin sinh viên

- **Họ và tên:** Trần Gia Bảo
- **Mã số sinh viên:** 2A202603914
- **Lớp:** L3B
- **Chủ đề:** Day 07 — Agentic RAG: Retrieval & Context Engineering
- **Nguồn tài liệu:** Bài giảng Chẩn đoán & Điều trị Suy tim (52 trang PDF, GS. TS. Huỳnh Văn Minh, GĐ Trung tâm Tim mạch BVĐH YD Huế)
- **Vector Store:** Qdrant Cloud (`https://qdrant.vectorium.space`, port 443, Collection: `rag_strategy_b`)
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (384 chiều)
- **LLM Agent Controller:** Google Gemini (`gemini-3.1-flash-lite`)

- **Cách chạy và demo:** [RUN.md](RUN.md) · [Kịch bản demo](docs/DEMO.md)
- **Đánh giá hiện tại:** Benchmark v3; nhãn AI hỗ trợ đọc nội dung và đối chiếu bản gốc, không tự nhận chấm bởi con người. Xem báo cáo và `starter/results/v3/selection.json`.
