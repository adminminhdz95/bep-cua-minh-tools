import copy
import json
from pathlib import Path
import unittest

from render import prepare, frames, card, landscape, color_ink

SAMPLE = json.loads(Path(__file__).with_name('sample.json').read_text())


class QuizValidationTests(unittest.TestCase):
    def test_color_palette_is_complete_and_valid(self):
        source = copy.deepcopy(SAMPLE)
        source['option_colors'] = {'young': '#bad'}
        with self.assertRaisesRegex(ValueError, '#RRGGBB'):
            prepare(source)
        source['option_colors'] = {'young': '#ff0000'}
        with self.assertRaisesRegex(ValueError, 'missing an option'):
            prepare(source)

    def test_color_cards_retain_their_color_at_reveal(self):
        source = copy.deepcopy(SAMPLE)
        source['questions'] = source['questions'][:1]
        words = [source['questions'][0]['word']] + [d['word'] for d in source['questions'][0]['distractors']]
        colors = ['#00ff00', '#ffffff', '#000000', '#ffff00']
        source['option_colors'] = dict(zip(words, colors))
        data = prepare(source)
        q = data['questions'][0]
        bg = landscape()
        before, after = [card(bg, data, q, 0, reveal) for reveal in (False, True)]
        for j in range(4):
            point = (975, 755+j*186+70)
            self.assertEqual(before.getpixel(point), after.getpixel(point))
            marker = (142, 755+j*186+40)
            self.assertEqual(min(after.getpixel(marker)) > 220, j == q['answer'])
            self.assertFalse(min(before.getpixel(marker)) > 220)
        # The check stroke is actually visible, even with a font missing ✓.
        y = 755 + q['answer'] * 186
        self.assertEqual(after.getpixel((137, y+87)), (0, 0, 0))
        self.assertEqual(color_ink('#ffffff'), '#000000')
        self.assertEqual(color_ink('#000000'), '#ffffff')

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
