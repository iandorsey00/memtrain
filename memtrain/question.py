import decimal
import random
import string
import textwrap
import time

import os

class Question:
    '''Manages the current cue and response interface'''
    def __init__(self, settings, database):
        self.settings = settings
        self.conn = database.conn
        self.cur = self.conn.cursor()
        self.database = database

        self.responses = self.database.get_all_responses()

        self.cue_id = 0
        self.response_id = 0
        self.f_cue = ''
        self.mtags = []
        self.mchoices = []

        self.mtstatistics = None

        self.iam = ' '
        self.ascii_range = ['a', 'b', 'c', 'd']

        self.response = ''
        self.user_input = ''
        self.synonyms = []

        self.plural_responses = [i for i in self.responses if self.is_plural(i)]
        self.nonplural_responses = [i for i in self.responses if not self.is_plural(i)]

    def get_value(self, value, value_id):
        self.cur.execute('''SELECT {} FROM {} WHERE {} = (?)'''
                         .format(value, value + 's', value + '_id'),
                         (str(value_id), ))
        rows = self.cur.fetchall()
        return rows[0][0]

    def get_cue(self, cue_id):
        return self.get_value('cue', cue_id)

    def get_response(self, response_id):
        return self.get_value('response', response_id)

    def get_hints(self):
        # Translate response_id into hint_id
        self.cur.execute('''SELECT hint_id FROM responses_to_hints
                         WHERE response_id = (?)''', (str(self.response_id), ))
        rows = self.cur.fetchall()
        rows = list(map(lambda x: x[0], rows))

        out = []

        # Translate hint_id to hint
        for hint_id in rows:
            out.append(self.get_value('hint', hint_id))

        return out

    def get_synonyms(self):
        # Translate response_id into synonym_id
        self.cur.execute('''SELECT synonym_id FROM responses_to_synonyms
                         WHERE response_id = (?)''', (str(self.response_id), ))
        rows = self.cur.fetchall()
        rows = list(map(lambda x: x[0], rows))

        out = []

        # Translate synonym_id to synonym
        for synonym_id in rows:
            out.append(self.get_value('synonym', synonym_id))

        return out

    def get_mtags(self):
        # Translate response_id into mtag_id
        self.cur.execute('''SELECT mtag_id FROM responses_to_mtags
                         WHERE response_id = (?)''', (str(self.response_id), ))
        rows = self.cur.fetchall()
        rows = list(map(lambda x: x[0], rows))

        out = []

        # Translate mtag_id to mtag
        for mtag_id in rows:
            out.append(self.get_value('mtag', mtag_id))

        return out

    def get_placement(self, cue_id, response_id):
        self.cur.execute('''SELECT placement FROM cues_to_responses
                         WHERE cue_id = (?) AND response_id = (?)''',
                         (str(cue_id), str(response_id)))
        rows = self.cur.fetchall()
        return rows[0][0]

    def get_responses_by_mtag(self, mtag):
        # Translate mtag_id to mtag
        self.cur.execute('''SELECT mtag_id FROM mtags WHERE mtag = (?)''',
                         (mtag, ))
        rows = self.cur.fetchall()
        rows = list(map(lambda x: x[0], rows))

        # Translate mtag_id to response_id
        response_ids = []

        for mtag_id in rows:
            self.cur.execute('''SELECT response_id FROM responses_to_mtags
                             WHERE mtag_id = (?)''', (mtag_id, ))
            more_rows = self.cur.fetchall()
            response_ids += list(map(lambda x: x[0], more_rows))

        # Translate response_id to response
        out = []

        for response_id in response_ids:
            out.append(self.get_value('response', response_id))

        return out

    def is_plural(self, string):
        return string[-1] == 's'

    # Question rendering ######################################################
    def format_cue(self):
        self.f_cue = self.cue.replace('{{}}', '_' * 9)

        if self.placement == 1:
            self.f_cue = self.f_cue.replace('{{1}}', '___(1)___')
        else:
            self.f_cue = self.f_cue.replace('{{1}}', '_' * 9)
        if self.placement == 2:
            self.f_cue = self.f_cue.replace('{{2}}', '___(2)___')
        else:
            self.f_cue = self.f_cue.replace('{{2}}', '_' * 9)
        if self.placement == 3:
            self.f_cue = self.f_cue.replace('{{3}}', '___(3)___')
        else:
            self.f_cue = self.f_cue.replace('{{3}}', '_' * 9)

        return textwrap.fill(self.f_cue, initial_indent=' ' * 6,
                                    subsequent_indent=' ' * 6, width=80)

    def print_header(self, final=False):
        '''Print the question header.'''

        # Determine the level
        if self.settings.settings['level1']:
            level = 'Level 1'
        elif self.settings.settings['level2']:
            level = 'Level 2'
        elif self.settings.settings['level3']:
            level = 'Level 3'

        # Print the first row - version and level
        print(('memtrain ' + self.settings.version).ljust(69) + self.iam + level.rjust(10))
        print()

        if final:
            # Just print the title
            print(self.settings.settings['title'])
        else:
            # Print the second row - title and number of responses
            title_block = self.settings.settings['title'].ljust(59)
            responses_block = ('Response ' + str(self.mtstatistics.response_number) + '/' + str(self.mtstatistics.total)).rjust(20)

            print(title_block + self.iam + responses_block)

            # Print the third row if we are not on the first response - statistics
            # regarding the number of problems right so far.
            if self.mtstatistics.response_number is not 1:
                label_block = 'Correct so far'.ljust(59)
                statistics_block = (str(self.mtstatistics.number_correct) + '/' + str(self.mtstatistics.response_number-1) + ' (' + str(round(self.mtstatistics.percentage, 1)) + '%)').rjust(20)
                print(label_block + self.iam + statistics_block)

    def generate_mchoices(self):
        '''Return the choices for the multiple choice questions'''
        out = dict()

        # Get responses for all mtags for this response
        same_mtag_responses = []

        for mtag in self.mtags:
            same_mtag_responses += self.get_responses_by_mtag(mtag)

        # Get responses of the same and the other plurality
        plurality = self.is_plural(self.response)

        same_plurality_responses = list(self.plural_responses) if plurality else list(self.nonplural_responses)
        other_plurality_responses = list(self.nonplural_responses) if plurality else list(self.plural_responses)

        # We will select first from same_mtag_responses. Then, if
        # that's empty, we'll select from same_plurality_responses. If
        # that's also empty, we'll resort to other_plurality_responses.

        # Filter all three of these lists to make sure they don't contain
        # the correct response
        same_mtag_responses = [i for i in same_mtag_responses if i != self.response]
        same_plurality_responses = [i for i in same_plurality_responses if i != self.response]
        # The response won't be located in other_plurality_responses.

        # Filter the pluarlity_responses lists
        same_plurality_responses = [i for i in same_plurality_responses if i not in same_mtag_responses]
        other_plurality_responses = [i for i in other_plurality_responses if i not in same_mtag_responses]

        # Shuffle the response lists.
        random.shuffle(same_mtag_responses)
        random.shuffle(same_plurality_responses)
        random.shuffle(other_plurality_responses)

        # Get the index of the correct answer.
        correct_letter = random.choice(self.ascii_range)

        response_pool_consumption_index = 0
        response_pool = same_mtag_responses

        # Loop through the ascii range
        for i in self.ascii_range:
            # If we have the correct letter, output the correct response.
            if i == correct_letter:
                this_response = self.response
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
            # Now that we have our choice, insert it into self.mchoices
            out[i] = this_response

        return out

    def print_hints(self):
        for hint in self.hints:
            if hint:
                # Format hint to match cue.
                f_hint = textwrap.fill('Hint: ' + hint, subsequent_indent=' ' * 6, width=80)
                print(f_hint)

    def print_mchoices(self):
        '''Print the multiple choices for Level 1'''
        for letter, choice in self.mchoices.items():
            this_line = textwrap.fill(choice,
                                      initial_indent=letter + ')' + (' ' * 4),
                                      subsequent_indent=' ' * 6, width=80)
            print(this_line)

    def prompt_for_response(self):
        '''Prompt for a response and return user input'''
        if self.settings.settings['level1']:
            self.user_input = input('Enter response choice: ')
        else:
            self.user_input = input('Enter response: ')

        self.user_input = self.user_input.lower()

    def validate_input(self):
        self.mtstatistics.is_input_valid = False

        if self.settings.settings['level1']:
            if self.user_input in self.ascii_range:
                self.mtstatistics.is_input_valid = True
        else:
            if self.user_input:
                self.mtstatistics.is_input_valid = True

    def standardize_string(self, string):
        '''Standardize strings so they can be compared for correctness'''
        # The idea here is that a question shouldn't be marked wrong just
        # because the user forgot to enter a hyphen or a space or used the
        # wrong case.
        #
        # Standarization involves the removal of all case, whitespace, and
        # hyphens. This means the grading of questions is not case, whitespace,
        # or hyphen sensitive.
        
        # Remove case (transform to lowercase)
        out = string.lower()
        # Remove whitespace
        out = ''.join(out.split())
        # Remove hyphens
        out = out.replace('-', '')
        out = out.replace('–', '')
        out = out.replace('—', '')

        return out

    def determine_equivalence(self):
        '''See if input matches a synonym or standarized string'''
        self.mtstatistics.is_input_correct = False
        
        # If not, does the input match the response?
        std_input = self.standardize_string(self.user_input)
        std_response = self.standardize_string(self.response)

        if std_input == std_response:
            self.mtstatistics.used_response = self.response
            self.mtstatistics.is_input_correct = True

        if not self.mtstatistics.is_input_correct:
            # If not, does the input match a synonym?
            for synonym in self.synonyms:
                std_synonym = self.standardize_string(synonym)
                if std_input == std_synonym:
                    self.mtstatistics.used_synonym = synonym
                    self.mtstatistics.is_input_correct = True

    def grade_input(self):
        '''Determine whether input is correct.'''
        if self.settings.settings['level1']:
            # For level 1, check to see if the right letter was entered.
            # First, translate the letter to its corresponding choice.
            self.user_input = self.mchoices[self.user_input]
            self.mtstatistics.is_input_correct = self.response.lower() == self.user_input.lower()
        elif self.settings.settings['level2'] or self.settings.settings['level3']:
            # For levels 2 or 3, make sure the right input was entered.
            self.determine_equivalence()
    
    def finalize(self):
        '''Notify the user of correctness, update statistics, and print'''
        if self.mtstatistics.is_input_correct:
            self.mtstatistics.number_correct += 1
            if self.mtstatistics.has_synonym_been_used():
                remaining_synonyms = [i for i in self.synonyms if i != self.mtstatistics.used_synonym]
                default_answer_str = 'Correct. Default answer: ' + self.response
                other_correct_responses_str = 'Other correct responses: ' + ', '.join(remaining_synonyms)
                f_default_answer_str = textwrap.fill(default_answer_str, width=80)
                f_other_correct_responses_str = textwrap.fill(other_correct_responses_str, width=80)

                print(f_default_answer_str)

                if remaining_synonyms:
                    print(f_other_correct_responses_str)
                else:
                    print()
            else:
                print('Correct.')
                other_correct_responses_str = 'Other correct responses: ' + ', '.join(self.synonyms)
                f_other_correct_responses_str = textwrap.fill(other_correct_responses_str, width=80)

                if self.synonyms:
                    print(f_other_correct_responses_str)
                else:
                    print()

        else:
            self.mtstatistics.number_incorrect += 1
            self.mtstatistics.incorrect_responses.append(self.response)
            print('Incorrect. Answer: ' + self.response)

            other_correct_responses_str = 'Other correct responses: ' + ', '.join(self.synonyms)
            f_other_correct_responses_str = textwrap.fill(other_correct_responses_str, width=80)
            
            if self.synonyms:
                print(f_other_correct_responses_str)
            else:
                print()

        print()

        self.mtstatistics.response_number += 1

        # Reset
        self.mtstatistics.used_synonym = ''

    def render_question(self, cue_id, response_id, mtstatistics):
        '''Render the question'''
        self.mtstatistics = mtstatistics

        is_last_question = self.cue_id == cue_id and self.response_id == response_id

        if not is_last_question:
            self.cue_id = cue_id
            self.response_id = response_id

            self.cue = self.get_cue(self.cue_id)
            self.response = self.get_response(self.response_id)
            self.placement = self.get_placement(self.cue_id, self.response_id)
            self.synonyms = self.get_synonyms()
            self.hints = self.get_hints()
            self.mtags = self.get_mtags()
            self.mtstatistics.update_percentage()

            # If on Level 1, generate the multiple choice questions.
            if self.settings.settings['level1']:
                self.mchoices = self.generate_mchoices()

        self.print_header()

        self.f_cue = self.format_cue()
        print()
        print(self.f_cue)
        print()

        if self.settings.settings['level1']:
            self.print_mchoices()
            print()
        elif self.settings.settings['level2']:
            self.print_hints()
            print()

        # Start time
        start = time.time()

        # Prompt for user input
        self.prompt_for_response()

        # End time
        end = time.time()
        elasped_time = end - start

        self.validate_input()

        # Clear screen.
        os.system('clear')

        if mtstatistics.is_input_valid:
            self.grade_input()
            self.mtstatistics.times.append(elasped_time)
            self.finalize()
        else:
            print('Please enter a valid response.')
            print()
    