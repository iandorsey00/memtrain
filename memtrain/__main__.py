import argparse
import csv
import random
import decimal
import time
import string
import textwrap
import sqlite3
from datetime import timedelta
from statistics import mean

import os

version = '0.2a'

# SettingError ################################################################
class SettingError(Exception):
    pass

# NoResponsesError ############################################################
class NoResponsesError(Exception):
    pass

# CSVError ####################################################################
class CSVError(Exception):
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
        
        # If a row contains 'Cue' and 'Response', it is designated as the column header row.
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
    settings = MtSettings()

    # Initialize SQLite
    conn = sqlite3.connect(':memory:')

    # Initialize indices dictionary
    indices = dict()
    indices['cue'] = []
    indices['response'] = []
    indices['synonym'] = []
    indices['tag'] = []
    indices['mtag'] = []

    set_csv_settings(settings, csv_list)
    get_csv_column_indices(indices, csv_list)
    csv_column_header_row_number = get_csv_column_header_row_number(csv_list)
    data_list = csv_list[csv_column_header_row_number+1:]

    # Create tables ###########################################################
    conn.execute('''CREATE TABLE cues
                 (cue_id INTEGER PRIMARY KEY,
                 cue TEXT)''')

    conn.execute('''CREATE TABLE responses
                 (response_id INTEGER PRIMARY KEY,
                 response TEXT)''')

    conn.execute('''CREATE TABLE cues_to_responses
                 (cue_id INTEGER,
                 response_id INTEGER,
                 placement INTEGER,
                 PRIMARY KEY (cue_id, response_id))''')

    conn.execute('''CREATE TABLE synonyms
                 (synonym_id INTEGER PRIMARY KEY,
                 synonym TEXT)''')

    conn.execute('''CREATE TABLE responses_to_synonyms
                 (response_id INTEGER,
                 synonym_id INTEGER,
                 PRIMARY KEY (response_id, synonym_id))''')

    conn.execute('''CREATE TABLE tags
                 (tag_id INTEGER PRIMARY KEY,
                 tag TEXT)''')

    conn.execute('''CREATE TABLE responses_to_tags
                 (response_id INTEGER,
                 tag_id INTEGER,
                 PRIMARY KEY (response_id, tag_id))''')

    conn.execute('''CREATE TABLE mtags
                 (mtag_id INTEGER PRIMARY KEY,
                 mtag TEXT)''')

    conn.execute('''CREATE TABLE responses_to_mtags
                 (response_id INTEGER,
                 mtag_id INTEGER,
                 PRIMARY KEY (response_id, mtag_id))''')

    # Save changes
    conn.commit()

    # Populate the database with data #########################################

    # cues table
    cue_list = []

    for data_row in data_list:
        cue = data_row[indices['cue'][0]]
        if cue not in cue_list:
            conn.execute('''INSERT INTO cues(cue)
                         VALUES (?)''', (cue, ))
            cue_list.append(cue)

    # responses table
    response_list = []

    for data_row in data_list:
        for index in indices['response']:
            response = data_row[index]
            # Add response only if it's not empty and hasn't been added before.
            if response and response not in response_list:
                conn.execute('''INSERT INTO responses(response)
                             VALUES (?)''', (response, ))
                response_list.append(response)

    # cues_to_response table
    all_cues = []

    for data_row in data_list:
        # Get the cue_id
        cue = data_row[indices['cue'][0]]
        cue_id = cue_list.index(cue) + 1
        
        # Get the response_id
        for placement, index in enumerate(indices['response']):
            response = data_row[index]

            if response:
                response_id = response_list.index(response) + 1

                # To determine placement, see if this cue has come up before.
                all_cues.append(cue_id)
                placement = len([i for i in all_cues if i == cue_id])

                conn.execute('''INSERT INTO cues_to_responses(cue_id, response_id, placement)
                            VALUES (?,?,?)''', (cue_id, response_id, placement))

    # synonyms table
    synonym_list = []

    for number, data_row in enumerate(data_list):
        for index in indices['synonym']:
            synonym = data_row[index]
            # Add row only if it's not empty
            if synonym and synonym not in synonym_list:
                conn.execute('''INSERT INTO synonyms(synonym)
                             VALUES (?)''', (synonym, ))
                synonym_list.append(synonym)

    # responses_to_synonyms table
    responses_to_synonyms_list = []

    for data_row in data_list:
        # Get the response_id
        for placement, index in enumerate(indices['response']):
            response = data_row[index]

            if response:
                response_id = response_list.index(response) + 1

                # Get the synonym_id
                synonym = data_row[indices['synonym'][placement]]

                if synonym:
                    synonym_id = synonym_list.index(synonym) + 1
                    pair = (response_id, synonym_id)

                    if pair not in responses_to_synonyms_list:
                        conn.execute('''INSERT INTO responses_to_synonyms(response_id, synonym_id)
                                    VALUES (?,?)''', pair)
                        responses_to_synonyms_list.append(pair)

    # tags table
    tag_list = []

    for number, data_row in enumerate(data_list):
        for index in indices['tag']:
            tag = data_row[index]
            # Add row only if it's not empty
            if tag and tag not in tag_list:
                conn.execute('''INSERT INTO tags(tag)
                             VALUES (?)''', (tag, ))
                tag_list.append(tag)

    # responses_to_tags table
    responses_to_tag_list = []

    for data_row in data_list:
        # Get the response_id
        for placement, index in enumerate(indices['response']):
            response = data_row[index]

            if response:
                response_id = response_list.index(response) + 1

                # Get the tag_id
                # Only one tag placement per cue
                for tag_index in indices['tag']:
                    tag = data_row[tag_index]

                    if tag:
                        tag_id = tag_list.index(tag) + 1
                        pair = (response_id, tag_id)

                        if pair not in responses_to_tag_list:
                            conn.execute('''INSERT INTO responses_to_tags(response_id, tag_id)
                                        VALUES (?,?)''', pair)
                            responses_to_tag_list.append(pair)

    # mtags table
    mtag_list = []

    for number, data_row in enumerate(data_list):
        for index in indices['mtag']:
            mtag = data_row[index]
            # Add row only if it's not empty
            if mtag and mtag not in mtag_list:
                conn.execute('''INSERT INTO mtags(mtag)
                             VALUES (?)''', (mtag, ))
                mtag_list.append(mtag)

    # responses_to_mtags table
    responses_to_mtag_list = []

    for data_row in data_list:
        # Get the response_id
        for placement, index in enumerate(indices['response']):
            response = data_row[index]

            if response:
                response_id = response_list.index(response) + 1

                # Get the mtag_id
                # Only one mtag placement per cue
                for mtag_index in indices['mtag']:
                    mtag = data_row[mtag_index]

                    if mtag:
                        mtag_id = mtag_list.index(mtag) + 1
                        pair = (response_id, mtag_id)

                        if pair not in responses_to_mtag_list:
                            conn.execute('''INSERT INTO responses_to_mtags(response_id, mtag_id)
                                        VALUES (?,?)''', pair)
                            responses_to_mtag_list.append(pair)

    # Save changes
    conn.commit()

    # Helper methods ##########################################################
    def memtrain_query(columns, tables):
        cur = conn.cursor()
        cur.execute('''SELECT {} FROM {}'''.format(columns, tables))
        rows = cur.fetchall()
        columns = len(columns.split(','))
        if columns == 1:
            rows = list(map(lambda x: x[0], rows))

        return rows

    def get_all_responses():
        return memtrain_query('response', 'responses')

    def get_all_response_ids():
        return memtrain_query('response_id', 'responses')

    def get_all_response_ids_by_tag(tag):
        cur = conn.cursor()
        cur.execute('''SELECT tag_id FROM tags
                     WHERE tag = (?)''', (str(tag), ))
        rows = cur.fetchall()
        tag_id = rows[0][0]
        cur.execute('''SELECT response_id FROM responses_to_tags
                     WHERE tag_id = (?)''', (str(tag_id), ))
        rows = cur.fetchall()
        rows = list(map(lambda x: x[0], rows))

        return rows

    def get_all_cue_response_id_pairs():
        return memtrain_query('cue_id, response_id', 'cues_to_responses')

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
    responses = get_all_responses()
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
    cr_id_pairs = get_all_cue_response_id_pairs()

    # Filter out other tags if tags were specified on the command line.
    if args.tags:
        these_response_ids = []
        args_tags = args.tags.split(',')
        for tag in args_tags:
            these_response_ids += get_all_response_ids_by_tag(tag)
        these_response_ids = list(set(these_response_ids))
        cr_id_pairs = [i for i in cr_id_pairs if i[1] in these_response_ids]

    # List of times
    times = []

    # Inter-area margin for printing purposes
    iam = ' '

    # If nquestions is not 0, add necessary responses or remove responses.
    nquestions = settings.settings['nquestions']

    if nquestions is not 0:
        total = len(cr_id_pairs)

        # If nquestions is greater than the total number of questions,
        # duplicate them at random until nquestions is reached.
        if nquestions > total:
            add = nquestions - total
            new_cr_id_pairs = list(cr_id_pairs)

            for i in range(add):
                new_response_ids.append(random.choice(cr_id_pairs))
            
            cr_id_pairs = list(new_cr_id_pairs)
        # If nquestions is less than the total number of questions, choose the
        # questions at random until we have another.
        elif nquestions < total:
            random.shuffle(cr_id_pairs)
            new_cr_id_pairs= []
            for i in range(nquestions):
                new_cr_id_pairs.append(cr_id_pairs[i])
            
            cr_id_pairs = list(new_cr_id_pairs)
        # If nquestions is equal to the total number of questions, don't do
        # anything.

    # Shuffle database
    random.shuffle(cr_id_pairs)

    # Initialize statistics
    correct = 0
    incorrect = 0
    response_number = 1
    total = len(cr_id_pairs)

    # Raise NoResponsesError if there are no responses available.
    if total == 0:
        raise NoResponsesError('There are no responses available that match the criteria.')

    # Prompt helper methods ###################################################
    cur = conn.cursor()

    def memtrain_get_value(value, value_id):
        cur.execute('''SELECT {} FROM {} WHERE {} = (?)'''.format(value, value + 's', value + '_id'), (str(value_id), ))
        rows = cur.fetchall()
        return rows[0][0]

    def get_cue(cue_id):
        return memtrain_get_value('cue', cue_id)

    def get_response(response_id):
        return memtrain_get_value('response', response_id)

    def get_mtags(response_id):
        cur.execute('''SELECT mtag_id FROM responses_to_mtags WHERE response_id = (?)''', (str(response_id), ))
        rows = cur.fetchall()
        rows = list(map(lambda x: x[0], rows))

        out = []

        for mtag_id in rows:
            out.append(memtrain_get_value('mtag', mtag_id))

        return out

    def get_placement(cue_id, response_id):
        cur.execute('''SELECT placement FROM cues_to_responses WHERE cue_id = (?) AND response_id = (?)''', (str(cue_id), str(response_id)))
        rows = cur.fetchall()
        return rows[0][0]

    def get_responses_by_mtag(mtag):
        cur.execute('''SELECT mtag_id FROM mtags WHERE mtag = (?)''', (mtag, ))
        rows = cur.fetchall()
        rows = list(map(lambda x: x[0], rows))

        response_ids = []

        for mtag_id in rows:
            cur.execute('''SELECT response_id FROM responses_to_mtags WHERE mtag_id = (?)''', (mtag_id, ))
            rows = cur.fetchall()
            response_ids.append(rows[0][0])

        out = []

        for response_id in response_ids:
            out.append(memtrain_get_value('response', response_id))

        return out

    def is_plural(string):
        return string[-1] == 's'

    plural_responses = [i for i in responses if is_plural(i)]
    nonplural_responses = [i for i in responses if not is_plural(i)]

    # Prompts #################################################################
    for cue_id, response_id in cr_id_pairs:
        cue = get_cue(cue_id)
        response = get_response(response_id)
        placement = get_placement(cue_id, response_id)
        # hints = response_id_to_hints(response_id)
        mtags = get_mtags(response_id)
        # Get number of mtags
        n_mtags = len(mtags)

        # Format the cue
        f_cue = cue.replace('{{}}', '_' * 9)

        if placement == 1:
            f_cue = f_cue.replace('{{1}}', '___(1)___')
        else:
            f_cue = f_cue.replace('{{1}}', '_' * 9)
        if placement == 2:
            f_cue = f_cue.replace('{{2}}', '___(2)___')
        else:
            f_cue = f_cue.replace('{{2}}', '_' * 9)
        if placement == 3:
            f_cue = f_cue.replace('{{3}}', '___(3)___')
        else:
            f_cue = f_cue.replace('{{3}}', '_' * 9)

        f_cue = textwrap.fill(f_cue, initial_indent=' ' * 6, subsequent_indent=' ' * 6, width=80)

        # Print how questions were answered correctly so far if we are not on
        # the first question.
        if response_number is not 1:
            percentage = decimal.Decimal(correct) / decimal.Decimal(response_number-1) * decimal.Decimal(100)

        # Determine the level
        if settings.settings['level1']:
            level = 'Level 1'
        elif settings.settings['level2']:
            level = 'Level 2'
        elif settings.settings['level3']:
            level = 'Level 3'

        def print_header():
            # Print the program header.
            print(('memtrain '+ version).ljust(69) + iam + level.rjust(10))
            print()

        print_header()

        # Print first two rows and the cue.
        print(settings.settings['title'].ljust(59) + iam + ('Response ' + str(response_number) + '/' + str(total)).rjust(20))
        if response_number is not 1:
            print('Correct so far'.ljust(59) + iam + (str(correct) + '/' + str(response_number-1) + ' (' + str(round(percentage, 1)) + '%)').rjust(20))
        print()
        print(f_cue)
        print()

        # If on level one, generate the multiple choice questions.
        if settings.settings['level1']:
            # Get responses for all mtags for this response
            same_mtag_responses = []

            for mtag in mtags:
                same_mtag_responses += get_responses_by_mtag(mtag)

            # Get responses of the same and the other plurality
            plurality = is_plural(response)

            same_plurality_responses = list(plural_responses) if plurality else list(nonplural_responses)
            other_plurality_responses = list(nonplural_responses) if plurality else list(plural_responses)

            # We will select first from same_mtag_responses. Then, if
            # that's empty, we'll select from same_plurality_responses. If
            # that's also empty, we'll resort to other_plurality_responses.

            # Filter all three of these lists to make sure they don't contain
            # the correct response
            same_mtag_responses = [i for i in same_mtag_responses if i != response]
            same_plurality_responses = [i for i in same_plurality_responses if i != response]
            # The response won't be located in other_plurality_responses.

            # Filter the pluarlity_responses lists
            same_plurality_responses = [i for i in same_plurality_responses if i not in same_mtag_responses]
            other_plurality_responses = [i for i in other_plurality_responses if i not in same_mtag_responses]

            # Shuffle the response lists.
            random.shuffle(same_mtag_responses)
            random.shuffle(same_plurality_responses)
            random.shuffle(other_plurality_responses)

            # Get our ascii range for the multiple choice questions
            ascii_range = string.ascii_lowercase[:4]
            # Get the index of the correct answer.
            correct_letter = random.choice(ascii_range)

            response_pool_consumption_index = 0
            response_pool = same_mtag_responses

            # Loop through the ascii range
            for i in ascii_range:
                # If we have the correct letter, output the correct response.
                if i == correct_letter:
                    this_response = response
                # Otherwise...
                else:
                    # If the response_pool is empty...
                    while len(response_pool) == 0:
                        response_pool_consumption_index = response_pool_consumption_index + 1

                        if response_pool_consumption_index == 1:
                            response_pool = same_plurality_responses
                        elif response_pool_consumption_index == 2:
                            response_pool = other_plurality_responses
                        elif response_pool_consumption_index > 2:
                            raise NoResponsesError('There are no more responses available.')

                    this_response = response_pool.pop()
                # Capitalize only the first letter of this_response
                this_response = this_response[0].upper() + this_response[1:]
                # Now that we have our response, print it
                f_response = textwrap.fill(this_response, initial_indent=i + ')' + ' ' * 4, subsequent_indent=' ' * 6, width=80)
                print(f_response)

            print()
        
        elif settings.settings['level2']:
            for hint in hints:
                # Print hint only if it is not empty.
                if len(hint) != 0:
                    # Format hint to match cue.
                    f_hint = textwrap.fill('Hint: ' + hint, subsequent_indent=' ' * 6, width=80)
                    print(f_hint)
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

        # Validate input.
        if settings.settings['level1']:
            # For level 1, check to see if the right letter was entered.
            correct_user_input = correct_letter == user_input
        elif settings.settings['level2'] or settings.settings['level3']:
            # For levels 2 or 3, make sure the right alias was entered.
            if user_input in aliases.keys():
                correct_user_input = response.lower() == user_input.lower() or response == aliases[user_input.lower()]
            else:
                correct_user_input = response.lower() == user_input.lower()

        # Perform actions based on correctness.
        if correct_user_input:
            print('Correct.')
            correct = correct + 1
        else:
            print('Incorrect. Answer: ' + response)
            incorrect = incorrect + 1
        print()
        response_number = response_number + 1 

    # Print statistics ########################################################
    decimal.getcontext().prec = 5
    percentage = decimal.Decimal(correct) / decimal.Decimal(total) * decimal.Decimal(100)

    print_header()
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
parser.add_argument('-n', '--nquestions', type=int, help='Set the number of questions for this session')
parser.add_argument('csvfile', help='The CSV file to load')

# Parse arguments
args = parser.parse_args()
args.func(args)
