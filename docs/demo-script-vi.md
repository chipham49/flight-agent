# Kịch bản demo: Cheapest Flight Finder (khoảng 3 phút)

**Cách đọc kịch bản:** **Làm** là thao tác trên màn hình. **Nói** là câu bạn đọc lên.
Giá vé thay đổi mỗi ngày. Nếu demo live, hãy đọc con số đang hiện trên màn hình.

## Chuẩn bị (5 phút trước khi trình bày)

- Mở `submission.html` trong trình duyệt.
- Mở video `demo.mp4`, hoặc mở app nếu bạn demo live.
- Nếu demo live: chạy **"LAX to New York on December 15"** một lần, trong vòng 30 phút trước khi trình bày. Lần chạy live sau đó chỉ mất khoảng 1 giây.

---

## 1. Vấn đề (0:00 – 0:20)

**Làm:** Mở phần đầu của trang `submission.html`.

**Nói:**
> "Khi tìm vé máy bay rẻ, mình phải xem nhiều trang web. Sau đó mới phát hiện còn phải trả thêm phí hành lý ký gửi.
> Vé 'rẻ nhất' nhiều khi không còn rẻ nhất khi cộng thêm một cái vali. Việc so sánh mất 30 đến 60 phút.
> Agent của em tìm **3 chuyến bay rẻ nhất**, cộng **phí hành lý** để ra **giá thật**, và giá nào cũng có **link nguồn**.
> Nó chỉ tìm kiếm. Nó **không bao giờ đặt vé hay thanh toán**."

## 2. Chạy thử (0:20 – 1:20)

**Làm:** Chạy video, hoặc trong app bấm **✈️ LAX → New York**.

**Nói** (khi agent đang tìm):
> "Em đã lưu một sở thích: **1 vali ký gửi**. Đây là **trí nhớ** của agent: lần tìm nào nó cũng dùng.
> Agent làm 7 bước theo thứ tự: kiểm tra yêu cầu có an toàn không, hiểu câu hỏi, lấy sở thích đã lưu,
> tìm giá trên web, cộng phí hành lý, xếp hạng, rồi trả lời.
> Em dùng một mô hình AI **nhỏ và rẻ** để hiểu câu hỏi, và một mô hình **mạnh hơn** để tìm trên web. Như vậy tiết kiệm chi phí."

**Nói** (khi có kết quả):
> "Đây là kết quả: ví dụ JetBlue **182 đô**, gồm giá vé 142 đô cộng **40 đô phí vali**.
> Phí vali lấy từ một thư viện nhỏ chứa quy định của các hãng bay. Phần này gọi là **RAG**: AI tra tài liệu trước khi trả lời.
> Điểm quan trọng: **AI không được tự quyết giá.** Code kiểm tra lại: một giá chỉ được giữ nếu link nằm trong kết quả tìm kiếm thật,
> đúng tuyến bay, đúng ngày và có tên hãng. Nhờ vậy AI **không thể bịa giá**."

**Làm:** Chạy lại cùng chuyến bay (trong video: phần "Cache hit").

**Nói:**
> "Lần đầu mất khoảng **30 giây** và khoảng **7 xu**. Tìm lại cùng chuyến thì lấy từ bộ nhớ đệm (**cache**):
> chỉ **1 giây** và gần như **miễn phí**."

**Làm:** Bấm **📅 Past date**, rồi **🛑 Booking request**.

**Nói:**
> "Đây là các **hàng rào an toàn (guardrails)**. Một ngày đã qua thì bị từ chối.
> Câu 'đặt vé và trả bằng thẻ của tôi' bị từ chối **ngay lập tức**, trước khi gọi AI, nên tốn **0 đồng**."

## 3. Nhật ký chạy: trace (1:20 – 2:00)

**Làm:** Cuộn tới **"How the agent worked"**, hoặc mở tab **Past runs**.

**Nói:**
> "Mỗi lần chạy đều lưu một **file trace**, giống như một cuốn nhật ký.
> Nó ghi lại từng bước, từng công cụ được gọi, và mỗi lần gọi AI: câu lệnh gửi đi, số token, thời gian và chi phí.
> Khi có lỗi, em biết ngay lỗi nằm ở bước nào. Em cũng so sánh được tốc độ và chi phí giữa các lần chạy."

## 4. Kết quả kiểm tra: evals (2:00 – 2:40)

**Làm:** Trong `submission.html`, cuộn tới **Eval results**.

**Nói:**
> "Để biết agent có tốt không, em có một **bộ 8 bài kiểm tra, chấm điểm tự động**:
> 4 lần tìm chuyến bay, và 4 tình huống khó: câu hỏi mơ hồ, ngày đã qua, yêu cầu đặt vé, và câu lừa AI.
> **Phiên bản 1 đạt 75%.** Nó quên sân bay nhà của em, và không tìm được giá Denver đi Las Vegas. Em sửa cả hai.
> Bài kiểm tra lại phát hiện một lỗi phụ: có giá không ghi tên hãng, nên không tính được phí vali.
> Em thêm một guardrail để loại các giá đó. **Phiên bản 3 đạt 100%.**
> Ngoài ra còn có **33 bài test tự động**, chạy mỗi khi có thay đổi code. Mỗi lần chạy bộ kiểm tra chỉ tốn khoảng **17 xu**."

## 5. Giới hạn và bước tiếp theo (2:40 – 3:00)

**Làm:** Cuộn tới **Limitations and next steps**.

**Nói:**
> "Em xin nói thật về giới hạn: giá lấy từ tìm kiếm web, chưa phải hệ thống đặt vé, nên đôi khi thiếu giờ bay,
> và phí hành lý dựa trên quy định năm 2025.
> Bước tiếp theo: dùng **API giá vé thật**, tìm theo **ngày linh hoạt** (cộng trừ 3 ngày), và **báo khi giá giảm**.
> Em cảm ơn mọi người đã lắng nghe."

---

## Câu hỏi có thể gặp và cách trả lời ngắn

| Câu hỏi | Trả lời |
|---|---|
| Tại sao không để AI tự làm hết? | Vì không thể tin AI một mình với con số. Em cho AI làm phần cần hiểu ngôn ngữ và tìm kiếm, còn code kiểm tra giá. Quy trình cố định cũng dễ test và dễ theo dõi hơn. |
| Làm sao biết AI không bịa giá? | Code chỉ giữ giá nếu link nằm trong kết quả tìm kiếm thật, đúng tuyến, đúng ngày và có tên hãng. Giá nào không trích nguyên văn được thì có cảnh báo "cần kiểm tra lại". |
| RAG là gì? | AI tra cứu một thư viện tài liệu trước khi trả lời. Ở đây là 11 ghi chú về phí hành lý của 10 hãng bay, và câu trả lời có ghi nguồn. |
| Chạy một lần tốn bao nhiêu? | Lần đầu khoảng 7 xu, lần lặp lại khoảng 0,02 xu. Em đặt giới hạn chi tiêu 10 đô. |
| Có bị chạy vòng lặp mãi không? | Không. Mỗi lần chạy tối đa 12 bước và 120 giây, và chỉ thử tìm lại 1 lần. |
| Có đặt vé được không? | Không, đó là cố ý để an toàn. Agent chỉ đưa link để người dùng tự đặt. |

## Từ khóa giải thích nhanh

| Từ | Nghĩa đơn giản |
|---|---|
| Agent | Chương trình AI tự làm nhiều bước để hoàn thành một việc |
| Trace | Nhật ký ghi lại mọi thứ agent đã làm trong một lần chạy |
| Guardrail | Hàng rào an toàn: chặn yêu cầu nguy hiểm hoặc kết quả sai |
| Cache | Bộ nhớ đệm: lưu kết quả 30 phút để lần sau nhanh và rẻ |
| Eval | Bài kiểm tra chấm điểm tự động để đo chất lượng agent |
| RAG | AI tra tài liệu trước khi trả lời, có ghi nguồn |
