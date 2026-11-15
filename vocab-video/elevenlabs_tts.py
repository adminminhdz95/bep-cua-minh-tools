"""Optional ElevenLabs Vietnamese narration using the user's key and voice."""
import argparse
import array
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import build_opener, HTTPRedirectHandler, Request

API = 'https://api.elevenlabs.io'
CACHE = Path(__file__).resolve().parent / '.cache' / 'elevenlabs'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(path, payload=None):
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key:
        raise ValueError('Missing ELEVENLABS_API_KEY. Add the key securely in Environment settings, never in chat.')
    headers = {'xi-api-key': key, 'Accept': 'audio/mpeg' if payload else 'application/json'}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    req = Request(API+path, data=json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None,
                  headers=headers, method='POST' if payload is not None else 'GET')
    try:
        with build_opener(NoRedirect()).open(req, timeout=60) as response:
            result = response.read(8*1024*1024+1)
    except HTTPError as exc:
        # Only expose the provider's bounded machine-readable status, never headers or raw error text.
        status = ''
        try:
            detail = json.loads(exc.read(4096)).get('detail', {})
            candidate = detail.get('status', '') if isinstance(detail, dict) else ''
            if isinstance(candidate, str) and re.fullmatch(r'[a-z_]{1,64}', candidate):
                status = f' {candidate}'
        except (ValueError, AttributeError):
            pass
        raise ValueError(f'ElevenLabs HTTP {exc.code}{status}. Check the saved key, endpoint permissions and account quota.') from None
    except URLError:
        raise ValueError('Cannot reach api.elevenlabs.io. Check the environment network settings.') from None
    if not result or len(result) > 8*1024*1024:
        raise ValueError('ElevenLabs returned empty or oversized content')
    return result


def list_voices():
    return json.loads(request('/v1/voices')).get('voices', [])


def speech(text, language="vi"):
    if language not in ("vi", "en"):
        raise ValueError("Unsupported speech language")
    voice = os.environ.get('ELEVENLABS_VOICE_ID', '').strip()
    model = os.environ.get('ELEVENLABS_MODEL_ID', 'eleven_v3').strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', voice):
        raise ValueError('Missing/invalid ELEVENLABS_VOICE_ID. Set the chosen voice ID in Environment settings. No voice is selected automatically.')
    payload = {'text': text, 'model_id': model, 'language_code': language,
               'voice_settings': {'stability': .5, 'similarity_boost': .75}}
    cache_key = hashlib.sha256(json.dumps([voice, payload], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    cached = CACHE / (cache_key+'.pcm')
    if cached.is_file():
        raw = cached.read_bytes()
    else:
        audio = request('/v1/text-to-speech/'+quote(voice, safe='')+'?output_format=mp3_44100_128', payload)
        with tempfile.TemporaryDirectory(prefix='vocab-elevenlabs-') as tmp:
            path = Path(tmp)/'speech.mp3'
            path.write_bytes(audio)
            try:
                raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path),
                    '-ac', '1', '-ar', '48000', '-af', 'alimiter=limit=0.8:level=false', '-f', 's16le', 'pipe:1'], stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                raise ValueError('Cannot decode ElevenLabs audio; no speech was cached.') from None
        if not raw or len(raw) % 2:
            raise ValueError('Invalid/empty ElevenLabs PCM audio')
        samples = array.array('h', raw)
        if not samples or max(abs(s) for s in samples) < 100:
            raise ValueError('ElevenLabs produced silent narration')
        CACHE.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=CACHE, delete=False) as temp:
            temp.write(raw)
            temporary = Path(temp.name)
        temporary.replace(cached)
    samples = array.array('h', raw)
    if sys.byteorder != 'little':
        samples.byteswap()
    if not samples or max(abs(s) for s in samples) < 100:
        raise ValueError('ElevenLabs produced no audible narration')
    return samples


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list-voices', action='store_true', required=True)
    parser.parse_args()
    try:
        for voice in list_voices():
            print(json.dumps({k: voice.get(k) for k in ('voice_id', 'name', 'labels')}, ensure_ascii=False))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Error: {exc}\n')
