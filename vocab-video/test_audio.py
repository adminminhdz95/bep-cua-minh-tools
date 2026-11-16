import array
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

from audio import SR, write_audio, narration_pace, tone


class AudioTests(unittest.TestCase):
    def test_slower_narration_keeps_full_signal_and_increases_duration(self):
        original = tone(.8, (440,), .2)
        slower = narration_pace(original, .8)
        self.assertGreater(len(slower), len(original)*1.15)
        self.assertLess(abs(len(slower)/SR-1.0), .08)
        self.assertGreater(max(abs(s) for s in slower), 500)

    def test_rejects_unsupported_narration_speed(self):
        with self.assertRaisesRegex(ValueError, 'narration_rate'):
            narration_pace(array.array('h', [1000]*1000), .2)

    def setUp(self):
        self.data = json.loads(Path(__file__).with_name('sample.json').read_text())
        self.data['questions'] = self.data['questions'][:1]

    def test_countdown_and_total_duration(self):
        self.data['countdown'] = 'tick'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'audio.wav'
            write_audio(path, self.data, 120, 60)
            with wave.open(str(path)) as source:
                self.assertEqual(source.getnframes(), 6*SR)
            ticks = [e['seconds'] for e in self.data['audio_events'] if e['kind']=='tick']
            self.assertEqual(ticks, [0, 1, 2, 3])

    def test_short_reveal_rejects_speech_instead_of_truncating(self):
        self.data['voice'] = 'slt'
        with tempfile.TemporaryDirectory() as tmp, patch('audio.speech', return_value=array.array('h', [200])*SR):
            with self.assertRaisesRegex(ValueError, 'Increase --reveal'):
                write_audio(Path(tmp)/'audio.wav', self.data, 120, 15)

    def test_default_does_not_call_tts(self):
        with tempfile.TemporaryDirectory() as tmp, patch('audio.speech') as speak:
            write_audio(Path(tmp)/'audio.wav', self.data, 120, 60)
            speak.assert_not_called()
            self.assertEqual([e['kind'] for e in self.data['audio_events']], ['answer'])

    def test_loud_speech_keeps_headroom_and_complete_duration(self):
        self.data['voice'] = 'elevenlabs'
        loud = array.array('h', [32000, -32000]) * (SR // 2)
        with tempfile.TemporaryDirectory() as tmp, patch('elevenlabs_tts.speech', return_value=loud):
            path = Path(tmp)/'audio.wav'
            write_audio(path, self.data, 120, 60)
            with wave.open(str(path)) as source:
                samples = array.array('h', source.readframes(source.getnframes()))
            start = round(4.48 * SR)
            self.assertEqual(len(samples[start:start+SR]), SR)
            self.assertEqual(max(abs(s) for s in samples[start:start+SR]), round(.65 * 32767))
            event = next(e for e in self.data['audio_events'] if e['kind'] == 'speech')
            self.assertEqual(event['duration'], 1)
            self.assertAlmostEqual(event['seconds'], 4.48)

    def test_narration_precedes_reference_countdown(self):
        self.data.update(question_voice='fpt-leminh', countdown='reference')
        with tempfile.TemporaryDirectory() as tmp, patch('fpt_tts.speech', return_value=array.array('h', [1200])*SR):
            write_audio(Path(tmp)/'audio.wav', self.data, 120, 60)
            events = self.data['audio_events']
            self.assertEqual(events[0]['kind'], 'narration')
            self.assertEqual(events[0]['seconds'], 0)
            self.assertEqual(events[1]['kind'], 'reference_countdown')
            self.assertAlmostEqual(events[1]['seconds'], 1.12)
            self.assertAlmostEqual(events[1]['seconds']+events[1]['duration'], 3.94)

    def test_narration_too_long_is_rejected(self):
        self.data['question_voice'] = 'fpt-leminh'
        with tempfile.TemporaryDirectory() as tmp, patch('fpt_tts.speech', return_value=array.array('h', [1200])*SR*4):
            with self.assertRaisesRegex(ValueError, 'increase --think'):
                write_audio(Path(tmp)/'audio.wav', self.data, 120, 60)


if __name__ == '__main__':
    unittest.main()
