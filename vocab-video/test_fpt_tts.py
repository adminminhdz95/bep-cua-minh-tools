import array
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import fpt_tts


class FptTests(unittest.TestCase):
    def test_missing_key_fails_without_network(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(fpt_tts, 'CACHE', Path(tmp)), patch.dict('os.environ', {'FPT_TTS_API_KEY': ''}), patch.object(fpt_tts, 'build_opener') as network:
            with self.assertRaisesRegex(ValueError, 'Missing FPT_TTS_API_KEY'):
                fpt_tts.speech('Trẻ tuổi')
            network.assert_not_called()

    def test_request_download_and_cache_keep_key_on_api_only(self):
        opener = Mock()
        opener.open.side_effect = [io.BytesIO(json.dumps({'error': 0, 'async': 'https://file01.fpt.ai/example.mp3'}).encode()), io.BytesIO(b'fake-audio')]
        pcm = array.array('h', [1000, -1000]*2400).tobytes()
        with tempfile.TemporaryDirectory() as tmp, patch.object(fpt_tts, 'CACHE', Path(tmp)), patch.dict('os.environ', {'FPT_TTS_API_KEY': 'test-key-not-a-secret'}), patch.object(fpt_tts, 'build_opener', return_value=opener), patch.object(fpt_tts.subprocess, 'check_output', return_value=pcm):
            first = fpt_tts.speech('Trẻ tuổi')
            second = fpt_tts.speech('Trẻ tuổi')
            self.assertEqual(first, second)
            self.assertEqual(opener.open.call_count, 2)
            api_request = opener.open.call_args_list[0].args[0]
            download_request = opener.open.call_args_list[1].args[0]
            self.assertEqual(api_request.get_header('Api-key'), 'test-key-not-a-secret')
            self.assertEqual(api_request.get_header('Voice'), 'leminh')
            self.assertIsNone(download_request.get_header('Api-key'))

    def test_refuses_unexpected_audio_host(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(json.dumps({'error': 0, 'async': 'https://example.org/speech.mp3'}).encode())
        with tempfile.TemporaryDirectory() as tmp, patch.object(fpt_tts, 'CACHE', Path(tmp)), patch.dict('os.environ', {'FPT_TTS_API_KEY': 'test-key-not-a-secret'}), patch.object(fpt_tts, 'build_opener', return_value=opener):
            with self.assertRaisesRegex(ValueError, 'unexpected audio host'):
                fpt_tts.speech('Trẻ tuổi')
            self.assertEqual(opener.open.call_count, 1)


if __name__ == '__main__':
    unittest.main()
