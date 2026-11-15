#!/usr/bin/env python3
"""Offline Vietnamese vocabulary cards -> H.264/AAC MP4. No API calls."""
import argparse
import copy
from datetime import datetime
from functools import lru_cache
import json
import math
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import uuid

from PIL import Image, ImageDraw, ImageFont
from audio import write_audio

ROOT = Path(__file__).resolve().parent
W, H, FPS, SR = 1080, 1920, 30, 48000
FONT = Path('/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf')
REGULAR = FONT.with_name('NotoSans-Regular.ttf')
GREEN = (63, 236, 157)
WHITE = (250, 247, 255)


def normalize(value):
    return unicodedata.normalize('NFC', value).strip().casefold()


def text(value, label, limit=160):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'{label}: expected nonempty text, at most {limit} characters')
    if any(unicodedata.category(c).startswith('C') and c != '\n' for c in value):
        raise ValueError(f'{label}: control characters are unsupported')
    return unicodedata.normalize('NFC', value.strip())


def frames(seconds, label):
    if isinstance(seconds, bool) or not isinstance(seconds, (float, int)) or not math.isfinite(seconds):
        raise ValueError(f'{label}: expected finite seconds')
    if not 0.5 <= seconds <= 60 or abs(seconds * FPS - round(seconds * FPS)) > 1e-6:
        raise ValueError(f'{label}: must be 0.5–60 seconds in steps of 1/30 second')
    return round(seconds * FPS)


def prepare(source, seed=7):
    data = copy.deepcopy(source)
    data['title'] = text(data.get('title', 'TỪ VỰNG A1'), 'title', 60)
    data['think_seconds'] = data.get('think_seconds', 4)
    data['reveal_seconds'] = data.get('reveal_seconds', 2)
    frames(data['think_seconds'], 'think_seconds')
    frames(data['reveal_seconds'], 'reveal_seconds')
    questions = data.get('questions')
    if not isinstance(questions, list) or not 1 <= len(questions) <= 200:
        raise ValueError('questions: expected 1–200 questions')
    data['questions'] = questions = [copy.deepcopy(q) for q in questions]
    rng = random.Random(seed)
    # Every complete group of four uses A, B, C, D exactly once.
    slots = []
    for _ in range(math.ceil(len(questions) / 4)):
        batch = list(range(4))
        rng.shuffle(batch)
        slots.extend(batch)
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            raise ValueError(f'question {i + 1}: expected object')
        for key in ('word', 'meaning', 'pos', 'prompt'):
            q[key] = text(q.get(key), f'question {i + 1}.{key}', 160 if key == 'prompt' else 65)
        ds = q.get('distractors')
        if not isinstance(ds, list) or len(ds) != 3 or any(not isinstance(d, dict) for d in ds):
            raise ValueError(f'question {i + 1}: exactly three distractors required')
        options = [{k: q[k] for k in ('word', 'meaning', 'pos')}]
        for d in ds:
            options.append({k: text(d.get(k), f'distractor.{k}', 65) for k in ('word', 'meaning', 'pos')})
        if len({normalize(o['word']) for o in options}) != 4:
            raise ValueError(f'question {i + 1}: duplicate English options')
        if len({normalize(o['meaning']) for o in options}) != 4:
            raise ValueError(f'question {i + 1}: duplicate Vietnamese meanings')
        if any(normalize(o['pos']) != normalize(q['pos']) for o in options):
            raise ValueError(f'question {i + 1}: all options must share a part of speech')
        correct = options.pop(0)
        rng.shuffle(options)
        q['answer'] = slots[i]
        options.insert(q['answer'], correct)
        q['options'] = options
    data.update(width=W, height=H, fps=FPS, seed=seed)
    return data


@lru_cache(maxsize=80)
def font(size, bold=True):
    return ImageFont.truetype(str(FONT if bold else REGULAR), size)


def wrap(draw, value, f, width):
    result = []
    for paragraph in value.split('\n'):
        line = ''
        for word in paragraph.split():
            candidate = f'{line} {word}'.strip()
            if draw.textlength(candidate, font=f) > width and line:
                result.append(line)
                line = word
            else:
                line = candidate
        result.append(line)
    return result


def fit(draw, value, box, size=60, minimum=26, fill=WHITE, bold=True, align='center'):
    x0, y0, x1, y1 = box
    for s in range(size, minimum - 1, -1):
        f = font(s, bold)
        lines = wrap(draw, value, f, x1 - x0)
        advance = round(s * 1.42)
        if len(lines) * advance <= y1 - y0 and all(draw.textlength(line, font=f) <= x1 - x0 for line in lines):
            y = y0 + (y1 - y0 - len(lines) * advance) / 2
            for line in lines:
                x = (x0 + x1 - draw.textlength(line, font=f)) / 2 if align == 'center' else x0
                draw.text((x, y), line, font=f, fill=fill, anchor='lt', stroke_width=0)
                y += advance
            return
    raise ValueError(f'Text does not fit the card. Shorten it: {value!r}')


def landscape():
    im = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line((0, y, W, y), fill=(int(43 + 43 * t), int(20 + 25 * t), int(84 + 50 * t)))
    # Original vector scenery: lavender moon, mountain silhouettes, lake, pines.
    d.ellipse((660, 180, 970, 490), fill='#c4a4e0')
    d.polygon([(0, 700), (150, 380), (310, 610), (500, 350), (770, 690), (940, 420), (1080, 610), (1080, 1920), (0, 1920)], fill='#68428d')
    d.polygon([(0, 900), (210, 570), (460, 840), (680, 550), (1080, 940), (1080, 1920), (0, 1920)], fill='#472b70')
    d.rectangle((0, 1370, W, H), fill='#392153')
    rng = random.Random(43)
    for y in range(1390, 1920, 19):
        x = rng.randrange(120, 750)
        d.line((x, y, min(1080, x + rng.randrange(80, 300)), y), fill='#614071', width=2)
    for x, y, scale in [(15, 1290, 1.2), (1000, 1380, 1.4), (65, 1800, 1.7), (960, 1840, 1.8)]:
        d.rectangle((x-4, y, x+4, y+100*scale), fill='#21152f')
        for offset in range(3):
            yy = y + offset * 40 * scale
            d.polygon([(x, yy-160*scale), (x-65*scale, yy+25*scale), (x+65*scale, yy+25*scale)], fill='#21152f')
    return im


def card(background, data, q, index, reveal):
    im = background.copy().convert('RGBA')
    layer = Image.new('RGBA', im.size)
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((58, 95, 1022, 310), 40, fill=(24, 12, 54, 220), outline=(194, 151, 238, 255), width=2)
    fit(d, data['title'], (88, 105, 992, 220), size=76, minimum=32, fill='#f5de87')
    fit(d, f'ANH – VIỆT   •   {index+1:02d} / {len(data["questions"]):02d}', (100, 225, 980, 290), size=30, bold=False)
    d.rounded_rectangle((58, 370, 1022, 690), 36, fill=(24, 12, 54, 220))
    fit(d, q['prompt'], (95, 395, 985, 660), size=58, minimum=30)
    for j, option in enumerate(q['options']):
        y = 755 + j * 186
        correct = reveal and j == q['answer']
        fill = (*GREEN, 255) if correct else (30, 16, 63, 235)
        ink = '#102e25' if correct else WHITE
        d.rounded_rectangle((80, y, 1000, y+158), 28, fill=fill, outline=(*GREEN, 255) if correct else (171, 135, 207, 255), width=3)
        d.ellipse((102, y+35, 182, y+115), fill=(20, 46, 37, 255) if correct else (104, 68, 143, 255))
        fit(d, 'ABCD'[j], (104, y+38, 180, y+110), size=41)
        fit(d, option['word'], (215, y+8, 956, y+91 if reveal else y+150), size=62, minimum=30, fill=ink, align='left')
        if reveal:
            fit(d, option['meaning'], (215, y+86, 956, y+150), size=33, minimum=24, fill=ink, bold=False, align='left')
    fit(d, 'ĐÁP ÁN ĐÚNG' if reveal else 'BẠN CHỌN ĐÁP ÁN NÀO?', (80, 1535, 1000, 1610), size=33, fill=GREEN if reveal else '#eddfed')
    fit(d, 'Mỗi ngày một chút • Tiếng Anh dễ nhớ', (70, 1750, 1010, 1820), size=28, bold=False, fill='#d5c3e6')
    composed = Image.alpha_composite(im, layer)
    logo_path = ROOT / 'assets' / 'logo-tieng-anhh-cung-minh.png'
    if logo_path.is_file():
        with Image.open(logo_path) as logo:
            badge = logo.convert('RGBA').resize((180, 180), Image.Resampling.LANCZOS)
            composed.alpha_composite(badge, (24, 24))
    return composed.convert('RGB')


def add_timer(im, remaining, reveal=False):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((90, 1650, 990, 1672), 11, fill='#25133e')
    if remaining > 0:
        d.rounded_rectangle((90, 1650, 90+round(900*remaining), 1672), 11, fill=GREEN if reveal else '#f5de87')


def doctor():
    for exe in ('ffmpeg', 'ffprobe'):
        if not shutil.which(exe):
            raise ValueError(f'Missing {exe}')
    for path in (FONT, REGULAR):
        if not path.is_file():
            raise ValueError(f'Missing font {path}; install fonts-noto-core')
    encoders = subprocess.check_output(['ffmpeg', '-hide_banner', '-encoders'], text=True)
    if 'libx264' not in encoders:
        raise ValueError('FFmpeg needs libx264')
    if ' aac ' not in encoders:
        raise ValueError('FFmpeg needs AAC encoder')
    font(50).getmask('TỪ VỰNG • trẻ tuổi • một phần tư')
    print('OK: FFmpeg H.264/AAC, Noto Sans Vietnamese, Pillow')


def render(data, output):
    output.mkdir(parents=True, exist_ok=True)
    stem = 'vocab-' + datetime.now().astimezone().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]
    final = output / (stem + '.mp4')
    review = output / stem
    review.mkdir()
    think = frames(data['think_seconds'], 'think_seconds')
    reveal = frames(data['reveal_seconds'], 'reveal_seconds')
    bg = landscape()
    with tempfile.TemporaryDirectory(prefix='vocab-') as tmp:
        tmp = Path(tmp)
        audio = tmp / 'answer.wav'
        write_audio(audio, data, think, reveal)
        movie = tmp / 'video.mp4'
        command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
                   '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', 'pipe:0',
                   '-i', str(audio), '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast',
                   '-crf', '20', '-threads', '2', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                   '-movflags', '+faststart', '-shortest', str(movie)]
        with (review / 'ffmpeg.log').open('w') as log:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log)
            try:
                for i, q in enumerate(data['questions']):
                    thought = card(bg, data, q, i, False)
                    answer = card(bg, data, q, i, True)
                    for f in range(think + reveal):
                        is_answer = f >= think
                        frame = (answer if is_answer else thought).copy()
                        add_timer(frame, 0 if is_answer else (think-f)/think, is_answer)
                        process.stdin.write(frame.tobytes())
                    print(f'Rendered {i+1}/{len(data["questions"])}: {q["word"]}', flush=True)
                process.stdin.close()
                if process.wait() != 0:
                    raise RuntimeError(f'FFmpeg failed; see {review / "ffmpeg.log"}')
            except BaseException:
                process.stdin.close()
                process.wait()
                raise
        shutil.move(str(movie), final)
    data['video_file'] = final.name
    data['duration_seconds'] = len(data['questions']) * (think + reveal) / FPS
    manifest = review / 'manifest.json'
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'MP4: {final}\nManifest: {manifest}', flush=True)
    return final, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--doctor', action='store_true')
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument('--input', type=Path, help='Codex-authored quiz JSON (see sample.json)')
    inputs.add_argument('--words', help='Comma-separated words from sample.json; arbitrary words need --input')
    parser.add_argument('--title')
    parser.add_argument('--think', type=float, help='Thinking seconds, default 4')
    parser.add_argument('--reveal', type=float, help='Answer seconds, default 2')
    parser.add_argument('--voice', choices=('none', 'slt', 'kal', 'elevenlabs'), default='none', help='English answers: offline slt/kal or same configured ElevenLabs voice')
    parser.add_argument('--countdown', choices=('none', 'tick', 'reference'), default='none', help='Once-per-second tick or fast tick-tock sampled from the supplied reference')
    parser.add_argument('--question-voice', choices=('none', 'fpt-leminh', 'elevenlabs'), default='none', help='Optional Vietnamese narration: FPT or ElevenLabs; requires provider credentials')
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--output', type=Path, default=ROOT / 'output')
    args = parser.parse_args()
    try:
        doctor()
        if args.doctor:
            return
        source = json.loads((args.input or ROOT / 'sample.json').read_text(encoding='utf-8'))
        if args.words is not None:
            words = [normalize(w) for w in args.words.split(',')]
            bank = {normalize(q['word']): q for q in source['questions']}
            missing = [w for w in words if w not in bank]
            if missing:
                raise ValueError(f'Words need Codex-authored JSON via --input: {", ".join(missing)}. See AGENTS.md.')
            source['questions'] = [copy.deepcopy(bank[w]) for w in words]
        for arg, key in [(args.title, 'title'), (args.think, 'think_seconds'), (args.reveal, 'reveal_seconds')]:
            if arg is not None:
                source[key] = arg
        data = prepare(source, args.seed)
        data.update(voice=args.voice, countdown=args.countdown, question_voice=args.question_voice)
        video, manifest = render(data, args.output.resolve())
        subprocess.run([sys.executable, str(ROOT / 'verify.py'), str(video), '--manifest', str(manifest)], check=True)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
