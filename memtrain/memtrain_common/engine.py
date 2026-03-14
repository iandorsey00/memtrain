import argparse
import csv
import random
import decimal
import time
import string
import textwrap
import hashlib

from memtrain.memtrain_common.settings import Settings, SettingError
from memtrain.memtrain_common.database import Database
from memtrain.memtrain_common.mtstatistics import MtStatistics
from memtrain.memtrain_common.progress_store import ProgressStore

import os

# NoResponsesError ############################################################
class NoResponsesError(Exception):
    pass

# CSVError ####################################################################
class CSVError(Exception):
    pass

class Engine:
    def __init__(self, csvfile, level, nquestions, tags, not_tags):
        # Initalize core objects
        self.csvfile = csvfile
        self.level = level
        self.nquestions = nquestions
        self.tags = tags
        self.not_tags = not_tags
        self.stage_labels = {
            0: 'New',
            1: 'Reinforcing',
            2: 'Guided recall',
            3: 'Free recall',
            4: 'Mature',
        }

        # Initialize settings and database
        csv_list = self.load(self.csvfile)
        self.settings = Settings()
        self.database = Database()
        self.progress_store = ProgressStore(self.csvfile)
        self.study_set_id = self.get_study_set_id()

        # Initialize indices dictionary
        indices = dict()
        indices['cue'] = []
        indices['response'] = []
        indices['synonym'] = []
        indices['hint'] = []
        indices['tag'] = []
        indices['mtag'] = []
        indices['item_id'] = []

        # Parse the CSV
        self.set_csv_settings(self.settings, csv_list)
        self.get_csv_column_indices(indices, csv_list)
        self.csv_column_header_row_number = self.get_csv_column_header_row_number(csv_list)
        data_list = csv_list[self.csv_column_header_row_number+1:]

        self.database.populate(indices, data_list)
        self.all_items = self.build_item_records(indices, data_list)

        # Now, parse command line settings. ###################################

        self.session_mode = 'adaptive'

        # See if we've set a valid level.
        if self.level:
            if self.level == '1':
                if self.settings.settings['level1'] == False:
                    raise SettingError('Level 1 functionality has been disabled for this CSV.')
                self.session_mode = 'manual'
            elif self.level == '2':
                if self.settings.settings['level2'] == False:
                    raise SettingError('Level 2 functionality has been disabled for this CSV.')
                self.session_mode = 'manual'
            elif self.level == '3':
                if self.settings.settings['level3'] == False:
                    raise SettingError('Level 3 functionality has been disabled for this CSV.')
                self.session_mode = 'manual'
            else:
                raise SettingError('Invalid level specified.')

        if self.session_mode == 'manual':
            self.settings.level = self.level
        else:
            self.settings.level = '1'

        self.settings.session_mode = self.session_mode

        # Get nquestions if specified.
        if self.nquestions:
            try:
                if int(self.nquestions) < 0:
                    raise SettingError('Invalid number of questions specified.')
                else:
                    self.settings.settings['nquestions'] = int(self.nquestions)
            except ValueError:
                raise SettingError('Supplied nquestions is not an int.')

        # Main training program ###############################################
        self.filtered_items = self.filter_items(list(self.all_items))
        self.session_items = self.build_session_items(self.filtered_items)
        self.cr_id_pairs = [(item['cue_id'], item['response_id']) for item in self.session_items]

        # MtStatistics
        self.mtstatistics = MtStatistics()
        self.mtstatistics.total = len(self.session_items)

        # Raise NoResponsesError if there are no responses available.
        if self.mtstatistics.total == 0:
            raise NoResponsesError('There are no responses available that match the criteria.')

    def get_study_set_id(self):
        normalized = os.path.abspath(self.csvfile)
        return hashlib.sha1(normalized.encode('utf-8')).hexdigest()

    def build_item_id(self, cue, response):
        normalized = '{}::{}'.format(cue.strip(), response.strip())
        return hashlib.sha1(normalized.encode('utf-8')).hexdigest()

    def level_for_stage(self, stage):
        if stage <= 1:
            return '1'
        if stage == 2:
            return '2'
        return '3'

    def stage_label(self, stage):
        return self.stage_labels.get(stage, 'Unknown')

    def default_progress(self):
        return {
            'current_stage': 0,
            'mastery_score': 0.0,
            'success_streak': 0,
            'failure_count': 0,
            'lapse_count': 0,
            'average_response_time': 0.0,
            'reviews': 0,
            'last_seen_at': None,
            'next_due_at': None,
        }

    def merge_progress(self, item, progress_map):
        progress = dict(self.default_progress())
        if item['item_id'] in progress_map:
            progress.update(progress_map[item['item_id']])

        item['progress'] = progress
        item['current_stage'] = int(progress['current_stage'])
        item['level'] = self.level_for_stage(item['current_stage'])
        item['stage_label'] = self.stage_label(item['current_stage'])
        item['is_new'] = progress['last_seen_at'] is None

        next_due_at = self.progress_store.parse_datetime(progress['next_due_at'])
        item['next_due_at'] = next_due_at
        item['is_due'] = progress['last_seen_at'] is not None and (
            next_due_at is None or next_due_at <= self.progress_store.now()
        )
        item['is_weak'] = progress['failure_count'] > 0 or progress['mastery_score'] < 0.4

        return item

    def build_item_records(self, indices, data_list):
        out = []

        for data_row in data_list:
            cue = data_row[indices['cue'][0]]

            for placement, response_index in enumerate(indices['response']):
                response = data_row[response_index]

                if not response:
                    continue

                item = {
                    'item_id': self.build_item_id(cue, response),
                    'cue': cue,
                    'response': response,
                    'cue_id': self.database.get_cue_id(cue),
                    'response_id': self.database.get_response_id(response),
                    'placement': placement + 1,
                }
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

    def filter_items(self, items):
        if self.tags:
            these_response_ids = self.get_all_response_ids_for_tags(self.tags)
            items = [item for item in items if item['response_id'] in these_response_ids]

        if self.not_tags:
            these_response_ids = self.get_all_response_ids_for_tags(self.not_tags)
            items = [item for item in items if item['response_id'] not in these_response_ids]

        return items

    def build_manual_session_items(self, items, progress_map):
        session_items = [self.merge_progress(dict(item), progress_map) for item in items]
        random.shuffle(session_items)

        nquestions = self.settings.settings['nquestions']

        if nquestions != 0:
            if nquestions > len(session_items) and len(session_items) > 0:
                add = nquestions - len(session_items)
                duplicates = list(session_items)

                for i in range(add):
                    duplicates.append(dict(random.choice(session_items)))

                session_items = duplicates
            else:
                session_items = session_items[:nquestions]

        for item in session_items:
            item['level'] = self.level
            item['session_stage'] = item['current_stage']

        return session_items

    def sort_due_items(self, items):
        return sorted(
            items,
            key=lambda item: (
                item['next_due_at'] or self.progress_store.now(),
                item['progress']['mastery_score'],
                -item['progress']['failure_count'],
            )
        )

    def sort_weak_items(self, items):
        return sorted(
            items,
            key=lambda item: (
                item['progress']['mastery_score'],
                -item['progress']['failure_count'],
                item['progress']['reviews'],
            )
        )

    def adaptive_session_size(self, total_items):
        nquestions = self.settings.settings['nquestions']

        if nquestions:
            return min(nquestions, total_items)

        return min(20, total_items)

    def take_items(self, pool, amount, selected_ids):
        out = []

        for item in pool:
            if len(out) >= amount:
                break
            if item['item_id'] in selected_ids:
                continue
            out.append(item)
            selected_ids.add(item['item_id'])

        return out

    def build_adaptive_session_items(self, items, progress_map):
        annotated = [self.merge_progress(dict(item), progress_map) for item in items]
        due_items = self.sort_due_items([item for item in annotated if item['is_due']])
        weak_items = self.sort_weak_items([item for item in annotated if item['is_weak'] and not item['is_due']])
        new_items = [item for item in annotated if item['is_new']]
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
            item['session_stage'] = item['current_stage']

        return session_items

    def build_session_items(self, items):
        item_ids = [item['item_id'] for item in items]
        progress_map = self.progress_store.get_progress_map(self.study_set_id, item_ids)

        if self.session_mode == 'manual':
            return self.build_manual_session_items(items, progress_map)

        return self.build_adaptive_session_items(items, progress_map)

    def current_item(self, question_index):
        return self.session_items[question_index]

    def record_result(self, item, is_correct, elapsed_time):
        progress = dict(item['progress'])
        progress['reviews'] = int(progress['reviews']) + 1
        progress['last_seen_at'] = self.progress_store.to_iso(self.progress_store.now())

        previous_avg = float(progress['average_response_time'])
        previous_reviews = progress['reviews'] - 1
        progress['average_response_time'] = (
            (previous_avg * previous_reviews + elapsed_time) / progress['reviews']
        )

        stage = int(progress['current_stage'])
        mastery = float(progress['mastery_score'])
        streak = int(progress['success_streak'])

        if is_correct:
            streak += 1
            progress['success_streak'] = streak
            progress['failure_count'] = max(0, int(progress['failure_count']) - 1)
            mastery = min(1.0, mastery + 0.2)
            required_streak = 2 if stage < 3 else 3

            if streak >= required_streak and stage < 4:
                stage += 1
                progress['success_streak'] = 0
        else:
            stage = max(0, stage - 1)
            progress['success_streak'] = 0
            progress['failure_count'] = int(progress['failure_count']) + 1
            progress['lapse_count'] = int(progress['lapse_count']) + 1
            mastery = max(0.0, mastery - 0.25)

        progress['current_stage'] = stage
        progress['mastery_score'] = mastery
        progress['next_due_at'] = self.progress_store.next_due(stage, is_correct)

        item['progress'] = progress
        item['current_stage'] = stage
        item['level'] = self.level if self.session_mode == 'manual' else self.level_for_stage(stage)
        item['stage_label'] = self.stage_label(stage)

        self.progress_store.update_progress(self.study_set_id, item['item_id'], progress)

    def normalize_row(self, row):
        '''Make every string in a row lowercase and remove all whitespace'''
        # Lowercase row
        out = list(map(lambda x: x.lower(), row))
        # Remove whitespace from row and return
        return list(map(lambda x: ''.join(x.split()), out))

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
        index = self.get_indices(row, target_str)[:1]
        return index

    def get_index_mandatory(self, row, target_str):
        '''
        Get a mandatory index for target_str in a row. It is an error if it doesn't
        exist.
        '''
        index = self.get_index(row, target_str)

        if len(index) < 1:
            raise CSVError('The mandatory column {} is missing.', target_str)
        
        return index

    def is_header_row(self, row):
        '''Determine whether the curent row is the header row'''
        return 'cue' in row and 'response' in row

    def set_csv_settings(self, settings, csv_list):
        '''Set CSV settings'''
        for row in csv_list:
            # Only one non-empty string in row
            if len([item for item in row if len(item) > 0]) == 1:
                settings_str = self.normalize_row(row)[0]

                # If it begins with settings: or Settings:, it's the settings
                # string
                if settings_str.startswith('settings:'):
                    settings.load_settings(settings_str)
                
                # Otherwise, it's the title row
                else:
                    settings.set_title(row)
            
            # Stop if there is more than one non-empty string
            elif len([item for item in row if len(item) > 0]) > 1:
                break

    def get_csv_column_indices(self, indices, csv_list):
        '''Get column indices for database processing'''
        for row in csv_list:
            this_row = self.normalize_row(row)
            
            # If a row contains 'Cue' and 'Response', it is designated as the
            # column header row.
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

                # We're done after the header row.
                break

    def get_csv_column_header_row_number(self, csv_list):
        '''Get the CSV column header row number'''
        for row_number, row in enumerate(csv_list):
            this_row = self.normalize_row(row)
            if self.is_header_row(this_row):
                return row_number

        # It's an error if there is no header row.
        raise CSVError('No header row')
