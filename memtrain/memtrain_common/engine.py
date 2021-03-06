import argparse
import csv
import random
import decimal
import time
import string
import textwrap

from memtrain.memtrain_common.settings import Settings
from memtrain.memtrain_common.database import Database
from memtrain.memtrain_common.mtstatistics import MtStatistics

import os

# SettingError ################################################################
class SettingError(Exception):
    pass

# NoResponsesError ############################################################
class NoResponsesError(Exception):
    pass

# CSVError ####################################################################
class CSVError(Exception):
    pass

class Engine:
    def __init__(self, csvfile, level='', nquestions='', tags='', not_tags=''):
        # Initalize parameters
        self.csvfile = csvfile
        self.level = level
        self.nquestions = nquestions
        self.tags = tags
        self.not_tags = not_tags

        # Initialize settings and database
        csv_list = self.load(self.csvfile)
        self.settings = Settings()
        self.database = Database()

        # Initialize indices dictionary
        indices = dict()
        indices['cue'] = []
        indices['response'] = []
        indices['synonym'] = []
        indices['hint'] = []
        indices['tag'] = []
        indices['mtag'] = []

        self.set_csv_settings(self.settings, csv_list)
        self.get_csv_column_indices(indices, csv_list)
        self.csv_column_header_row_number = self.get_csv_column_header_row_number(csv_list)
        data_list = csv_list[self.csv_column_header_row_number+1:]

        self.database.populate(indices, data_list)

        # Now, parse command line settings. #######################################

        # Set level, if one was specified:
        if self.level:
            if self.level == '1':
                if self.settings.settings['level1'] == False:
                    raise SettingError('Level 1 functionality has been disabled for this CSV.')
                else:
                    self.settings.settings['level1'] = True
                    self.settings.settings['level2'] = False
                    self.settings.settings['level3'] = False
            elif self.level == '2':
                if self.settings.settings['level2'] == False:
                    raise SettingError('Level 2 functionality has been disabled for this CSV.')
                else:
                    self.settings.settings['level1'] = False
                    self.settings.settings['level2'] = True
                    self.settings.settings['level3'] = False
            elif self.level == '3':
                if self.settings.settings['level3'] == False:
                    raise SettingError('Level 3 functionality has been disabled for this CSV.')
                else:
                    self.settings.settings['level1'] = False
                    self.settings.settings['level2'] = False
                    self.settings.settings['level3'] = True
            else:
                raise SettingError('Invalid level specified.')

        # Get nquestions if specified on the command line.
        if self.nquestions:
            if self.nquestions < 0:
                raise SettingError('Invalid number of questions specified.')
            else:
                self.settings.settings['nquestions'] = self.nquestions

        # Get responses
        # responses = database.get_all_responses()

        # Main training program ###################################################
        self.cr_id_pairs = self.database.get_all_cue_response_id_pairs()

        # Get response IDs for multiple tags
        def get_all_response_ids_for_tags(tags):
            these_response_ids = []
            args_tags = tags.split(',')
            for tag in args_tags:
                these_response_ids += self.database.get_all_response_ids_by_tag(tag)
            return list(set(these_response_ids))

        # Filter out other tags if tags were specified on the command line.
        if self.tags:
            these_response_ids = get_all_response_ids_for_tags(self.tags)
            cr_id_pairs = [i for i in cr_id_pairs if i[1] in these_response_ids]

        # Remove tags if not-tags were specified on the command line.
        if self.not_tags:
            these_response_ids = get_all_response_ids_for_tags(self.not_tags)
            cr_id_pairs = [i for i in cr_id_pairs if i[1] not in these_response_ids]

        self.mtstatistics = MtStatistics()
        self.mtstatistics.total = len(self.cr_id_pairs)

        # If nquestions is not 0, add necessary responses or remove responses.
        nquestions = self.settings.settings['nquestions']

        if nquestions != 0:
            # If nquestions is greater than the total number of questions,
            # duplicate them at random until nquestions is reached.
            if nquestions > self.mtstatistics.total:
                add = nquestions - self.mtstatistics.total
                new_cr_id_pairs = list(cr_id_pairs)

                for i in range(add):
                    new_cr_id_pairs.append(random.choice(cr_id_pairs))
                
                cr_id_pairs = list(new_cr_id_pairs)
                self.mtstatistics.total = len(cr_id_pairs)
            # If nquestions is less than the total number of questions, choose the
            # questions at random until we have another.
            elif nquestions < self.mtstatistics.total:
                random.shuffle(cr_id_pairs)
                new_cr_id_pairs= []
                for i in range(nquestions):
                    new_cr_id_pairs.append(cr_id_pairs[i])
                
                self.cr_id_pairs = list(new_cr_id_pairs)
                self.mtstatistics.total = len(cr_id_pairs)
            # If nquestions is equal to the total number of questions, don't do
            # anything.

        # Shuffle database
        random.shuffle(self.cr_id_pairs)

        # Raise NoResponsesError if there are no responses available.
        if self.mtstatistics.total == 0:
            raise NoResponsesError('There are no responses available that match the criteria.')

        # return (settings, database, mtstatistics, cr_id_pairs)


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