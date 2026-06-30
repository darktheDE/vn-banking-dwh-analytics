---
title: "ĐỀ XUẤT NGHIÊN CỨU KHOA HỌC"
subject: "Môn học: Phân tích Dữ liệu (Data Analysis)"
university: "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT THÀNH PHỐ HỒ CHÍ MINH"
department: "BỘ MÔN HỆ THỐNG THÔNG TIN"
project: "Hệ thống Phân tích Dữ liệu Tài chính Ngân hàng Việt Nam: Tích hợp Kho dữ liệu (Data Warehouse) và Mô hình Học máy"
group: "Nhóm thực hiện: Nhóm 2"
members:
  - "Nguyễn Đặng Quốc Anh"
  - "Trần Minh Khánh"
  - "Phạm Minh Quân"
  - "Đỗ Kiến Hưng"
date: "Thành phố Hồ Chí Minh, Năm 2026"
---

# ĐỀ XUẤT NGHIÊN CỨU

## Phân tích Dữ liệu Tài chính Ngân hàng Việt Nam: Tích hợp Data Warehouse và Mô hình Học máy

---

## 1. Abstract

Việc khai thác và phân tích dữ liệu trong lĩnh vực tài chính ngân hàng tại Việt Nam đang ngày càng trở nên cấp thiết, đặc biệt trong các bài toán đánh giá rủi ro, định giá tài sản và phân tích cấu trúc thị trường. Tuy nhiên, trong quá trình vận hành thực tế, các dữ liệu cốt lõi thường nằm rải rác ở nhiều định dạng, thiếu sự liên kết và gây ra nút thắt lớn về khả năng truy xuất cũng như tổng hợp thông tin. Điều này làm giảm đáng kể năng lực phân tích định lượng của các tổ chức.

Mặc dù đã có nhiều công cụ phân tích tài chính trên thị trường, phần lớn các hệ thống hiện tại hoặc chỉ tập trung vào mảng chứng khoán ngắn hạn, hoặc chỉ báo cáo tài chính ngân hàng một cách rời rạc. Sự thiếu vắng một hệ thống tích hợp toàn diện tạo ra một khoảng trống ứng dụng rõ ràng. Nghiên cứu này đề xuất xây dựng một luồng xử lý dữ liệu đầu cuối toàn diện, bao gồm việc thiết kế Kho dữ liệu Data Warehouse trên nền tảng Google BigQuery với kiến trúc Star Schema, kết hợp triển khai các mô hình Học máy để phân tích tập dữ liệu của 45 ngân hàng Việt Nam trong giai đoạn 2002 đến 2022 và giao dịch của các cổ phiếu ngân hàng tiêu biểu như BID, TCB, VCB, CTG. Phạm vi đánh giá tập trung vào ba khía cạnh chính: tính toàn vẹn của hệ thống lưu trữ, độ chính xác của các mô hình dự báo phân loại, và giá trị diễn giải tài chính của các cụm dữ liệu.

---

## 2. Giới thiệu

Dữ liệu khối lượng lớn đã trở thành thành phần cốt lõi trong nhiều hệ thống ra quyết định tài chính hiện đại, bao gồm hệ thống giao dịch thuật toán, đánh giá tín dụng và quản trị rủi ro. Đối với thị trường Việt Nam, nhu cầu ứng dụng Khoa học Dữ liệu đang tăng nhanh, nhưng việc triển khai thực tế vẫn gặp nhiều hạn chế do chất lượng dữ liệu đầu vào không đồng đều, chứa nhiều nhiễu và thiếu hụt giá trị. Những vấn đề này càng trở nên nghiêm trọng khi hệ thống phải xử lý đồng thời biến động giá cổ phiếu theo từng nhịp khớp lệnh trong ngày và dữ liệu chéo nền tảng của các ngân hàng.

Mặc dù đã có các phương pháp Học máy được áp dụng để dự báo giá hay phân loại rủi ro, phần lớn các nghiên cứu hiện tại vẫn tập trung vào các bộ dữ liệu đã làm sạch sẵn hoặc có quy mô nhỏ. Do đó, vẫn chưa rõ các mô hình chuỗi thời gian hay thuật toán phân cụm sẽ hoạt động như thế nào khi được tích hợp trực tiếp trên một hệ thống lưu trữ chuyên biệt cho chuẩn mực kế toán và cấu trúc giao dịch của thị trường Việt Nam.

Nghiên cứu này giải quyết khoảng trống đó bằng cách xây dựng một hệ thống tích hợp liền mạch từ khâu Kỹ thuật dữ liệu ETL đến Kỹ thuật mô hình hóa Học máy. Thay vì đề xuất một thuật toán mới, nghiên cứu tập trung vào bài toán ứng dụng thực nghiệm, định vị như một giải pháp toàn diện để khai phá tri thức từ hệ sinh thái tài chính Việt Nam.

---

## 3. Bài toán nghiên cứu

Bài toán trọng tâm của nghiên cứu là làm thế nào để chuẩn hóa, lưu trữ hiệu quả và trích xuất thành công các thông tin có giá trị cao từ các nguồn dữ liệu tài chính không đồng nhất của Việt Nam. Trong các kịch bản thực tế, việc phân tích đồng thời biến động giá cổ phiếu độ trễ thấp và các chỉ số đánh giá ngân hàng theo khung CAMELS đòi hỏi hệ thống phải đối mặt với bài toán đánh đổi giữa chi phí xử lý dữ liệu và độ phức tạp của mô hình dự báo.

Nghiên cứu đặt ra câu hỏi liệu việc chuẩn hóa dữ liệu tập trung qua mô hình Star Schema trên BigQuery có giúp cải thiện tính sẵn sàng của dữ liệu cho các mô hình Học máy hay không. Cụ thể hơn, nghiên cứu xem xét tính hiệu quả của các thuật toán K-Means trong việc gom nhóm các ngân hàng theo mức độ rủi ro, cũng như so sánh hiệu năng giữa mô hình dự báo thống kê truyền thống ARIMA và mạng học sâu LSTM khi có sự tác động của dòng tiền khối ngoại và tự doanh.

---

## 4. Mục tiêu nghiên cứu

- **Mục tiêu thứ nhất**: Xây dựng và định lượng tính toàn vẹn của Kho dữ liệu trên nền tảng Google BigQuery thông qua kiến trúc Star Schema với 5 bảng chiều Dimension và 5 bảng dữ kiện Fact.
- **Mục tiêu thứ hai**: Đo lường mức độ phân hóa và tính tương đồng của hệ thống 45 ngân hàng Việt Nam bằng các thuật toán học máy không giám sát kết hợp phương pháp giảm chiều dữ liệu phân tích thành phần chính PCA.
- **Mục tiêu thứ ba**: Đánh giá chất lượng dự báo giá cổ phiếu trong ngắn hạn (T+1 đến T+5) và khả năng phân loại rủi ro tín dụng của các thuật toán học máy có giám sát thông qua các chỉ số đo lường sai số và độ chính xác.
- **Mục tiêu thứ tư**: Phân tích diễn giải ý nghĩa tài chính từ các kết quả mô hình đầu ra, tiếp đó chuyển hóa chúng thành các chỉ báo trực quan trên một hệ thống Dashboard có tính ứng dụng thực tiễn.

---

## 5. Phạm vi nghiên cứu

Nghiên cứu này tập trung vào bộ dữ liệu lịch sử đã thu thập từ thị trường Việt Nam. Khối lượng thông tin bao gồm dữ liệu giao dịch cổ phiếu của các ngân hàng trọng tâm BID, TCB, VCB, CTG cùng bộ dữ liệu tài chính của 45 ngân hàng Việt Nam trong khoảng thời gian hai thập kỷ từ 2002 đến 2022. Phạm vi xây dựng mô hình tập trung vào các thuật toán Machine Learning như Random Forest, K-Means và mạng học sâu LSTM căn bản.

Nghiên cứu không mở rộng sang bài toán giao dịch thuật toán tự động với tần suất mili-giây, không đi sâu vào phân tích ngôn ngữ tự nhiên từ tin tức hay văn bản, và cũng không bao quát toàn bộ các mã chứng khoán trên cả ba sàn giao dịch. Trọng tâm của bài báo là đánh giá thực nghiệm các quy trình chuẩn hóa và phân tích học máy trong bối cảnh chuẩn mực tài chính Việt Nam.

---

## 6. Câu hỏi nghiên cứu

Nghiên cứu được dẫn dắt bởi bốn câu hỏi chính:

- Kiến trúc Star Schema thiết kế cho BigQuery có đảm bảo được tính nhất quán và tối ưu hóa thời gian truy vấn cho cả dữ liệu giao dịch chứng khoán hàng ngày lẫn dữ liệu báo cáo tài chính hàng năm hay không?
- Việc áp dụng kỹ thuật giảm chiều dữ liệu trên bộ các biến tài chính CAMELS có mang lại sự phân tách ranh giới rõ ràng giữa các nhóm ngân hàng nhà nước, cổ phần và ngân hàng ngoại hay không?
- Các yếu tố tài chính nào trong mô hình CAMELS đóng vai trò quyết định cấu thành mức độ quan trọng của đặc trưng trong việc phân loại rủi ro nợ xấu của ngân hàng?
- Sự khác biệt về chất lượng dự báo giữa mô hình chuỗi thời gian thống kê học và mạng nơ-ron nhân tạo biểu hiện như thế nào đối với chuỗi giá lịch sử khi kết hợp thêm tín hiệu dòng tiền khối ngoại và tự doanh?

---

## 7. Phương pháp thực hiện

Thiết kế thực nghiệm của nghiên cứu dựa trên quy trình chuẩn hóa dữ liệu vòng đời CRISP-DM. Đầu tiên, một luồng tự động hóa bao gồm khâu Trích xuất, Biến đổi và Tải dữ liệu được xây dựng bằng Python để làm sạch, xử lý giá trị khuyết thiếu và định dạng lại các trường thông tin từ các tệp Excel nguyên bản. Dữ liệu sau đó được nạp vào kho BigQuery làm cơ sở đánh giá duy nhất. Thiết lập này bảo đảm tất cả các mô hình sau đó đều truy xuất từ một nguồn sự thật đồng nhất, tránh sai lệch do phân mảnh lưu trữ.

Tập dữ liệu huấn luyện và kiểm thử được chia tách theo trục thời gian cho mảng chứng khoán và áp dụng kỹ thuật kiểm chứng chéo (hoặc chia tách theo năm) cho tập dữ liệu ngân hàng. Các biến đầu vào được đưa qua bộ lọc chuẩn hóa tỷ lệ nhằm bảo đảm không làm thay đổi bản chất của bài toán nhưng tránh được sự thiên lệch do khác biệt về đơn vị đo lường, ví dụ như sự chênh lệch độ lớn giữa tỷ lệ phần trăm và giá trị tiền tỷ VND.

Thực nghiệm Học máy được tiến hành ở hai nhánh song song. Nhánh thứ nhất sử dụng học không giám sát để tìm ra các mẫu hình ngầm ẩn trong năng lực quản trị rủi ro ngân hàng. Nhánh thứ hai sử dụng học có giám sát để dự đoán các nhãn mục tiêu cụ thể. Các thông số được ghi nhận bao gồm độ hội tụ của mô hình, thời gian huấn luyện và các chỉ số sai số. Phần phân tích định tính về ý nghĩa kinh tế học sẽ được kết hợp để hiểu rõ bản chất của các cụm phân loại.

---

## 8. Chỉ số đánh giá

Nghiên cứu sử dụng các nhóm chỉ số khác nhau tương ứng với từng bài toán đặc thù. Đối với tính toàn vẹn của nền tảng lưu trữ, mức độ thành công được đo lường thông qua số lượng bản ghi khớp trong quá trình xác thực dữ liệu và thời gian thực thi truy vấn.
Đối với các mô hình Học máy, chất lượng đầu ra được đo lường bằng các chỉ số chuyên biệt:

- **Bài toán Phân cụm**: Sử dụng Silhouette Score và Davies-Bouldin Index để đo lường độ chặt chẽ của các nhóm ngân hàng sau khi thuật toán phân loại.
- **Bài toán Phân loại rủi ro**: Sử dụng các chỉ số Accuracy, F1-Score, Recall và vùng dưới đường cong AUC-ROC để đánh giá khả năng nhận diện chính xác tổ chức tín dụng có nợ xấu cao (NPL $\ge$ 3%).
- **Bài toán Dự báo chuỗi thời gian**: Đo lường mức độ sai số của giá dự báo so với thực tế bằng MAE, RMSE và MAPE.

Phần phân tích cuối cùng nhấn mạnh vào việc đối chiếu các chỉ số toán học này với các thước đo thực tiễn trên phương diện kinh tế học, tập trung vào bài toán tối ưu rủi ro và lợi nhuận thay vì chỉ báo cáo các con số thống kê đơn thuần.

---

## 9. Đóng góp kỳ vọng

Nghiên cứu này kỳ vọng đóng góp theo ba hướng thiết thực. Thứ nhất, đây là một trong những nghiên cứu ứng dụng hiếm hoi công bố chi tiết toàn bộ quy trình từ kiến trúc hạ tầng đến phát triển thuật toán áp dụng riêng cho kết cấu dữ liệu ngân hàng và chứng khoán nội địa. Thứ hai, nghiên cứu cung cấp một giao thức đánh giá hiệu suất tổ chức tín dụng có khả năng tái lập cao, hỗ trợ đắc lực cho các cơ quan kiểm toán hoặc chuyên viên phân tích đầu tư. Thứ ba, việc triển khai thành công một nền tảng báo cáo tương tác sẽ cung cấp bằng chứng thực nghiệm có giá trị thực tiễn cho quy trình ra quyết định tài chính.

Một đóng góp bổ sung quan trọng là các phân tích đo lường mức độ ảnh hưởng của tỷ lệ nợ xấu hay tỷ lệ trích lập dự phòng lên biên lợi nhuận, từ đó tạo ra tài liệu tham chiếu hữu ích cho công tác quản trị rủi ro của hệ thống tín dụng hiện nay.

---

## 10. Kết luận

Đề xuất này trình bày một nghiên cứu ứng dụng toàn diện theo hướng xây dựng nền tảng Kỹ thuật Dữ liệu và trí tuệ nhân tạo cho thị trường tài chính Việt Nam. Nghiên cứu được xây dựng trên nhu cầu thực tế về xử lý dữ liệu quy mô lớn, khắc phục tình trạng phân mảnh và được định vị như một bản phân tích thực nghiệm có tính hệ thống cao. Bằng cách tập trung vào việc thiết kế cấu trúc dữ liệu chuẩn mực và áp dụng đa dạng các thuật toán tiên tiến, nghiên cứu hướng tới việc tạo ra một hệ thống đánh giá tài chính nghiêm ngặt, tự động và có giá trị ứng dụng mạnh mẽ. Kết quả của dự án kỳ vọng sẽ đóng góp trực tiếp vào hệ sinh thái công nghệ tài chính trong nước, tạo nền tảng vững chắc cho các hệ thống hỗ trợ ra quyết định đầu tư an toàn và hiệu quả hơn.