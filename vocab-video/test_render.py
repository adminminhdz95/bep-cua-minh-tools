import copy
import json
from pathlib import Path
import unittest

from render import prepare, frames

SAMPLE = json.loads(Path(__file__).with_name('sample.json').read_text())


class QuizValidationTests(unittest.TestCase):
    def test_balanced_positions_for_many_questions(self):
        source = copy.deepcopy(SAMPLE)
        source['questions'] *= 8
        prepared = prepare(source, seed=28)
        positions = [q['answer'] for q in prepared['questions']]
        self.assertEqual([positions.count(i) for i in range(4)], [10]*4)
        for q in prepared['questions']:
            self.assertEqual(q['options'][q['answer']]['word'], q['word'])

    def test_rejects_mixed_parts_of_speech(self):
        source = copy.deepcopy(SAMPLE)
        source['questions'][0]['distractors'][0]['pos'] = 'verb'
        with self.assertRaisesRegex(ValueError, 'part of speech'):
            prepare(source)

    def test_rejects_unicode_duplicate_options_and_meanings(self):
        for key in ('word', 'meaning'):
            with self.subTest(key=key):
                source = copy.deepcopy(SAMPLE)
                source['questions'][0]['distractors'][0][key] = source['questions'][0][key].upper()
                with self.assertRaisesRegex(ValueError, 'duplicate'):
                    prepare(source)

    def test_rejects_invalid_durations(self):
        for seconds in (0, -.2, .01, 1.01, 61, float('nan'), float('inf'), True):
            with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                frames(seconds, 'time')
        self.assertEqual(frames(4, 'time'), 120)

    def test_requires_three_distractors(self):
        source = copy.deepcopy(SAMPLE)
        source['questions'][0]['distractors'].pop()
        with self.assertRaisesRegex(ValueError, 'three'):
            prepare(source)


if __name__ == '__main__':
    unittest.main()
