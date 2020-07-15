import argparse
import csv
import random
import decimal
import time
import string
import textwrap

from datetime import timedelta
from statistics import mean

from settings import Settings
from database import Database
from question import Question
from mtstatistics import MtStatistics

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

def normalize_row(row):
    '''Make every string in a row lowercase and remove all whitespace'''
    # Lowercase row
    out = list(map(lambda x: x.lower(), row))
    # Remove whitespace from row and return
    return list(map(lambda x: ''.join(x.split()), out))

def load(csvfile):
    '''Load the CSV file'''
    out = []

    with open(csvfile) as cf:
        csvreader = csv.reader(cf)
        for row in csvreader:
            out.append(row)

    return out

def get_indices(row, target_str):
    '''Get all indices for target_str in a row'''
    return [index for index, element in enumerate(row) if element == target_str]

def get_index(row, target_str):
    '''Get the first index for target_str in a row.'''
    index = get_indices(row, target_str)[:1]
    return index

def get_index_mandatory(row, target_str):
    '''
    Get a mandatory index for target_str in a row. It is an error if it doesn't
    exist.
    '''
    index = get_index(row, target_str)

    if len(index) < 1:
        raise CSVError('The mandatory column {} is missing.', target_str)
    
    return index

def is_header_row(row):
    '''Determine whether the curent row is the header row'''
    return 'cue' in row and 'response' in row

def set_csv_settings(settings, csv_list):
    '''Set CSV settings'''
    for row in csv_list:
        # Only one non-empty string in row
        if len([item for item in row if len(item) > 0]) == 1:
            settings_str = normalize_row(row)[0]

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

def get_csv_column_indices(indices, csv_list):
    '''Get column indices for database processing'''
    for row in csv_list:
        this_row = normalize_row(row)
        
        # If a row contains 'Cue' and 'Response', it is designated as the
        # column header row.
        if is_header_row(this_row):
            indices['cue'] = get_index_mandatory(this_row, 'cue')

            indices['response'] = get_index_mandatory(this_row, 'response')
            indices['response'] += get_index(this_row, 'response2')
            indices['response'] += get_index(this_row, 'response3')

            indices['synonym'] = get_index_mandatory(this_row, 'synonym')
            indices['synonym'] += get_index(this_row, 'synonym2')
            indices['synonym'] += get_index(this_row, 'synonym3')

            indices['hint'] = get_indices(this_row, 'hint')
            indices['hint'] += get_index(this_row, 'hint2')
            indices['hint'] += get_index(this_row, 'hint3')

            indices['tag'] = get_indices(this_row, 'tag')
            indices['mtag'] = get_indices(this_row, 'mtag')

            # We're done after the header row.
            break

def get_csv_column_header_row_number(csv_list):
    '''Get the CSV column header row number'''
    for row_number, row in enumerate(csv_list):
        this_row = normalize_row(row)
        if is_header_row(this_row):
            return row_number

    # It's an error if there is no header row.
    raise CSVError('No header row')

def train(args):
    '''Begin training'''
    # Initialize settings and database
    csv_list = load(args.csvfile)
    settings = Settings()
    database = Database()

    # Initialize indices dictionary
    indices = dict()
    indices['cue'] = []
    indices['response'] = []
    indices['synonym'] = []
    indices['hint'] = []
    indices['tag'] = []
    indices['mtag'] = []

    set_csv_settings(settings, csv_list)
    get_csv_column_indices(indices, csv_list)
    csv_column_header_row_number = get_csv_column_header_row_number(csv_list)
    data_list = csv_list[csv_column_header_row_number+1:]

    database.populate(indices, data_list)

    # Now, parse command line settings. #######################################

    # Set level, if one was specified:
    if args.level:
        if args.level == '1':
            if settings.settings['level1'] == False:
                raise SettingError('Level 1 functionality has been disabled for this CSV.')
            else:
                settings.settings['level1'] = True
                settings.settings['level2'] = False
                settings.settings['level3'] = False
        elif args.level == '2':
            if settings.settings['level2'] == False:
                raise SettingError('Level 2 functionality has been disabled for this CSV.')
            else:
                settings.settings['level1'] = False
                settings.settings['level2'] = True
                settings.settings['level3'] = False
        elif args.level == '3':
            if settings.settings['level3'] == False:
                raise SettingError('Level 3 functionality has been disabled for this CSV.')
            else:
                settings.settings['level1'] = False
                settings.settings['level2'] = False
                settings.settings['level3'] = True
        else:
            raise SettingError('Invalid level specified.')

    # Get nquestions if specified on the command line.
    if args.nquestions:
        if args.nquestions < 0:
            raise SettingError('Invalid number of questions specified.')
        else:
            settings.settings['nquestions'] = args.nquestions

    # Get responses and aliases
    responses = database.get_all_responses()
    aliases = dict()

    # Map aliases to responses
    if settings.settings['alias']:
        unique_responses = list(set(responses))
        for unique_response in unique_responses:
            lc_unique_response = unique_response.lower()
            level = 1
            complete = False
            while not complete:
                proposed_key = lc_unique_response[:level]
                if proposed_key not in aliases.keys():
                    aliases[proposed_key] = unique_response
                    level = 1
                    complete = True
                else:
                    get_key = aliases.pop(proposed_key)
                    level = level + 1
                    aliases[get_key[:level].lower()] = get_key

    # Main training program ###################################################
    cr_id_pairs = database.get_all_cue_response_id_pairs()

    # Filter out other tags if tags were specified on the command line.
    if args.tags:
        these_response_ids = []
        args_tags = args.tags.split(',')
        for tag in args_tags:
            these_response_ids += database.get_all_response_ids_by_tag(tag)
        these_response_ids = list(set(these_response_ids))
        cr_id_pairs = [i for i in cr_id_pairs if i[1] in these_response_ids]

    mtstatistics = MtStatistics()
    mtstatistics.total = len(cr_id_pairs)

    # If nquestions is not 0, add necessary responses or remove responses.
    nquestions = settings.settings['nquestions']

    if nquestions is not 0:
        # If nquestions is greater than the total number of questions,
        # duplicate them at random until nquestions is reached.
        if nquestions > mtstatistics.total:
            add = nquestions - total
            new_cr_id_pairs = list(cr_id_pairs)

            for i in range(add):
                new_response_ids.append(random.choice(cr_id_pairs))
            
            cr_id_pairs = list(new_cr_id_pairs)
        # If nquestions is less than the total number of questions, choose the
        # questions at random until we have another.
        elif nquestions < mtstatistics.total:
            random.shuffle(cr_id_pairs)
            new_cr_id_pairs= []
            for i in range(nquestions):
                new_cr_id_pairs.append(cr_id_pairs[i])
            
            cr_id_pairs = list(new_cr_id_pairs)
        # If nquestions is equal to the total number of questions, don't do
        # anything.

    # Shuffle database
    random.shuffle(cr_id_pairs)

    # Raise NoResponsesError if there are no responses available.
    if mtstatistics.total == 0:
        raise NoResponsesError('There are no responses available that match the criteria.')

    question = Question(settings, database)

    for cr_id_pair in cr_id_pairs:
        mtstatistics.is_input_valid = False

        # Don't continue with the loop until a valid response has been
        # entered.
        while not mtstatistics.is_input_valid:
            question.render_question(cr_id_pair[0], cr_id_pair[1], mtstatistics, aliases)

    question.print_header(True)
    print()
    print('Training session complete.')
    print()
    print('Correct: ' + str(mtstatistics.number_correct) + '/' + str(mtstatistics.total) + ' (' + str(round(mtstatistics.percentage, 1)) + '%)')
    print('Average response time: ' + str(timedelta(seconds=mean(mtstatistics.times))))
    print()
    if(mtstatistics.number_incorrect > 0):
        print('Responses for which answers were incorrect:')
        print()
        print(mtstatistics.formatted_incorrect_responses())
        print()

###############################################################################
# Argument parsing with argparse

# Create the top-level argument parser
parser = argparse.ArgumentParser(
    description='A program for better memory training')
parser.set_defaults(func=train)

# Create arguments
parser.add_argument('-t', '--tags', help='Study these tags only')
parser.add_argument('-l', '--level', help='Specify which level to study')
parser.add_argument('-n', '--nquestions', type=int, help='Set the number of questions for this session')
parser.add_argument('csvfile', help='The CSV file to load')

# Parse arguments
args = parser.parse_args()
args.func(args)
