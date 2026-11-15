# Video trắc nghiệm từ vựng Anh–Việt

Bộ dựng độc lập bằng Python/Pillow + FFmpeg. Chữ được raster hóa từ Noto Sans có tiếng Việt; nền núi, trăng và hồ tím được vẽ bằng mã. Âm báo hai nốt 880/1320 Hz được tổng hợp tại máy, không có nhạc nền hay API trả phí. Không sử dụng nội dung thư mục `videos/`.

## Dùng trong Codex

Chỉ cần nhắn: **Tạo video: young, share, enough, fourth, quarter**.

`AGENTS.md` ở gốc repo hướng dẫn Codex tự soạn đề cho danh sách bất kỳ, chọn distractor, chạy bộ dựng, xem khung hình và trả MP4. Codex cung cấp kiến thức ngôn ngữ trong cuộc trò chuyện; bản CLI offline chỉ có sẵn năm từ mẫu và không phải từ điển/dịch vụ AI độc lập cho mọi từ.

## Cài đặt và chạy trực tiếp

Yêu cầu Python 3.12+, gói OS `python3-venv`, `ffmpeg` (libx264/AAC và ffprobe), `fonts-noto-core`. Môi trường cloud này đã có Python, FFmpeg và Noto Sans. Nếu dùng máy Debian/Ubuntu khác, cài các gói OS qua package manager đáng tin cậy với quyền quản trị; script không tự dùng sudo. Dependency Python duy nhất được ghim trong `requirements.txt` và cài trong `.venv`.

```bash
cd /workspace/bep-cua-minh-tools
bash vocab-video/setup.sh
vocab-video/.venv/bin/python vocab-video/render.py --words 'young, share, enough, fourth, quarter'
```

Đổi tiêu đề và thời gian (ví dụ 8 giây/câu: 5 giây suy nghĩ + 3 giây đáp án):

```bash
vocab-video/.venv/bin/python vocab-video/render.py --input vocab-video/sample.json --title 'TỪ VỰNG A2' --think 5 --reveal 3
```

`--seed` đổi vị trí đáp án (mặc định 7, mỗi nhóm 4 câu dùng đủ A–D). `--output` đổi thư mục đích; mặc định luôn là `vocab-video/output`, bất kể thư mục chạy lệnh. Thời gian chia hết cho 1/30 giây, mỗi giai đoạn từ 0.5 đến 60 giây. Kích thước, fps và codec cố định theo yêu cầu. Mỗi lần xuất có tên riêng, không ghi đè lần trước.

## Dữ liệu

Xem `sample.json`: trường cấp cao `title`, `think_seconds`, `reveal_seconds`, `questions`. Mỗi câu có `word`, `meaning`, `pos`, `prompt` và đúng ba `distractors` cùng loại từ. Renderer xáo trộn và gán vị trí đáp án. Phần đáp án hiện nghĩa tiếng Việt của cả bốn lựa chọn; lựa chọn đúng có nền xanh. Ví dụ một câu:

```json
{
  "word": "young",
  "meaning": "trẻ tuổi",
  "pos": "adjective",
  "prompt": "Từ nào có nghĩa là “trẻ tuổi”?",
  "distractors": [
    {"word": "old", "meaning": "già, lớn tuổi", "pos": "adjective"},
    {"word": "tall", "meaning": "cao", "pos": "adjective"},
    {"word": "short", "meaning": "thấp, ngắn", "pos": "adjective"}
  ]
}
```

Validator phát hiện dữ liệu thiếu, từ/nghĩa trùng và nhãn loại từ không khớp. Codex cần rà soát nghĩa thật và tính duy nhất của đáp án; việc chỉ gắn nhãn cùng loại từ chưa chứng minh đề đúng. Từ đa nghĩa cần prompt giới hạn ngữ cảnh. Tiêu đề “A1” là mặc định thiết kế, không phải chứng nhận CEFR cho danh sách tùy ý.

## Kiểm tra

```bash
cd /workspace/bep-cua-minh-tools/vocab-video
.venv/bin/python -m unittest -v
.venv/bin/python render.py --doctor
```

Mỗi lần render tự kiểm tra MP4 thực tế bằng `verify.py`. Có thể chạy lại:

```bash
.venv/bin/python verify.py output/TEN.mp4 --manifest output/TEN/manifest.json
```

Kết quả gồm `validation.json`, 5 khung hình cho mỗi câu (đầu, giữa, cuối suy nghĩ, đầu và cuối đáp án), `contact-sheet.jpg` của 5 câu đầu, `audio-waveform.png` và `audio-preview.wav`. Kiểm tra tự động đo âm báo, không thay thế nghe đánh giá cảm nhận; kiểm tra hình tự động không thay thế đọc nội dung và xem bố cục.

Không có server phải giữ chạy. `.venv`, `jobs`, `output` được bỏ qua bởi Git; source và sample có thể lưu vào repo. Dữ liệu câu hỏi đã dùng cũng nằm trong manifest cạnh video.

## Phạm vi và tùy chọn

Bản đầu dựa trên mô tả. Sau đó đã nhận và phân tích video mẫu 34.248 giây, 720×1280 30fps; SFX tham chiếu được lưu riêng trong assets, xem assets/README.md. Giọng tiếng Anh offline không cần API. Giọng câu hỏi tiếng Việt có tùy chọn FPT.AI bên dưới.

## Thêm giọng đọc và tiếng đếm ngược

Trong Codex, nhắn: **Tạo video: young, share, enough, fourth, quarter; có giọng đọc tiếng Anh và tiếng tích đếm ngược.**

Chạy trực tiếp:

```bash
vocab-video/.venv/bin/python vocab-video/render.py --words 'young, share, enough, fourth, quarter' --voice slt --countdown tick
```

- `--voice slt`: giọng nữ tiếng Anh offline từ FFmpeg/Flite, đọc từ đúng sau âm báo 0.48 giây. `--voice kal`: giọng nam. `--voice none`: tắt.
- `--countdown tick`: tiếng tích hai tần số 1600/2400 Hz tự tổng hợp mỗi giây chờ; không phải nhạc lấy từ nguồn bên ngoài. `--countdown none`: tắt.
- FFmpeg của môi trường này đã tích hợp Flite và các giọng; không cần cài Python dependency mới, không gửi văn bản ra ngoài và không tính phí. FFmpeg ở máy khác cần được build với libflite để dùng giọng đọc.
- Giọng offline khá máy. Giọng tiếng Việt tự nhiên có adapter FPT.AI tùy chọn bên dưới; chưa kiểm thử trực tiếp dịch vụ do thiếu khóa. Muốn thêm dịch vụ ngoài cần chọn nhà cung cấp và nêu rõ chi phí/cấu hình trước.
- Nếu từ dài không vừa 2 giây đáp án, lệnh báo lỗi, không cắt lời. Thêm `--reveal 4` để dành 4 giây cho phần đáp án.

## Giọng Lê Minh và tích tắc theo video mẫu

Người dùng đã chọn **nam miền Bắc, FPT.AI — Lê Minh**. Chế độ tùy chọn:

```bash
vocab-video/.venv/bin/python vocab-video/render.py --input vocab-video/sample.json --question-voice fpt-leminh --countdown reference --voice slt
```

FPT nhận nội dung `prompt` (hoặc trường `narration` của từng câu nếu có) và có thể tính phí theo hạn mức tài khoản. Đặt khóa trong secret `FPT_TTS_API_KEY` ở Environment settings, không gửi khóa trong chat. Bật truy cập mạng FPT; cấu hình dự thảo đã khai báo `api.fpt.ai`, `docs.fpt.ai`, `*.fpt.ai`. Header chứa khóa chỉ gửi tới API, không gửi khi tải audio. Tệp đã tổng hợp được cache trong `.cache/fpt/` theo nội dung, giọng, tốc độ, định dạng để tránh gọi lại. Không thêm dependency Python mới.

Lời đọc bắt đầu lúc hiện câu hỏi. Tích tắc theo mẫu bắt đầu sau lời đọc 0.12 giây và kết thúc trước thời điểm hiện đáp án. Giữ mặc định 6 giây/câu: lời đọc nằm trong 4 giây suy nghĩ, đáp án 2 giây. Nếu muốn đủ 4 giây đếm ngược sau lời đọc, phải tăng thời lượng câu. Bộ dựng báo lỗi nếu lời đọc không vừa, không cắt âm thầm.

SFX `reference` được trích từ đoạn 1.177–1.643 giây của video người dùng gửi, khoảng 4.3 nhịp/giây. Đây là đoạn hiệu ứng ngắn được lặp, không phải toàn bộ âm thanh/nhạc của mẫu. Có thể nghe đối chiếu bản MP4 thử được trả trong cuộc trò chuyện.

**Trạng thái:** unit tests mô phỏng yêu cầu API, cache và bảo vệ khóa đã qua. TTS FPT thật chưa được xác minh vì chưa có khóa và cấu hình mạng mới chưa áp dụng; lệnh đã được thử và dừng rõ ràng với thông báo thiếu khóa. Không coi adapter là đã hoạt động thực tế cho đến khi tạo và kiểm tra được lời Việt qua dịch vụ. Tài liệu nhà cung cấp: https://docs.fpt.ai/docs/en/speech/api/text-to-speech.html (truy cập từ máy hiện tại bị mạng chặn trong lần kiểm tra này).

## ElevenLabs (tùy chọn mới)

Đặt secret `ELEVENLABS_API_KEY` và biến `ELEVENLABS_VOICE_ID` trong Environment settings, cho phép `api.elevenlabs.io`. Giữ API key ngoài source/chat. Người dùng đã chọn dịch vụ này để tạo câu hỏi tiếng Việt tự nhiên; chọn và nghe thử giọng nam miền Bắc trong tài khoản, không clone giọng từ mẫu.

```bash
vocab-video/.venv/bin/python vocab-video/elevenlabs_tts.py --list-voices
vocab-video/.venv/bin/python vocab-video/render.py --words 'young, share, enough, fourth, quarter' --question-voice elevenlabs --countdown reference --voice slt
```

Mặc định dùng `eleven_v3`, ngôn ngữ `vi`; đổi `ELEVENLABS_MODEL_ID` nếu cần mô hình khác hỗ trợ tiếng Việt và có trong tài khoản. Quyền API, hạn mức miễn phí, các giọng được phép dùng và quyền thương mại phụ thuộc tài khoản. Không tự động mua/nâng gói hoặc đổi giọng. API dùng header `xi-api-key`, không theo redirect chứa khóa; audio được decode sang mono PCM 48kHz và cache `.cache/elevenlabs/` theo giọng/mô hình/nội dung. Không cần dependency cài mới.

Câu hỏi được đọc trong 4 giây suy nghĩ, tiếp theo là tích tắc; đáp án vẫn hiện ở giây 4–6. Câu quá dài gây lỗi thay vì bị cắt; có thể rút ngắn `narration` hoặc tăng `--think` với thông báo thời lượng rõ ràng.

**Trạng thái lần tích hợp:** 18 unit tests đã qua. Xác thực thật trả 401 `invalid_api_key`; Voice ID chưa có trong máy. Đã thử lệnh dựng và chưa xuất được video với giọng ElevenLabs. Cần sửa cấu hình rồi kiểm tra lại bằng một kết nối mới và video thật, không coi kết quả mô phỏng là đã kiểm chứng giọng tự nhiên.

Để dùng cùng giọng ElevenLabs cho cả hai ngôn ngữ, thay `--voice slt` bằng `--voice elevenlabs`. `ELEVENLABS_VOICE_ID` được giữ nguyên; câu hỏi dùng ngôn ngữ `vi`, đáp án dùng `en`.

Logo tròn **Tiếng Anhh Cùng Minh** tự xuất hiện ở góc trên bên trái mọi video, kích thước 180×180. Asset: `assets/logo-tieng-anhh-cung-minh.png` (PNG nền trong suốt). Có thể tạo lại chữ/viền bằng `.venv/bin/python create_logo.py`; ảnh chân dung gốc của thiết kế được giữ tại `assets/logo-portrait-base.png`.
