"""Rebuild the four color quizzes with the user's configured ElevenLabs voice."""
import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from audio import narration_pace
from elevenlabs_tts import speech
from render import prepare, render
from verify import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = args.output or ROOT / 'output' / ('mau-sac-co-loi-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    for index, path in enumerate(sorted(Path(__file__).with_name('noi-dung').glob('*.json')), 1):
        source = json.loads(path.read_text(encoding='utf-8'))
        vi = [len(narration_pace(speech(q['narration'], language='vi'), .92)) / 48000 for q in source['questions']]
        en = [len(speech(q['word'], language='en')) / 48000 for q in source['questions']]
        source['think_seconds'] = math.ceil((max(vi) + .12 + 4) * 30) / 30
        source['reveal_seconds'] = max(2, math.ceil((max(en) + .48 + .08) * 30) / 30)
        data = prepare(source, seed=index)
        data.update(question_voice='elevenlabs', voice='elevenlabs', countdown='reference')
        video, manifest = render(data, output / path.stem)
        verify(video, manifest)
        print('VERIFIED:', video, flush=True)


if __name__ == '__main__':
    main()
