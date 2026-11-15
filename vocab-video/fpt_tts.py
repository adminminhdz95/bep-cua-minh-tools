"""Optional FPT.AI Vietnamese TTS. Requests incur provider usage; cache locally."""
import array
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import build_opener, HTTPRedirectHandler, Request

API = 'https://api.fpt.ai/hmi/tts/v5'
CACHE = Path(__file__).resolve().parent / '.cache' / 'fpt'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def speech(text, voice='leminh'):
    cache_key = hashlib.sha256(json.dumps([text, voice, 0, 'mp3'], ensure_ascii=False).encode()).hexdigest()
    cached = CACHE / (cache_key+'.pcm')
    if cached.is_file():
        raw = cached.read_bytes()
    else:
        key = os.environ.get('FPT_TTS_API_KEY')
        if not key:
            raise ValueError('Missing FPT_TTS_API_KEY. Add it securely in Environment settings; do not paste it in chat. Use --question-voice none for offline rendering.')
        opener = build_opener(NoRedirect())
        request = Request(API, data=text.encode('utf-8'), method='POST', headers={
            'api-key': key, 'voice': voice, 'speed': '0', 'format': 'mp3',
            'Content-Type': 'text/plain; charset=utf-8'})
        try:
            with opener.open(request, timeout=30) as response:
                result = json.loads(response.read(65536))
        except (HTTPError, URLError, ValueError) as exc:
            # Do not expose request headers, credentials or raw server messages.
            status = getattr(exc, 'code', 'network/response error')
            raise ValueError(f'FPT synthesis failed ({status}). Check provider access, key and quota in settings.') from None
        if result.get('error') != 0 or not result.get('async'):
            raise ValueError('FPT rejected synthesis. Check provider key, quota and supported voice; no audio returned.')
        url = result['async']
        parsed = urlparse(url)
        host = parsed.hostname or ''
        if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port not in (None, 443) or not host.endswith('.fpt.ai'):
            raise ValueError('FPT returned an unexpected audio host. Review download destination before allowing it.')
        audio = None
        # FPT provides an asynchronous URL. Retry only the not-yet-created file.
        for attempt in range(12):
            try:
                with opener.open(Request(url), timeout=20) as response:
                    audio = response.read(8*1024*1024+1)
                if audio:
                    break
            except HTTPError as exc:
                if exc.code != 404:
                    raise ValueError(f'FPT audio download failed ({exc.code}); check network access.') from None
            except URLError:
                raise ValueError('FPT audio download could not reach the provider. Check network settings.') from None
            if attempt < 11:
                time.sleep(2)
        if not audio or len(audio) > 8*1024*1024:
            raise ValueError('FPT audio was not ready or exceeded the download size limit. Retry later.')
        with tempfile.TemporaryDirectory(prefix='vocab-fpt-') as tmp:
            path = Path(tmp)/'speech.mp3'
            path.write_bytes(audio)
            try:
                raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path),
                                               '-ac', '1', '-ar', '48000', '-af', 'alimiter=limit=0.8:level=false',
                                               '-f', 's16le', 'pipe:1'], stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                raise ValueError('FPT returned audio that FFmpeg could not decode.') from None
        if not raw or len(raw) % 2:
            raise ValueError('FPT returned empty/invalid PCM audio')
        CACHE.mkdir(parents=True, exist_ok=True)
        # Atomic cache replacement; no partial artifact survives a failed write.
        with tempfile.NamedTemporaryFile(dir=CACHE, delete=False) as temp:
            temp.write(raw)
            temporary = Path(temp.name)
        temporary.replace(cached)
    samples = array.array('h', raw)
    if sys.byteorder != 'little':
        samples.byteswap()
    if not samples or max(abs(s) for s in samples) < 100:
        raise ValueError('FPT produced no audible narration')
    return samples
