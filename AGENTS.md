# Quy trình tạo video từ vựng Anh–Việt

Khi người dùng nhập `Tạo video: young, share, enough, fourth, quarter` (hoặc danh sách từ khác), tự thực hiện toàn bộ quy trình dưới đây và trả đường dẫn MP4. Không yêu cầu người dùng tự viết JSON hay chạy lệnh.

## Phạm vi

- Bộ công cụ độc lập nằm ở `vocab-video/`. Không dùng hay sửa `videos/`, ZIP, phụ đề hoặc nội dung cũ của repo để làm video từ vựng.
- Mỗi cloud task đã được cô lập. Dùng checkout hiện có; không tạo Git worktree trừ khi người dùng yêu cầu.
- Đọc `vocab-video/README.md`. Nếu thiếu môi trường Python, chạy `bash vocab-video/setup.sh` từ gốc repo. Không cài vào Python toàn cục, không đổi dependency của ứng dụng khác.
- Không cần server, API key hay dịch vụ trả phí. Không lấy nhạc/âm thanh có bản quyền từ video tham chiếu. Không dùng AI tạo ảnh để vẽ chữ.

## Soạn nội dung tự động trong Codex

1. Tách các từ theo dấu phẩy, giữ đúng thứ tự. Mặc định tiêu đề `TỪ VỰNG A1`, 4 giây suy nghĩ và 2 giây đáp án. Áp dụng thay đổi người dùng yêu cầu mà không hỏi lại các mặc định này.
2. Codex tự soạn JSON UTF-8 theo `vocab-video/sample.json`, lưu tên riêng tại `vocab-video/jobs/` (tạo thư mục nếu thiếu). Không chỉ hỗ trợ 5 từ mẫu: với từ bất kỳ, tự viết đầy đủ `word`, `meaning`, `pos`, `prompt`, và 3 `distractors`, mỗi distractor có `word`, `meaning`, `pos`.
3. Chọn một nghĩa và loại từ cụ thể cho mỗi từ. Câu hỏi bằng tiếng Việt, có thể thêm câu tiếng Anh ngắn để xác định nghĩa/loại từ. `fourth` là số thứ tự, không phải Wednesday; `quarter` trong mẫu là danh từ “một phần tư”; `enough` trong `We have ___ food` là determiner. Tránh tự khẳng định mọi từ do người dùng cung cấp đều thuộc CEFR A1; tiêu đề là nhãn người dùng có thể đổi.
4. Ba đáp án nhiễu phải cùng loại từ theo ngữ cảnh, có nghĩa khác biệt và không đồng nghĩa/chồng lấn nghĩa với đáp án. Đảm bảo chỉ đúng một lựa chọn. Rà soát ngữ nghĩa thủ công: validator chỉ kiểm tra cấu trúc, nhãn loại từ, trùng từ/nghĩa, không thể chứng minh tính đúng về ngôn ngữ. Dùng distractor đơn giản, tránh câu hỏi văn phạm có nhiều cách điền đúng nếu đề không chỉ rõ nghĩa cần chọn.
5. Giữ prompt ngắn, tối đa 160 ký tự; từ/nghĩa tối đa 65 ký tự. Bộ dựng tự phân bổ đáp án A–D cân bằng (mỗi nhóm 4 dùng đủ 4 vị trí). Không tự gắn nhãn A–D vào JSON.
6. Không cần tra cứu API để soạn nội dung. Nếu một từ thực sự không rõ nghĩa (lỗi chính tả/tên riêng), chỉ hỏi về từ đó sau khi đã xử lý các từ rõ nghĩa.

## Dựng và kiểm tra bắt buộc

Từ gốc repo:

```bash
vocab-video/.venv/bin/python vocab-video/render.py --input vocab-video/jobs/TEN-RIENG.json
```

Hoặc với 5 từ đã có trong dữ liệu mẫu:

```bash
vocab-video/.venv/bin/python vocab-video/render.py --words 'young, share, enough, fourth, quarter'
```

- Đổi tiêu đề với `--title 'TỪ VỰNG A2'`; đổi tổng thời gian mỗi câu bằng `--think 5 --reveal 3` (8 giây/câu); đổi danh sách trong JSON hoặc `--words` nếu các từ đã có trong mẫu. Dùng `--input` cho mọi danh sách mới. Không lặng lẽ bỏ từ không có sẵn.
- Renderer xuất MP4 H.264/AAC 1080×1920, 30 fps vào `vocab-video/output/`, tên có thời gian và mã ngẫu nhiên tránh ghi đè. Cùng tên cơ sở có thư mục manifest, khung hình, contact sheet và kết quả kiểm tra.
- `render.py` tự gọi `verify.py`: decode cả video, xác minh metadata/số frame/thời lượng, lấy khung hình trước/đúng thời điểm hiện đáp án, kiểm tra màu xanh/thanh thời gian, kiểm tra âm báo đúng mốc và không clipping. Nếu lỗi, sửa nguyên nhân và chạy lại; không báo hoàn tất khi kiểm tra thất bại.
- Mở `contact-sheet.jpg` và ít nhất một `frame-*.png` kích thước đầy đủ bằng công cụ xem ảnh. Kiểm tra tiếng Việt, không tràn chữ, chỉ một đáp án xanh và nghĩa cả bốn lựa chọn xuất hiện sau thời gian suy nghĩ. Xem `audio-waveform.png`/`validation.json`; có `audio-preview.wav` để nghe đối chiếu nếu có công cụ phát âm thanh. Không nói “đã nghe” nếu chỉ kiểm tra tín hiệu.
- Trả link MP4 thật cùng thời lượng, số câu và kết quả kiểm tra ngắn gọn. Dùng đường dẫn tuyệt đối hoặc artifact link mà môi trường hỗ trợ; không tạo link localhost. Không cần push/commit để giao video nếu không được yêu cầu.
- Nếu người dùng cung cấp video mẫu, xem khung hình và metadata trước khi chỉnh thiết kế. Nếu tệp không truy cập được, nói rõ và dựng theo mô tả, không khẳng định khớp mẫu đã xem.

## Giọng đọc và đếm ngược

Khi người dùng yêu cầu “có giọng đọc và tiếng đếm ngược”, thêm `--voice slt --countdown tick` vào lệnh render. `slt` là giọng nữ tiếng Anh offline bằng FFmpeg/Flite, `kal` là giọng nam. Giọng đọc từ đúng bắt đầu 0.48 giây sau lúc hiện đáp án; tiếng tích nhẹ phát mỗi giây suy nghĩ. Không đọc đáp án trước khi hết giờ. Mặc định các tùy chọn mới đều tắt để giữ khả năng xuất bản không lời. Không cần mạng, API key hay chi phí; giọng offline có chất lượng máy, không hứa giọng người thật. Nếu phát âm dài hơn thời gian đáp án, bộ dựng báo lỗi thay vì cắt âm; tăng `--reveal` (ví dụ 4 giây) và thông báo thời lượng mới. Kiểm tra `extra_audio` trong validation.json cho tiếng tích và giọng đọc. Giọng tiếng Việt có tùy chọn FPT.AI như mục dưới; chỉ dùng khi khóa và mạng đã sẵn sàng.

 Nếu thêm TTS ngoài, giải thích nhà cung cấp, chi phí, quyền gửi nội dung và cấu hình tùy chọn trước khi dùng; không biến API trả phí thành điều kiện của bản cơ bản.

## Mẫu tham chiếu và giọng nam miền Bắc đã chọn

Người dùng đã cung cấp video mẫu và chọn FPT.AI, giọng Lê Minh (nam miền Bắc) cho câu hỏi. Với yêu cầu có giọng đọc tự nhiên và tiếng tích tắc theo mẫu, dùng:

```bash
vocab-video/.venv/bin/python vocab-video/render.py --input vocab-video/jobs/TEN-RIENG.json --question-voice fpt-leminh --countdown reference --voice slt
```

- `--countdown reference` dùng đoạn SFX tích tắc ngắn từ mẫu trong `vocab-video/assets/reference-tick-pair.wav`, khoảng 4.3 nhịp/giây; không dùng nhạc nền hay sao chép giọng người trong mẫu.
- `--question-voice fpt-leminh` gửi prompt tiếng Việt đến FPT.AI, cần secret `FPT_TTS_API_KEY` và quyền mạng tới `api.fpt.ai` cùng các máy chủ tải âm thanh `*.fpt.ai`. Người dùng đã chọn nhà cung cấp này và đã được thông báo về việc gửi câu hỏi/khả năng phát sinh phí. Giữ khóa trong Environment settings, không hỏi giá trị khóa trong chat. Cache `.cache/fpt` tránh tạo lại cùng nội dung/giọng/tốc độ.
- Mặc định vẫn 6 giây/câu: đọc câu hỏi lúc bắt đầu, tiếng tích tắc bắt đầu 0.12 giây sau khi đọc xong và dừng trước giây 4; đáp án hiện giây 4–6. Giọng đọc nằm trong 4 giây chờ. Nếu người dùng muốn đủ 4 giây đếm ngược SAU khi đọc, cần tăng thời lượng; không mô tả mặc định là 4 giây chờ độc lập sau lời đọc.
- Có thể thêm trường `narration` là câu hỏi thuần tiếng Việt, ngắn gọn, vào từng câu JSON nếu prompt có câu ví dụ tiếng Anh. Không đọc từ đáp án trước khi hết giờ. Không cắt âm thanh để ép thời gian; rút gọn câu hỏi hoặc tăng `--think` nếu không vừa.
- Chế độ offline vẫn hoạt động bằng `--question-voice none`; không tự thay giọng Lê Minh bằng giọng máy rồi báo là đã hoàn thành yêu cầu.
- Tại thời điểm tích hợp, 13 unit tests (gồm mô phỏng giao thức FPT) đã qua; video 5 câu với SFX tham chiếu đã qua kiểm tra. TTS FPT thật CHƯA được kiểm chứng do chưa có khóa và mạng hiện hành chặn FPT. Sau khi người dùng lưu cấu hình, kiểm tra lại hiện diện khóa (không in giá trị), gọi thử một câu ngắn và kiểm tra MP4 có lời Việt trước khi báo tích hợp đã hoạt động.

## ElevenLabs — lựa chọn mới nhất của người dùng

Người dùng hiện muốn ElevenLabs thay cho FPT để đọc câu hỏi tiếng Việt; vẫn thích giọng nam miền Bắc và tiếng tích tắc tham chiếu. Không tự chọn voice khác hoặc hứa giọng đúng miền khi chưa nghe thử. Dùng:

```bash
vocab-video/.venv/bin/python vocab-video/render.py --input vocab-video/jobs/TEN-RIENG.json --question-voice elevenlabs --countdown reference --voice slt
```

- Secret `ELEVENLABS_API_KEY` chỉ gửi trong header `xi-api-key` tới `https://api.elevenlabs.io`. Biến không bí mật `ELEVENLABS_VOICE_ID` là ID giọng người dùng chọn. Mô hình mặc định `eleven_v3` có thể đổi bằng `ELEVENLABS_MODEL_ID` nếu tài khoản dùng mô hình khác hỗ trợ tiếng Việt; phải kiểm tra hỗ trợ thực tế khi xác thực được. Không cam kết miễn phí hay quyền thương mại ngoài điều khoản tài khoản.
- Nội dung câu hỏi (`narration` nếu có, nếu không `prompt`) được gửi tới ElevenLabs; không tạo bản sao/clone giọng người trong video mẫu. Kết quả cache trong `.cache/elevenlabs` theo giọng, mô hình và nội dung để tránh tổng hợp trùng. Tiếng tích tắc, nhịp và thời lượng dùng cùng quy tắc của bộ dựng hiện tại.
- Kiểm tra khóa/giọng bằng `vocab-video/.venv/bin/python vocab-video/elevenlabs_tts.py --list-voices` (chỉ xuất tên, ID, labels). Không in khóa hay dump môi trường. Sau khi cấu hình thay đổi, thử lại kết nối mới rồi chạy video thật và kiểm tra hình/âm thanh.
- Kết quả tích hợp hiện tại: 18 unit tests đã qua (API ElevenLabs mô phỏng). Máy có secret được gắn và domain được phép nhưng GET /v1/voices và /v1/models trả HTTP 401 `invalid_api_key`; `ELEVENLABS_VOICE_ID` chưa có. Lệnh render ElevenLabs thật đã thử và dừng rõ ràng do thiếu Voice ID. Chưa có video nào tạo thành công bằng ElevenLabs. Cần người dùng sửa khóa và thêm Voice ID trong Environment settings; không yêu cầu gửi khóa trong chat, không áp dụng lại cấu hình FPT hoặc xuất bản tự động.

## Cùng giọng ElevenLabs cho cả tiếng Việt và tiếng Anh

Yêu cầu mới nhất: dùng cùng `ELEVENLABS_VOICE_ID` để đọc câu hỏi tiếng Việt và đáp án tiếng Anh. Thêm `--question-voice elevenlabs --voice elevenlabs --countdown reference`. Bộ dựng gửi ngôn ngữ `vi` cho câu hỏi và `en` cho từ đáp án, cache riêng theo ngôn ngữ; không đổi giọng hay dùng Flite khi người dùng yêu cầu cùng giọng. Chỉ đọc đáp án sau khi hiện đáp án. Nếu lời đọc không vừa, tăng thời gian đáp án và báo rõ, không cắt âm.

## Logo thương hiệu mặc định

Mọi video từ vựng mới phải có logo tròn `vocab-video/assets/logo-tieng-anhh-cung-minh.png`, dùng ảnh chân dung người dùng cung cấp và chữ chính xác **Tiếng Anhh Cùng Minh** (giữ hai chữ h theo yêu cầu). Renderer tự đặt logo 180×180 tại (24,24), góc trên bên trái, trong cả giai đoạn suy nghĩ và đáp án. Không bỏ logo hoặc sửa chính tả nếu chưa được yêu cầu. Chữ logo được typeset bằng Noto Sans trong `create_logo.py`. Kiểm tra logo không che nội dung khi đổi tiêu đề/bố cục; không cần gọi lại công cụ tạo ảnh cho mỗi video.

## Trạng thái mới nhất đã xác minh

ElevenLabs hiện đã tổng hợp thành công cả tiếng Việt và tiếng Anh bằng cùng giọng đã cấu hình. Bộ 20 video tình yêu / 100 câu đã hoàn thành và qua kiểm tra. Các ghi chú 401/missing Voice ID phía trên là lịch sử, không phải trạng thái hiện tại. Tài khoản từng hết quota; nếu lỗi quota xuất hiện lại, giữ cache và tiếp tục sau khi người dùng bổ sung hạn mức, không đổi giọng âm thầm. Bản phân phối nằm tại `vocab-video/published/tinh-yeu/`, có 20 MP4, ZIP, danh sách và JSON câu hỏi. Không cần API key để tải/xem các video đã xuất; chỉ cần để tổng hợp giọng mới.

## Bộ từ vựng buổi sáng: đọc hết câu hỏi rõ ràng

Với yêu cầu đọc đầy đủ, đặt `narration` bằng toàn bộ `prompt` tiếng Việt, không chỉ đọc nghĩa. Dùng cùng giọng ElevenLabs cho hai ngôn ngữ. Có thể đặt `narration_rate: 0.92` để làm chậm lời Việt tại máy bằng FFmpeg atempo, giữ cao độ; không cần gọi lại TTS nếu có cache. Đặt `countdown_after_narration: true` để thanh thời gian bắt đầu giảm sau lời đọc. Tính `think_seconds` từ độ dài lời Việt đã điều chỉnh + 0.12 giây nghỉ + ít nhất 4 giây đếm ngược; làm tròn lên bội 1/30 giây. Tính `reveal_seconds` đủ cho từ/cụm tiếng Anh sau âm báo. Không cắt lời hay ép toàn bộ câu còn 6 giây khi không đủ thời gian. Người dùng đã yêu cầu hoàn thành bộ buổi sáng và đưa lên GitHub, không cần hỏi lại cho bộ này.

## Đáp án nhiễu gần nghĩa

Người dùng yêu cầu các lựa chọn sai gần nghĩa và cùng nhóm với đáp án đúng, tránh nghĩa lệch quá xa. Chọn cùng loại từ và cùng nhóm ngữ nghĩa; ví dụ câu hỏi về người thân phải dùng các vai trò trong gia đình. Vẫn bảo đảm chỉ một đáp án đúng: phân biệt rõ cháu của ông bà với cháu gọi mình bằng cô/chú, quan hệ huyết thống với quan hệ bên vợ/chồng. Với cụm động từ, dùng các hoạt động gần nhau trong cùng bối cảnh. Phân bố đáp án đúng giữa A–D và kiểm tra nghĩa của cả bốn lựa chọn.

## Yêu cầu đọc rõ hai ngôn ngữ

Người dùng nhấn mạnh đọc đúng tiếng Việt và tiếng Anh. Giữ giọng đã chọn, mã ngôn ngữ `vi` cho toàn bộ câu hỏi và `en` cho đáp án. Khi một thuật ngữ Việt ngắn dễ nghe nhầm, có thể viết câu hỏi mô tả chức năng/ngữ cảnh bằng tiếng Việt tự nhiên; vẫn giữ từ và nghĩa chuẩn trong đáp án. Đặt `narration` bằng câu hỏi hiển thị. Kiểm tra lại MP4 sau mọi lần sửa lời đọc. Nếu dùng ASR, giữ bản chép thực tế và ghi rõ các khác biệt chính tả từ ghép/từ mượn; không tự xem ASR là chứng nhận dấu thanh, trọng âm hoặc giọng bản ngữ, không tuyên bố đã nghe khi không có công cụ nghe.

## Chủ đề màu sắc

Khi người dùng yêu cầu lựa chọn mang màu tương ứng, đặt `option_colors` ở cấp JSON gốc: ánh xạ từ tiếng Anh sang mã `#RRGGBB` cho mọi đáp án đúng và nhiễu. Bộ dựng giữ màu này ở cả hai giai đoạn, tự chọn chữ đen/trắng theo độ tương phản; đáp án đúng hiện dấu ✓, viền trắng và tên đáp án, không đổi thành nền xanh. Các chủ đề không có `option_colors` giữ mẫu cũ. Kiểm tra màu trong MP4 sau nén, kể cả màu trắng/đen/vàng và trường hợp green là lựa chọn sai. Màu vàng kim và bạc dùng màu phẳng đại diện trên màn hình.

Bộ `vocab-video/published/mau-sac` gồm 20 màu/4 video xem trước không lời do ElevenLabs trả 401 invalid_api_key ngày 19/11/2026. Sau khi người dùng cập nhật secret trong cài đặt, dùng JSON `vocab-video/published/mau-sac/noi-dung` để dựng lại bằng cùng giọng ElevenLabs cho cả hai ngôn ngữ; tính thời lượng từ audio như quy trình trên. Không coi các bản xem trước là video đã có lời.
