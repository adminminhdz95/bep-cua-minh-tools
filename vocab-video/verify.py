#!/usr/bin/env python3
"""Verify the encoded video, card boundaries, timer and audible answer cues."""
import argparse
import array
import json
import math
from pathlib import Path
import subprocess
import sys
import wave

from PIL import Image, ImageDraw, ImageFont


def check(condition, message):
    if not condition:
        raise ValueError(message)


def green(pixel):
    r, g, b = pixel[:3]
    return g > 170 and g > r * 1.5 and g > b * 1.15


def rms(samples):
    return math.sqrt(sum((s / 32768)**2 for s in samples) / max(1, len(samples)))


def verify(video, manifest):
    data = json.loads(manifest.read_text(encoding='utf-8'))
    folder = manifest.parent
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)
    ]))
    v = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    a = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
    check((v['width'], v['height'], v['r_frame_rate'], v['pix_fmt'], v['codec_name']) ==
          (1080, 1920, '30/1', 'yuv420p', 'h264'), 'Video format mismatch')
    check(a['codec_name'] == 'aac' and int(a['sample_rate']) == 48000, 'Audio format mismatch')
    think = round(data['think_seconds'] * 30)
    reveal = round(data['reveal_seconds'] * 30)
    span = think + reveal
    total = len(data['questions']) * span
    check(int(v['nb_frames']) == total, f'Expected {total} frames, found {v.get("nb_frames")}')
    check(abs(float(probe['format']['duration']) - total/30) < .05, 'Duration mismatch')
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-nostdin', '-i', str(video), '-f', 'null', '-'], check=True)
    indices = sorted({i*span+j for i in range(len(data['questions'])) for j in (0, think//2, think-1, think, span-1)})
    # Read actual compressed frames, not the source PNGs.
    expression = '+'.join(f'eq(n,{n})' for n in indices)
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-i', str(video), '-vf', f'select={expression.replace(",", chr(92)+",")}',
                    '-fps_mode', 'vfr', str(folder / 'frame-%04d.png')], check=True)
    images = {n: folder / f'frame-{i+1:04d}.png' for i, n in enumerate(indices)}
    sheet = Image.new('RGB', (360*min(5, len(data['questions'])), 680*2), '#170d2e')
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf', 19)
    for i, q in enumerate(data['questions']):
        for offset in (0, think//2, think-1, think, span-1):
            with Image.open(images[i*span+offset]) as im:
                for j in range(4):
                    is_green = green(im.getpixel((975, 755+j*186+70)))
                    check(is_green == (offset >= think and j == q['answer']), f'Wrong answer state, question {i+1}, frame {offset}, option {j}')
                if offset == 0:
                    p = im.getpixel((900, 1660))
                    check(p[0] > 170 and p[1] > 150, 'Timer missing at question start')
                if offset == think-1:
                    p = im.getpixel((900, 1660))
                    check(p[0] < 100, 'Timer did not shrink')
        if i < 5:
            for row, offset in enumerate((think//2, think)):
                with Image.open(images[i*span+offset]) as im:
                    sheet.paste(im.resize((360, 640)), (i*360, row*680+40))
                d.text((i*360+10, row*680+8), f'{i+1}. {q["word"]} | {"answer" if row else "think"}', fill='white', font=f)
    sheet.save(folder / 'contact-sheet.jpg', quality=94)
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(video), '-vn', '-ac', '1', '-ar', '48000', '-f', 's16le', 'pipe:1'])
    samples = array.array('h', raw)
    if sys.byteorder != 'little':
        samples.byteswap()
    check(len(samples) >= round(total/30*48000), 'Audio truncated')
    peak = max(abs(s) for s in samples)/32768
    check(.05 < peak < .95, f'Audio is silent or clipping: {peak}')
    cues = []
    for i in range(len(data['questions'])):
        onset = (i*span+think)/30
        start = round(onset*48000)
        quiet = rms(samples[start-1920:start-720])
        sound = rms(samples[start+960:start+9600])
        tail = rms(samples[start+24000:start+int(data['reveal_seconds']*48000)-480])
        check(quiet < .002 and (data.get('voice', 'none') != 'none' or tail < .001) and .01 < sound < .4, f'Bad audio cue at {onset}s: {quiet}, {sound}, {tail}')
        # Check both intended tones survived encoding (frequency-specific energy).
        segment = samples[start+960:start+5760]
        powers = []
        for hz in (880, 1320):
            re = sum(s/32768 * math.cos(2*math.pi*hz*n/48000) for n, s in enumerate(segment))
            im = sum(s/32768 * math.sin(2*math.pi*hz*n/48000) for n, s in enumerate(segment))
            power = 2 * math.hypot(re, im) / len(segment)
            check(power > .02, f'Missing {hz}Hz tone at {onset}s')
            powers.append(round(power, 5))
        cues.append({'seconds': onset, 'rms': round(sound, 5), 'quiet_rms': round(quiet, 7), 'tone_amplitudes': powers})
    extra_audio = []
    for event in data.get('audio_events', []):
        if event['kind'] == 'answer':
            continue
        start = round(event['seconds']*48000)
        end = start+round(event['duration']*48000)
        level = rms(samples[start:end])
        check(level > .002, f"Missing {event['kind']} at {event['seconds']}s")
        if event['kind'] == 'tick':
            # Verify silence between ticks, not merely any audio energy.
            answer_start = round(((event['question']-1)*span+think)/30*48000)
            gap = samples[end+960:min(start+43200, answer_start-960)]
            check(rms(gap) < .001, f"Unexpected sound between ticks at {event['seconds']}s")
        extra_audio.append({**event, 'rms': round(level, 5)})
    preview_start = 0 if extra_audio else max(0, round((think/30-.4)*48000))
    with wave.open(str(folder / 'audio-preview.wav'), 'wb') as out:
        out.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
        preview_length = round(span/30*48000) if extra_audio else 48000
        section = samples[preview_start:preview_start+preview_length]
        if sys.byteorder != 'little':
            section.byteswap()
        out.writeframes(section.tobytes())
    waveform = Image.new('RGB', (1500, 240), '#21132e')
    wd = ImageDraw.Draw(waveform)
    for x in range(1500):
        chunk = samples[x*len(samples)//1500:(x+1)*len(samples)//1500]
        amplitude = max((abs(s) for s in chunk), default=0)/32768
        wd.line((x, 120-amplitude*330, x, 120+amplitude*330), fill='#40ec9d', width=1)
    waveform.save(folder / 'audio-waveform.png')
    result = {'status': 'passed', 'video': str(video), 'size': [1080, 1920], 'fps': 30,
              'frames': total, 'duration_seconds': total/30, 'sampled_frames': indices,
              'answer_positions': ['ABCD'[q['answer']] for q in data['questions']],
              'audio_peak': round(peak, 5), 'audio_cues': cues, 'extra_audio': extra_audio,
              'note': 'Automated signal and decoded-frame checks. Inspect contact-sheet.jpg and full frames for language/layout.'}
    (folder / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('video', type=Path)
    p.add_argument('--manifest', type=Path, required=True)
    args = p.parse_args()
    verify(args.video.resolve(), args.manifest.resolve())
