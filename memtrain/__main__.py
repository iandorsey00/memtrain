import argparse
import csv
import random
import decimal
import time
import string
import textwrap
from datetime import timedelta
from statistics import mean

import os

# SettingError ################################################################
class SettingError(Exception):
    pass

# NoCueError ##################################################################
class NoCueError(Exception):
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
    indicies['cue'] = -1
    indicies['response'] = -1
    indicies['mtag'] = []

    header_row = 0

    # Set level, if one was specified:
    if args.level:
        if args.level == 1:
            settings.settings['level1'] = True
            settings.settings['level2'] = False
            settings.settings['level3'] = False
        elif args.level == 2:
            settings.settings['level1'] = False
            settings.settings['level2'] = True
            settings.settings['level3'] = False
        elif args.level == '3':
            settings.settings['level1'] = False
            settings.settings['level2'] = False
            settings.settings['level3'] = True

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
                indicies['tag'] = [index for index, element in enumerate(this_row) if element == 'tag']
                indicies['mtag'] = [index for index, element in enumerate(this_row) if element == 'mtag']
                header_row = row_number
            
            break

    # Read cue/response pairs, tags, and mtags
    for row_number, row in enumerate(database[header_row + 1:]):
        cue = row[indicies['cue']]
        response = row[indicies['response']]
        tags = []
        mtags = []
        for index in indicies['tag']:
            tags.append(row[index])
        for index in indicies['mtag']:
            mtags.append(row[index])
        cr_database.append({'cue': cue, 'response': response, 'tags': tags,
        'mtags': mtags})

    if args.tags:
        args_tags = args.tags.split(',')
        cr_database = [row for row in cr_database if not set(args_tags).isdisjoint(row['tags'])]

    # Map mtags to responses
    mtag_list = dict()
    for row in cr_database:
        these_mtags = row['mtags']
        for this_mtag in these_mtags:
            response = row['response']
            if this_mtag not in mtag_list.keys():
                mtag_list[this_mtag] = [response]
            else:
                mtag_list[this_mtag].append(response)

    # Get responses and aliases
    responses = [i['response'] for i in cr_database]
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

    # Prompts #################################################################
    for this_dict in cr_database:
        cue = this_dict['cue']
        response = this_dict['response']
        mtags = this_dict['mtags']
        # Get number of mtags
        n_mtags = len(mtags)

        # Format the cue
        f_cue = cue.replace('{{}}', '_________')
        f_cue = textwrap.fill(f_cue, initial_indent='    ', subsequent_indent='    ', width=80)

        # Print how questions were answered correctly so far if we are not on
        # the first question.
        if question_number is not 1:
            percentage = decimal.Decimal(correct) / decimal.Decimal(question_number-1) * decimal.Decimal(100)

        # Print first two rows and the cue.
        print(settings.settings['title'].ljust(69) + iam + ('Cue ' + str(question_number) + '/' + str(total)).rjust(10))
        if question_number is not 1:
            print('Correct so far'.ljust(59) + iam + (str(correct) + '/' + str(question_number-1) + ' (' + str(round(percentage, 1)) + '%)').rjust(20))
        print()
        print(f_cue)
        print()

        # If on level one, generate the multiple choice questions.
        if settings.settings['level1']:
            # First, make copies of sets of responses for each mtag.
            response_copies_by_mtag = dict()

            for mtag in mtags:
                # Delete the correct reponse
                response_copies_by_mtag[mtag] = [i for i in mtag_list[mtag] if i is not response]

            # How many multiple choices will there be?
            ascii_range = string.ascii_lowercase[:4]
            
            # Select the index for the correct choice at random.
            correct_index = random.choice(ascii_range)

            # Now, for each choice, print the response.
            for i in ascii_range:
                # Reset and shuffle copied data.
                these_response_copies_by_mtag = dict(response_copies_by_mtag)
                for key in response_copies_by_mtag.keys():
                    random.shuffle(response_copies_by_mtag[key])
                these_mtags = list(mtags)
                random.shuffle(these_mtags)
                # If i is the correct_index, print the correct response
                if i == correct_index:
                    # Print the capitalized correct response.
                    print((i + ')').ljust(5) + iam + response.capitalize())
                # Otherwise, select an incorrect response at random.
                else:
                    this_mtag = random.choice(these_mtags)
                    # If there are no more mtags for this_mtag, delete it from
                    # these_mtags.
                    while len(these_response_copies_by_mtag[this_mtag]) == 0:
                        these_mtags.remove(this_mtag)
                        # If these_mtags is empty, just choose a random mtag.
                        if len(these_mtags) == 0:
                            this_mtag = random.choice(list(mtag_list.keys()))
                            these_response_copies_by_mtag[this_mtag] = [i for i in mtag_list[this_mtag] if i is not response]
                    # Get a random response.
                    this_response = these_response_copies_by_mtag[this_mtag].pop()
                    # If the response is the same as the correct response,
                    # get another one.
                    while this_response == response:
                        this_response = these_response_copies_by_mtag[this_mtag].pop()
                    # Print the capitalized response
                    print((i + ')').ljust(5) + iam + this_response.capitalize())

            print()

        # Start time
        start = time.time()
        # Prompt for a response
        user_input = input('Enter response: ')
        # End time
        end = time.time()
        # Get elapsed time and add it to times.
        elasped_time = end - start
        times.append(elasped_time)
        print()
        # Clear screen.
        os.system('clear')

        if settings.settings['level1']:
            correct_user_input = correct_index == user_input
        elif settings.settings['level3']:
            if user_input in aliases.keys():
                correct_user_input = response.lower() == user_input.lower() or response == aliases[user_input.lower()]
            else:
                correct_user_input = response.lower() == user_input.lower()

        if correct_user_input:
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
parser.add_argument('-t', '--tags', help='Study these tags only')
parser.add_argument('-l', '--level', help='Specify which level to study')
parser.add_argument('csvfile', help='The CSV file to load')

# Parse arguments
args = parser.parse_args()
args.func(args)
