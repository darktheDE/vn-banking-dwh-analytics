⇒ mục tiêu tối thượng của mình sẽ cố gắng hiểu project nhất có thể + chỉnh cho đúng chứ hạn chế impl bổ sung thêm gì mới nữa, chỉ bổ sung mới khi những cái hiện tại đã ổn. Nội dung bên dưới bao gồm cả những tasks chỉnh sửa theo yêu cầu giảng viên và tasks nâng cấp.
Trước hết, bạn cần đọc những tài liệu liên quan đến dự án: các file .md, các file .json, các file ở /docs
Tôi cần bạn thực hiện task research lớn như sau:
b1: prompt tìm agent skill phù hợp với dự án này và tiến hành cài đặt, nhất là những skill liên quan tới data engineering, data modeling, warehouse, ....

b2: reformat, làm rõ task và xếp theo thứ tự ưu tiên: 

Feedback của thầy, anh em còn nhớ gì thì nhắn lên @All
Phản biện, làm rõ mô hình cho 4 câu hỏi
Phải so nguyên chuỗi cho câu hỏi 2
Q3: kiểm tra xem có mối quan hệ nhân quả cho llp_ratio
Huấn luyện lại theo hướng đặt thù cho câu hỏi dùng model random forest hoặc dùng model khác.
làm rõ hơn biểu đồ tương quan, chỉnh lại star schema, xem lại fact forein có phải là fact không (fact là tính toán metrics measure gì vô không phải load dataset vào không)
=> làm rõ luồng và kiến thức của project 2. Có 1 database oltp, thực hiện crawl data daily (cron job)
dùng supabase
- Tóm lại, đặt ra những câu hỏi nghiên cứu cho dataset này có hợp lý hay không, phương pháp để trả lời các câu hỏi nghiên cứu (tức chọn các models) có hợp lý hay không
- Viết lại báo cáo (docs) (cần bổ sung hình ảnh...)
- Kiểm tra feedback của các nhóm khác, => dựa trên performance trên lớp(ý kiến cá nhân chủ quan, paraphrase lại ý của thầy), quăng docs của nhóm tại thời điểm đó vào AI gen ra nhận xét . => So sánh và viết báo cáo (so sánh diff v1 vs v2, phản biện nội dung nhận xét (ý đúng -> chỉnh sửa, ý sai phản biện)) Với đồ án náy chỉ có feedback của thầy như đã liệt kê.
- Làm rõ luồng, câu hỏi đặt ra, giải quyết bằng cách nào, input, process, output của mình là gì, độ hợp lý (giải quyết vấn đề A bằng giải pháp B, thì có ai làm chưa, hiệu quả như thế nào -> bám theo, căn cứ).
- Đơn giản hóa project 02 nếu có thể, hoặc giữ nguyên và chỉnh sửa, bổ sung.
- Làm rõ hướng trình bày: docs (báo cáo như cũ, báo cáo so sánh diff v1 v2), streamlit, DEPLOY dùng streamlit.
- Kiểm tra việc cào dataset có hợp lý hay không, có cần bổ sung gì không.

b3: triển khai