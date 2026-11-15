import array
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

import elevenlabs_tts as tts


class ElevenLabsTests(unittest.TestCase):
    def test_missing_voice_does_not_send_text(self):
        with patch.dict('os.environ', {'ELEVENLABS_VOICE_ID': ''}), patch.object(tts, 'request') as network:
            with self.assertRaisesRegex(ValueError, 'ELEVENLABS_VOICE_ID'):
                tts.speech('Trẻ tuổi')
            network.assert_not_called()

    def test_request_uses_xi_api_key_and_utf8(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(b'audio-data')
        with patch.dict('os.environ', {'ELEVENLABS_API_KEY': 'unit-test-key'}), patch.object(tts, 'build_opener', return_value=opener):
            tts.request('/v1/text-to-speech/test', {'text': 'Trẻ tuổi'})
            req = opener.open.call_args.args[0]
            self.assertEqual(req.get_header('Xi-api-key'), 'unit-test-key')
            self.assertEqual(json.loads(req.data)['text'], 'Trẻ tuổi')

    def test_invalid_key_error_does_not_expose_response_message(self):
        opener = Mock()
        opener.open.side_effect = HTTPError('https://api.elevenlabs.io', 401, 'Unauthorized', {}, io.BytesIO(json.dumps({'detail': {'status': 'invalid_api_key', 'message': 'must-not-be-printed'}}).encode()))
        with patch.dict('os.environ', {'ELEVENLABS_API_KEY': 'unit-test-key'}), patch.object(tts, 'build_opener', return_value=opener):
            with self.assertRaisesRegex(ValueError, '401 invalid_api_key') as context:
                tts.request('/v1/voices')
            self.assertNotIn('must-not-be-printed', str(context.exception))
            self.assertNotIn('unit-test-key', str(context.exception))

    def test_successful_synthesis_is_cached_by_voice_model_and_text(self):
        pcm = array.array('h', [900, -900]*2400).tobytes()
        with tempfile.TemporaryDirectory() as tmp, patch.object(tts, 'CACHE', Path(tmp)), patch.dict('os.environ', {'ELEVENLABS_VOICE_ID': 'test_voice', 'ELEVENLABS_MODEL_ID': 'eleven_v3'}), patch.object(tts, 'request', return_value=b'mp3') as network, patch.object(tts.subprocess, 'check_output', return_value=pcm):
            first = tts.speech('Trẻ tuổi')
            second = tts.speech('Trẻ tuổi')
            self.assertEqual(first, second)
            self.assertEqual(network.call_count, 1)
            self.assertEqual(network.call_args.args[1]['language_code'], 'vi')
            self.assertEqual(network.call_args.args[1]['model_id'], 'eleven_v3')

    def test_english_uses_same_voice_but_separate_language_cache(self):
        pcm = array.array('h', [900, -900]*2400).tobytes()
        with tempfile.TemporaryDirectory() as tmp, patch.object(tts, 'CACHE', Path(tmp)), patch.dict('os.environ', {'ELEVENLABS_VOICE_ID': 'same_voice'}), patch.object(tts, 'request', return_value=b'mp3') as network, patch.object(tts.subprocess, 'check_output', return_value=pcm):
            tts.speech('young', language='en')
            tts.speech('young', language='vi')
            tts.speech('young', language='en')
            self.assertEqual(network.call_count, 2)
            self.assertEqual([c.args[1]['language_code'] for c in network.call_args_list], ['en', 'vi'])
            self.assertTrue(all('/same_voice?' in c.args[0] for c in network.call_args_list))

    def test_audio_timeline_dispatches_elevenlabs(self):
        from audio import write_audio, SR
        data = {'question_voice': 'elevenlabs', 'countdown': 'reference',
                'questions': [{'word': 'young', 'prompt': 'Từ nào có nghĩa là trẻ tuổi?'}]}
        with tempfile.TemporaryDirectory() as tmp, patch.object(tts, 'speech', return_value=array.array('h', [1200])*SR) as speak:
            write_audio(Path(tmp)/'audio.wav', data, 120, 60)
            speak.assert_called_once_with('Từ nào có nghĩa là trẻ tuổi?')
            events = data['audio_events']
            self.assertEqual([e['kind'] for e in events], ['narration', 'reference_countdown', 'answer'])
            self.assertAlmostEqual(events[1]['seconds'], 1.12)
            self.assertEqual(events[-1]['seconds'], 4)


if __name__ == '__main__':
    unittest.main()
