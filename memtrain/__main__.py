import argparse
import csv
import random
import decimal
import time
from datetime import timedelta
from statistics import mean

import os

# SettingError ################################################################
class SettingError(Exception):
    pass

# Settings ####################################################################
class MtSettings:
    def __init__(self):
        self.settings = dict()
        self.all_labels = ['title', 'level1', 'level2', 'level3', 'alias',
        'nquestions']

        ## Boolean settings
        self.boolean_labels = ['level1', 'level2', 'level3', 'alias']

        ### Levels

        # Level 1 - Multiple choice questions
        self.settings['level1'] = True
        # Level 2 - Use a hint to respond
        self.settings['level2'] = True
        # Level 3 - Respond on your own
        self.settings['level3'] = True

        ### Alias

        # Alias
        self.settings['alias'] = True

        ## Integer settings
        self.integer_labels = ['nquestions']

        # nquestions - Number of questions
        self.settings['nquestions'] = 0

        ## String settings
        self.string_labels = ['title']

        # Title
        self.settings['title'] = ''

    def load_settings(self, settings_row):
        '''Load settings from CSV row'''
        # Remove all whitespace characters
        settings_row = ''.join(settings_row.split())
        settings_row = settings_row[len('settings:'):]
        settings_row = settings_row.split(',')

        for setting in settings_row:
            # Negated boolean setting
            if setting[0] == '!':
                label = setting[1:]
                if label in self.boolean_labels:
                    self.settings[label] = False
                else:
                    raise SettingError("'" + setting + "': Invalid setting.")

            # Integer setting
            elif '=' in setting:
                setting = setting.split('=')
                label = setting[0]
                param = int(setting[1])
                try:
                    param = int(param)
                    if label in self.integer_labels:
                        self.settings[label] = param
                except (ValueError, SettingError):
                    raise SettingError("'" + setting + "': Invalid setting.")

            # True boolean setting
            elif setting in self.boolean_labels:
                label = setting
                self.settings[label] = True

            # Else, the setting is invalid.
            else:
                raise SettingError("'" + setting + "': Invalid setting.")

    def set_title(self, title_row):
        '''Set the title'''
        self.settings['title'] = title_row[0]

    def print_settings(self):
        '''Print labels and parameters for each setting.'''
        print("Label".ljust(20) + "Parameter".ljust(20))
        print()
        for label in self.all_labels:
            print(label.ljust(20) + str(self.settings[label]).ljust(20))

def lowercase_row(row):
    '''Make every string in a row lowercase'''
    return list(map(lambda x: x.lower(), row))

def load(csvfile):
    '''Load the CSV file'''
    out = []

    with open(csvfile) as cf:
        csvreader = csv.reader(cf)
        for row in csvreader:
            out.append(row)

    return out


def train(args):
    '''Begin training'''
    # Initialize settings and database
    database = load(args.csvfile)
    cr_database = []
    settings = MtSettings()

    indicies = dict()
    indicies['cue'] = 0
    indicies['response'] = 0

    header_row = 0

    for row_number, row in enumerate(database):
        # Only one non-empty string in row
        if len([item for item in row if len(item) > 0]) == 1:
            settings_str = lowercase_row(row)[0]

            # If it begins with settings: or Settings:, it's the settings
            # string
            if settings_str.startswith('settings:'):
                settings.load_settings(settings_str)
            
            # Otherwise, it's the title row
            else:
                settings.set_title(row)

        else:
            this_row = lowercase_row(row)
            
            if 'cue' in this_row and 'response' in this_row:
                indicies['cue'] = this_row.index('cue')
                indicies['response'] = this_row.index('response')
                header_row = row_number
            
            break

    # Read cue/response pairs
    for row_number, row in enumerate(database[header_row + 1:]):
        cue = row[indicies['cue']]
        response = row[indicies['response']]
        cr_database.append([cue, response])

    # Get responses and aliases
    responses = [i[1] for i in cr_database]
    aliases = dict()

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
    # List of times
    times = []

    # Inter-area margin for printing purposes
    iam = ' '

    # If nquestions is not 0, add necessary questions to cr_database.
    nquestions = settings.settings['nquestions']

    if nquestions is not 0:
        total = len(cr_database)
        add = nquestions - total
        new_cr_database = list(cr_database)

        for i in range(add):
            new_cr_database.append(random.choice(cr_database))
        
        cr_database = list(new_cr_database)

    # Shuffle database
    random.shuffle(cr_database)

    # Initialize statistics
    correct = 0
    incorrect = 0
    question_number = 1
    total = len(cr_database)

    # Prompts
    for cue, response in cr_database:
        if question_number is not 1:
            percentage = decimal.Decimal(correct) / decimal.Decimal(question_number-1) * decimal.Decimal(100)

        print(settings.settings['title'].ljust(29) + iam + 'Cue ' + str(question_number) + '/' + str(total))
        if question_number is not 1:
            print('Correct so far'.ljust(29) + iam + str(correct) + '/' + str(question_number-1) + ' (' + str(round(percentage, 1)) + '%)')
        print()
        print('    ' + cue)
        print()
        start = time.time()
        answer = input('Enter response: ')
        end = time.time()
        elasped_time = end - start
        times.append(elasped_time)
        print()
        os.system('clear')

        if response == answer or response == aliases[answer]:
            print('Correct.')
            correct = correct + 1
        else:
            print('Incorrect. Answer: ' + response)
            incorrect = incorrect + 1
        print()
        question_number = question_number + 1 

    # Print statistics ########################################################
    decimal.getcontext().prec = 5
    percentage = decimal.Decimal(correct) / decimal.Decimal(total) * decimal.Decimal(100)

    print(settings.settings['title'])
    print()
    print('Training session complete.')
    print()
    print('Correct: ' + str(correct) + '/' + str(total) + ' (' + str(round(percentage, 1)) + '%)')
    print('Average response time: ' + str(timedelta(seconds=mean(times))))
    print()

###############################################################################
# Argument parsing with argparse

# Create the top-level argument parser
parser = argparse.ArgumentParser(
    description='A program for better memory training')
parser.set_defaults(func=train)

# Create arguments
parser.add_argument('csvfile', help='The CSV file to load')

# Parse arguments
args = parser.parse_args()
args.func(args)
