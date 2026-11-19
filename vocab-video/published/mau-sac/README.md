# Màu sắc — 20 từ, 4 video xem trước

**Bản xem trước KHÔNG LỜI.** Có tiếng tích tắc và âm báo. Giọng ElevenLabs chưa tạo được vì API trả HTTP 401 `invalid_api_key`. Cần cập nhật `ELEVENLABS_API_KEY` trong cài đặt môi trường; không gửi khóa vào chat.

Mỗi video 5 câu, 30 giây, 1080×1920/30fps. Mỗi câu gồm 4 giây suy nghĩ và 2 giây đáp án. Có logo. Mỗi lựa chọn mang màu tương ứng với từ tiếng Anh, giữ màu lúc hiện đáp án; dấu ✓, viền trắng và tên đáp án chỉ lựa chọn đúng.

[Tải cả 4 video xem trước — ZIP](https://github.com/adminminhdz95/bep-cua-minh-tools/raw/refs/heads/main/vocab-video/published/mau-sac/4-video-mau-sac-khong-loi.zip) · [20 từ và bảng màu](20-tu-mau-sac.md)

| Video | Từ vựng | MP4 không lời |
|---:|---|---|
| 1 | red, blue, yellow, green, orange | [Tải](https://github.com/adminminhdz95/bep-cua-minh-tools/raw/refs/heads/main/vocab-video/published/mau-sac/01-mau-sac-phan-1-khong-loi.mp4) |
| 2 | purple, pink, brown, black, white | [Tải](https://github.com/adminminhdz95/bep-cua-minh-tools/raw/refs/heads/main/vocab-video/published/mau-sac/02-mau-sac-phan-2-khong-loi.mp4) |
| 3 | gray, beige, navy, maroon, olive | [Tải](https://github.com/adminminhdz95/bep-cua-minh-tools/raw/refs/heads/main/vocab-video/published/mau-sac/03-mau-sac-phan-3-khong-loi.mp4) |
| 4 | turquoise, cyan, magenta, gold, silver | [Tải](https://github.com/adminminhdz95/bep-cua-minh-tools/raw/refs/heads/main/vocab-video/published/mau-sac/04-mau-sac-phan-4-khong-loi.mp4) |

![Khung hình bản xem trước](xem-truoc-01.jpg)

## Kiểm tra

24 unit tests đã qua. Cả 4 MP4 đã giải mã và kiểm tra màu, mốc đáp án, thanh thời gian, âm báo và mức âm. Đã xem ảnh tổng hợp và ảnh toàn kích thước của từng video; không tuyên bố nghe trực tiếp. [Báo cáo](validation.json).

## Hoàn tất giọng đọc sau khi cập nhật khóa

Giữ nguyên Voice ID đã chọn. Từ gốc repo chạy:

```bash
vocab-video/.venv/bin/python vocab-video/published/mau-sac/render_with_voice.py
```

Script gửi câu hỏi Việt với ngôn ngữ `vi` và đáp án Anh với `en` tới ElevenLabs, giữ cùng giọng. Tận dụng cache, tính thời lượng để lời Việt xong rồi đủ 4 giây đếm ngược, không cắt lời; tự kiểm tra MP4. Dừng rõ ràng nếu khóa/quota không hợp lệ. Các bản có lời cần được xem khung hình và rà soát giọng đọc trước khi giao.

Vàng kim và bạc là màu phẳng đại diện; không mô phỏng phản chiếu kim loại.
