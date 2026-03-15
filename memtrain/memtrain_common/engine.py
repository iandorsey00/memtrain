import csv
import hashlib
import os
import random

from typing import Any

from memtrain.memtrain_common.settings import Settings, SettingError
from memtrain.memtrain_common.database import Database
from memtrain.memtrain_common.models import ProgressRecord, SessionItem
from memtrain.memtrain_common.stats import SessionStatistics
from memtrain.memtrain_common.progress_store import ProgressStore


class NoResponsesError(Exception):
    '''Raised when no study items match the selected session criteria.'''


class CSVError(Exception):
    '''Raised when the study-set CSV is missing required structure.'''


class Engine:
    STAGE_LABELS = {
        0: 'New',
        1: 'Reinforcing',
        2: 'Guided recall',
        3: 'Free recall',
        4: 'Mature',
    }

    def __init__(self, csvfile, level, nquestions, tags, not_tags):
        self.csvfile = csvfile
        self.level = level
        self.nquestions = nquestions
        self.tags = tags
        self.not_tags = not_tags

        csv_list = self.load(self.csvfile)
        self.settings = Settings()
        self.database = Database()
        self.progress_store = ProgressStore(self.csvfile)
        self.study_set_id = self.get_study_set_id()

        indices: dict[str, list[Any]] = {
            'cue': [],
            'response': [],
            'synonym': [],
            'hint': [],
            'tag': [],
            'mtag': [],
            'item_id': [],
        }

        self.set_csv_settings(self.settings, csv_list)
        self.get_csv_column_indices(indices, csv_list)
        self.csv_column_header_row_number = self.get_csv_column_header_row_number(csv_list)
        data_list = csv_list[self.csv_column_header_row_number + 1:]

        self.database.populate(indices, data_list)
        self.all_items = self.build_item_records(indices, data_list)

        self.session_mode = 'adaptive'
        self.configure_session_mode()

        if self.session_mode == 'manual':
            self.settings.level = self.level
        else:
            self.settings.level = '1'

        self.settings.session_mode = self.session_mode

        if self.nquestions:
            try:
                if int(self.nquestions) < 0:
                    raise SettingError('Invalid number of questions specified.')
                else:
                    self.settings.settings['nquestions'] = int(self.nquestions)
            except ValueError:
                raise SettingError('Supplied nquestions is not an int.')

        self.filtered_items = self.filter_items(list(self.all_items))
        self.session_items = self.build_session_items(self.filtered_items)
        self.cr_id_pairs = [(item.cue_id, item.response_id) for item in self.session_items]

        self.mtstatistics = SessionStatistics()
        self.mtstatistics.total = len(self.session_items)

        if self.mtstatistics.total == 0:
            raise NoResponsesError('There are no responses available that match the criteria.')

    def configure_session_mode(self):
        if not self.level:
            return

        enabled_levels = {
            '1': self.settings.settings['level1'],
            '2': self.settings.settings['level2'],
            '3': self.settings.settings['level3'],
        }

        if self.level not in enabled_levels:
            raise SettingError('Invalid level specified.')

        if not enabled_levels[self.level]:
            raise SettingError(f'Level {self.level} functionality has been disabled for this CSV.')

        self.session_mode = 'manual'

    def get_study_set_id(self) -> str:
        normalized = os.path.abspath(self.csvfile)
        return hashlib.sha1(normalized.encode('utf-8')).hexdigest()

    def build_item_id(self, cue: str, response: str) -> str:
        normalized = '{}::{}'.format(cue.strip(), response.strip())
        return hashlib.sha1(normalized.encode('utf-8')).hexdigest()

    def level_for_stage(self, stage: int) -> str:
        if stage <= 1:
            return '1'
        if stage == 2:
            return '2'
        return '3'

    def stage_label(self, stage: int) -> str:
        return self.STAGE_LABELS.get(stage, 'Unknown')

    def merge_progress(
        self,
        item: SessionItem,
        progress_map: dict[str, ProgressRecord],
    ) -> SessionItem:
        progress = progress_map.get(item.item_id, ProgressRecord())

        item.progress = ProgressRecord.from_mapping(progress.to_mapping())
        item.current_stage = item.progress.current_stage
        item.level = self.level_for_stage(item.current_stage)
        item.stage_label = self.stage_label(item.current_stage)
        item.is_new = item.progress.last_seen_at is None

        next_due_at = self.progress_store.parse_datetime(item.progress.next_due_at)
        item.next_due_at = next_due_at
        item.is_due = item.progress.last_seen_at is not None and (
            next_due_at is None or next_due_at <= self.progress_store.now()
        )
        item.is_weak = item.progress.failure_count > 0 or item.progress.mastery_score < 0.4

        return item

    def build_item_records(self, indices, data_list) -> list[SessionItem]:
        out: list[SessionItem] = []

        for data_row in data_list:
            cue = data_row[indices['cue'][0]]

            for placement, response_index in enumerate(indices['response']):
                response = data_row[response_index]

                if not response:
                    continue

                explicit_item_id = ''
                if placement < len(indices['item_id']) and indices['item_id'][placement]:
                    explicit_item_id = data_row[indices['item_id'][placement][0]]

                item = SessionItem(
                    item_id=explicit_item_id or self.build_item_id(cue, response),
                    cue=cue,
                    response=response,
                    cue_id=self.database.get_cue_id(cue),
                    response_id=self.database.get_response_id(response),
                    placement=placement + 1,
                )
                out.append(item)

        return out

    def get_all_response_ids_for_tags(self, tags):
        these_response_ids = []
        args_tags = tags.split(',')

        for tag in args_tags:
            tag = tag.strip()
            if tag:
                these_response_ids += self.database.get_all_response_ids_by_tag(tag)

        return list(set(these_response_ids))

    def filter_items(self, items: list[SessionItem]) -> list[SessionItem]:
        if self.tags:
            these_response_ids = self.get_all_response_ids_for_tags(self.tags)
            items = [item for item in items if item.response_id in these_response_ids]

        if self.not_tags:
            these_response_ids = self.get_all_response_ids_for_tags(self.not_tags)
            items = [item for item in items if item.response_id not in these_response_ids]

        return items

    def build_manual_session_items(
        self,
        items: list[SessionItem],
        progress_map: dict[str, ProgressRecord],
    ) -> list[SessionItem]:
        session_items = [
            self.merge_progress(
                SessionItem(
                    item_id=item.item_id,
                    cue=item.cue,
                    response=item.response,
                    cue_id=item.cue_id,
                    response_id=item.response_id,
                    placement=item.placement,
                ),
                progress_map,
            )
            for item in items
        ]
        random.shuffle(session_items)

        nquestions = self.settings.settings['nquestions']

        if nquestions != 0:
            if nquestions > len(session_items) and len(session_items) > 0:
                add = nquestions - len(session_items)
                duplicates = list(session_items)

                for i in range(add):
                    item = random.choice(session_items)
                    duplicates.append(
                        SessionItem(
                            item_id=item.item_id,
                            cue=item.cue,
                            response=item.response,
                            cue_id=item.cue_id,
                            response_id=item.response_id,
                            placement=item.placement,
                            progress=ProgressRecord.from_mapping(item.progress.to_mapping()),
                            current_stage=item.current_stage,
                            level=item.level,
                            stage_label=item.stage_label,
                            is_new=item.is_new,
                            next_due_at=item.next_due_at,
                            is_due=item.is_due,
                            is_weak=item.is_weak,
                            session_stage=item.session_stage,
                        )
                    )

                session_items = duplicates
            else:
                session_items = session_items[:nquestions]

        for item in session_items:
            item.level = self.level
            item.session_stage = item.current_stage

        return session_items

    def sort_due_items(self, items: list[SessionItem]) -> list[SessionItem]:
        return sorted(
            items,
            key=lambda item: (
                item.next_due_at or self.progress_store.now(),
                item.progress.mastery_score,
                -item.progress.failure_count,
            )
        )

    def sort_weak_items(self, items: list[SessionItem]) -> list[SessionItem]:
        return sorted(
            items,
            key=lambda item: (
                item.progress.mastery_score,
                -item.progress.failure_count,
                item.progress.reviews,
            )
        )

    def adaptive_session_size(self, total_items: int) -> int:
        nquestions = self.settings.settings['nquestions']

        if nquestions:
            return min(nquestions, total_items)

        return min(20, total_items)

    def take_items(
        self,
        pool: list[SessionItem],
        amount: int,
        selected_ids: set[str],
    ) -> list[SessionItem]:
        out: list[SessionItem] = []

        for item in pool:
            if len(out) >= amount:
                break
            if item.item_id in selected_ids:
                continue
            out.append(item)
            selected_ids.add(item.item_id)

        return out

    def build_adaptive_session_items(
        self,
        items: list[SessionItem],
        progress_map: dict[str, ProgressRecord],
    ) -> list[SessionItem]:
        annotated = [
            self.merge_progress(
                SessionItem(
                    item_id=item.item_id,
                    cue=item.cue,
                    response=item.response,
                    cue_id=item.cue_id,
                    response_id=item.response_id,
                    placement=item.placement,
                ),
                progress_map,
            )
            for item in items
        ]
        due_items = self.sort_due_items([item for item in annotated if item.is_due])
        weak_items = self.sort_weak_items([item for item in annotated if item.is_weak and not item.is_due])
        new_items = [item for item in annotated if item.is_new]
        random.shuffle(new_items)

        session_size = self.adaptive_session_size(len(annotated))
        due_target = min(len(due_items), max(1, int(session_size * 0.6)))
        weak_target = min(len(weak_items), int(session_size * 0.25))
        new_target = min(len(new_items), session_size - due_target - weak_target)

        selected_ids = set()
        session_items = []
        session_items += self.take_items(due_items, due_target, selected_ids)
        session_items += self.take_items(weak_items, weak_target, selected_ids)
        session_items += self.take_items(new_items, new_target, selected_ids)

        remainder_pool = due_items + weak_items + new_items + annotated
        session_items += self.take_items(remainder_pool, session_size - len(session_items), selected_ids)
        random.shuffle(session_items)

        for item in session_items:
            item.session_stage = item.current_stage

        return session_items

    def build_session_items(self, items: list[SessionItem]) -> list[SessionItem]:
        item_ids = [item.item_id for item in items]
        progress_map = self.progress_store.get_progress_map(self.study_set_id, item_ids)

        if self.session_mode == 'manual':
            return self.build_manual_session_items(items, progress_map)

        return self.build_adaptive_session_items(items, progress_map)

    def current_item(self, question_index: int) -> SessionItem:
        return self.session_items[question_index]

    def record_result(self, item: SessionItem, is_correct: bool, elapsed_time: float) -> None:
        progress = ProgressRecord.from_mapping(item.progress.to_mapping())
        progress.reviews += 1
        progress.last_seen_at = self.progress_store.to_iso(self.progress_store.now())

        previous_avg = progress.average_response_time
        previous_reviews = progress.reviews - 1
        progress.average_response_time = (
            (previous_avg * previous_reviews + elapsed_time) / progress.reviews
        )

        stage = progress.current_stage
        mastery = progress.mastery_score
        streak = progress.success_streak

        if is_correct:
            streak += 1
            progress.success_streak = streak
            progress.failure_count = max(0, progress.failure_count - 1)
            mastery = min(1.0, mastery + 0.2)
            required_streak = 2 if stage < 3 else 3

            if streak >= required_streak and stage < 4:
                stage += 1
                progress.success_streak = 0
        else:
            stage = max(0, stage - 1)
            progress.success_streak = 0
            progress.failure_count += 1
            progress.lapse_count += 1
            mastery = max(0.0, mastery - 0.25)

        progress.current_stage = stage
        progress.mastery_score = mastery
        progress.next_due_at = self.progress_store.next_due(stage, is_correct)

        item.progress = progress
        item.current_stage = stage
        item.level = self.level if self.session_mode == 'manual' else self.level_for_stage(stage)
        item.stage_label = self.stage_label(stage)

        self.progress_store.update_progress(self.study_set_id, item.item_id, progress)

    def normalize_row(self, row):
        '''Make every string in a row lowercase and remove all whitespace'''
        return [''.join(value.lower().split()) for value in row]

    def load(self, csvfile):
        '''Load the CSV file'''
        out = []

        with open(csvfile, encoding='utf-8') as cf:
            csvreader = csv.reader(cf)
            for row in csvreader:
                out.append(row)

        return out

    def get_indices(self, row, target_str):
        '''Get all indices for target_str in a row'''
        return [index for index, element in enumerate(row) if element == target_str]

    def get_index(self, row, target_str):
        '''Get the first index for target_str in a row.'''
        return self.get_indices(row, target_str)[:1]

    def get_index_mandatory(self, row, target_str):
        '''
        Get a mandatory index for target_str in a row. It is an error if it doesn't
        exist.
        '''
        index = self.get_index(row, target_str)

        if len(index) < 1:
            raise CSVError(f'The mandatory column {target_str} is missing.')
        
        return index

    def is_header_row(self, row):
        '''Determine whether the curent row is the header row'''
        return 'cue' in row and 'response' in row

    def set_csv_settings(self, settings, csv_list):
        '''Set CSV settings'''
        for row in csv_list:
            non_empty = [item for item in row if len(item) > 0]

            if len(non_empty) == 1:
                settings_str = self.normalize_row(row)[0]
                if settings_str.startswith('settings:'):
                    settings.load_settings(settings_str)
                else:
                    settings.set_title(row)

            elif len(non_empty) > 1:
                break

    def get_csv_column_indices(self, indices, csv_list):
        '''Get column indices for database processing'''
        for row in csv_list:
            this_row = self.normalize_row(row)
            if self.is_header_row(this_row):
                indices['cue'] = self.get_index_mandatory(this_row, 'cue')

                indices['response'] = self.get_index_mandatory(this_row, 'response')
                indices['response'] += self.get_index(this_row, 'response2')
                indices['response'] += self.get_index(this_row, 'response3')

                indices['synonym'] = [self.get_indices(this_row, 'synonym')]
                indices['synonym'].append(self.get_indices(this_row, 'synonym2'))
                indices['synonym'].append(self.get_indices(this_row, 'synonym3'))

                indices['hint'] = [self.get_indices(this_row, 'hint')]
                indices['hint'].append(self.get_indices(this_row, 'hint2'))
                indices['hint'].append(self.get_indices(this_row, 'hint3'))

                indices['tag'] = self.get_indices(this_row, 'tag')
                indices['mtag'] = self.get_indices(this_row, 'mtag')
                indices['item_id'] = [self.get_indices(this_row, 'id')]
                indices['item_id'].append(self.get_indices(this_row, 'id2'))
                indices['item_id'].append(self.get_indices(this_row, 'id3'))

                break

    def get_csv_column_header_row_number(self, csv_list):
        '''Get the CSV column header row number'''
        for row_number, row in enumerate(csv_list):
            this_row = self.normalize_row(row)
            if self.is_header_row(this_row):
                return row_number

        raise CSVError('No header row')
