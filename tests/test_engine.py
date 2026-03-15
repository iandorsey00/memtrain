import os
import tempfile
import textwrap
import unittest

from pathlib import Path

from memtrain.memtrain_common.engine import Engine


class EngineTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.workspace = Path(self.temp_dir.name)
        self.progress_db = self.workspace / 'progress.sqlite3'
        os.environ['MEMTRAIN_PROGRESS_DB'] = str(self.progress_db)
        self.addCleanup(os.environ.pop, 'MEMTRAIN_PROGRESS_DB', None)

    def write_csv(self, name, content):
        csv_path = self.workspace / name
        csv_path.write_text(textwrap.dedent(content).lstrip(), encoding='utf-8')
        return csv_path

    def test_manual_level_session_uses_requested_level(self):
        csv_path = self.write_csv(
            'animals.csv',
            '''
            Animals
            Cue,Response,Hint,Tag
            {{}} make milk.,Cows,Mooo,Ungulates
            You can ride on a {{}}.,horse,Neigh,Ungulates
            ''',
        )

        engine = Engine(str(csv_path), '2', None, None, None)

        self.assertEqual(engine.session_mode, 'manual')
        self.assertEqual(engine.settings.level, '2')
        self.assertTrue(all(item.level == '2' for item in engine.session_items))

    def test_adaptive_session_filters_by_tag(self):
        csv_path = self.write_csv(
            'animals.csv',
            '''
            Animals
            Cue,Response,Hint,Tag
            {{}} make milk.,Cows,Mooo,Ungulates
            You can ride on a {{}}.,horse,Neigh,Ungulates
            "{{}} are smaller than lions, not dangerous, and domesticated.",Cats,Meow,Felidae
            This land animal can be dangerous. It is a large carnivore often seen in zoos.,Lion,Roar,Felidae
            ''',
        )

        engine = Engine(str(csv_path), None, 10, 'Felidae', None)

        self.assertEqual(engine.session_mode, 'adaptive')
        self.assertEqual(sorted(item.response for item in engine.session_items), ['Cats', 'Lion'])

    def test_explicit_item_ids_are_used_when_present(self):
        csv_path = self.write_csv(
            'with_ids.csv',
            '''
            Animals
            Cue,Response,Hint,Tag,Id
            {{}} make milk.,Cows,Mooo,Ungulates,cows-1
            You can ride on a {{}}.,horse,Neigh,Ungulates,horse-1
            ''',
        )

        engine = Engine(str(csv_path), None, None, None, None)

        self.assertEqual(
            sorted(item.item_id for item in engine.session_items),
            ['cows-1', 'horse-1'],
        )

    def test_progress_persists_between_sessions(self):
        csv_path = self.write_csv(
            'animals.csv',
            '''
            Animals
            Cue,Response,Hint,Tag
            {{}} make milk.,Cows,Mooo,Ungulates
            You can ride on a {{}}.,horse,Neigh,Ungulates
            ''',
        )

        engine = Engine(str(csv_path), None, None, None, None)
        item = engine.session_items[0]
        item_id = item.item_id

        engine.record_result(item, True, 2.5)
        engine.record_result(item, True, 2.0)

        follow_up_engine = Engine(str(csv_path), None, None, None, None)
        persisted_item = next(
            session_item for session_item in follow_up_engine.session_items
            if session_item.item_id == item_id
        )

        self.assertEqual(persisted_item.current_stage, 1)
        self.assertGreater(persisted_item.progress.mastery_score, 0.0)
        self.assertIsNotNone(persisted_item.progress.next_due_at)


if __name__ == '__main__':
    unittest.main()
