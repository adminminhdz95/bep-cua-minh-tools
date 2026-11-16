"""Offline English speech and original countdown sounds, all at 48 kHz."""
import array
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import wave

SR = 48000


def narration_pace(samples, rate=1.0):
    """Slow narration locally without changing pitch or regenerating TTS."""
    if rate == 1.0:
        return samples
    if not .7 <= rate <= 1.2:
        raise ValueError('narration_rate must be between 0.7 and 1.2')
    pcm = array.array('h', samples)
    if sys.byteorder != 'little':
        pcm.byteswap()
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-f', 's16le', '-ar', str(SR),
        '-ac', '1', '-i', 'pipe:0', '-af', f'atempo={rate}', '-f', 's16le', 'pipe:1'], input=pcm.tobytes())
    result = array.array('h', raw)
    if sys.byteorder != 'little':
        result.byteswap()
    return result


def tone(duration, frequencies, volume):
    return array.array('h', (
        round(32767 * volume * min(1, i/SR/.008) * (1-i/SR/duration)**2 *
              sum(math.sin(2*math.pi*hz*i/SR) for hz in frequencies)/len(frequencies))
        for i in range(round(SR*duration))))


def speech(word, voice):
    # Text is passed through a UTF-8 file, never interpolated into a filter or shell.
    with tempfile.TemporaryDirectory(prefix='vocab-tts-') as tmp:
        path = Path(tmp) / 'word.txt'
        path.write_text(word, encoding='utf-8')
        raw = subprocess.check_output([
            'ffmpeg', '-v', 'error', '-nostdin', '-f', 'lavfi', '-i',
            f'flite=textfile={path}:voice={voice}', '-ac', '1', '-ar', str(SR),
            '-af', 'volume=0.85', '-f', 's16le', 'pipe:1'])
    result = array.array('h', raw)
    if sys.byteorder != 'little':
        result.byteswap()
    if not result or max(abs(s) for s in result) < 100:
        raise ValueError(f'TTS produced no audible speech for {word!r}')
    return result


def write_audio(path, data, think_frames, reveal_frames):
    voice = data.get('voice', 'none')
    countdown = data.get('countdown', 'none')
    think_samples = think_frames * SR // 30
    total_samples = (think_frames + reveal_frames) * SR // 30
    cue = tone(.42, (880, 1320), .30)
    tick = tone(.09, (1600, 2400), .13)
    events = []
    with wave.open(str(path), 'wb') as out:
        out.setparams((1, 2, SR, 0, 'NONE', 'not compressed'))
        for i, q in enumerate(data['questions']):
            track = array.array('h', [0]) * total_samples

            def place(start, sound, kind):
                if start+len(sound) > len(track):
                    raise ValueError(f'Speech for {q["word"]!r} does not fit. Increase --reveal (try --reveal 4). No speech was truncated.')
                # AAC can overshoot PCM peaks; retain headroom without clipping
                # individual samples or changing the speech timing.
                ceiling = round(.65 * 32767)
                peak = max((abs(s) for s in sound), default=0)
                if peak > ceiling:
                    gain = ceiling / peak
                    sound = array.array('h', (round(s * gain) for s in sound))
                track[start:start+len(sound)] = sound
                events.append({'question': i+1, 'kind': kind,
                               'seconds': (i*total_samples+start)/SR,
                               'duration': len(sound)/SR})

            countdown_start = 0
            question_voice = data.get('question_voice', 'none')
            if question_voice in ('fpt-leminh', 'elevenlabs'):
                if question_voice == 'elevenlabs':
                    from elevenlabs_tts import speech as vietnamese_speech
                else:
                    from fpt_tts import speech as vietnamese_speech
                narrated = narration_pace(vietnamese_speech(q.get('narration', q['prompt'])), data.get('narration_rate', 1.0))
                if len(narrated) > think_samples-round(.25*SR):
                    raise ValueError(f'Question {i+1} narration is too long. Shorten the question or increase --think; narration is never truncated.')
                place(0, narrated, 'narration')
                countdown_start = len(narrated)+round(.12*SR)
            if countdown == 'reference':
                with wave.open(str(Path(__file__).parent/'assets'/'reference-tick-pair.wav')) as source:
                    if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (1, 2, SR):
                        raise ValueError('Invalid reference countdown asset')
                    loop = array.array('h', source.readframes(source.getnframes()))
                    if sys.byteorder != 'little':
                        loop.byteswap()
                available = think_samples-round(.06*SR)-countdown_start
                if available > 0:
                    sound = (loop * math.ceil(available/len(loop)))[:available]
                    # Fade out the final 10ms to avoid a cut at the answer boundary.
                    fade = min(480, len(sound))
                    for k in range(fade):
                        sound[-fade+k] = round(sound[-fade+k]*(1-k/fade))
                    place(countdown_start, sound, 'reference_countdown')
            if countdown == 'tick':
                for start in range(countdown_start, think_samples, SR):
                    # Keep a silent gap before the answer cue, also for fractional durations.
                    if start+len(tick) <= think_samples-int(.04*SR):
                        place(start, tick, 'tick')
            place(think_samples, cue, 'answer')
            if voice != 'none':
                if voice == 'elevenlabs':
                    from elevenlabs_tts import speech as multilingual_speech
                    spoken = multilingual_speech(q['word'], language='en')
                else:
                    spoken = speech(q['word'], voice)
                place(think_samples+round(.48*SR), spoken, 'speech')
            if sys.byteorder != 'little':
                track.byteswap()
            out.writeframesraw(track.tobytes())
    data['audio_events'] = events
