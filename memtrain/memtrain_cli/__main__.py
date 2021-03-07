import argparse
import time
import textwrap
import os

from datetime import timedelta
from statistics import mean

from memtrain.memtrain_common.engine import Engine
from memtrain.memtrain_common.question import Question

class MemtrainCLI():
    def __init__(self):
        self.engine = None

        self.settings = None
        self.database = None
        self.mtstatistics = None
        self.cr_id_pairs = None

        self.question = None

        self.cue_id = None
        self.response_id = None

        self.cue = None
        self.response = None
        self.placement = None
        self.synonyms = None
        self.hints = None
        self.mtags = None
        self.mchoices = None

        # Inter-area margin
        self.iam = ' '

        #######################################################################
        # Argument parsing with argparse

        # Create the top-level argument parser
        parser = argparse.ArgumentParser(
            description='A program for better memory training')
        parser.set_defaults(func=self.train)

        # Create arguments
        parser.add_argument('-t', '--tags', help='Train these tags only')
        parser.add_argument('-x', '--not-tags', help='Do not train these tags')
        parser.add_argument('-l', '--level', help='Specify which level to study')
        parser.add_argument('-n', '--nquestions', type=int, help='Set the number of questions for this session')
        parser.add_argument('csvfile', help='The CSV file to load')

        # Parse arguments
        self.args = parser.parse_args()
        self.args.func(self.args)

    def train(self, args):
        # Read arguments
        self.csvfile = self.args.csvfile
        self.level = self.args.level
        self.nquestions = self.args.nquestions
        self.tags = self.args.tags
        self.not_tags = self.args.not_tags

        self.engine = Engine(self.csvfile, self.level, self.nquestions, self.tags, self.not_tags)

        self.settings = self.engine.settings
        self.database = self.engine.database
        self.mtstatistics = self.engine.mtstatistics
        self.cr_id_pairs = self.engine.cr_id_pairs

        self.question = Question(self.settings, self.database)

        for cr_id_pair in self.cr_id_pairs:
            self.mtstatistics.is_input_valid = False

            # Don't continue with the loop until a valid response has been
            # entered.
            while not self.mtstatistics.is_input_valid:
                self.render_question(cr_id_pair[0], cr_id_pair[1])
                pass

        self.mtstatistics.update_percentage()

        self.header_text()
        print()
        print('Training session complete.')
        print()
        print('Correct: ' + str(self.mtstatistics.number_correct) + '/' + str(self.mtstatistics.total) + ' (' + str(round(self.mtstatistics.percentage, 1)) + '%)')
        print('Average response time: ' + str(timedelta(seconds=mean(self.mtstatistics.times))))
        print()
        if(self.mtstatistics.number_incorrect > 0):
            print('Responses for which answers were incorrect:')
            print()
            print(self.mtstatistics.formatted_incorrect_responses())
            print()

        # def finalize(self):
        #     '''Notify the user of correctness, update statistics, and print'''
        #     if self.mtstatistics.is_input_correct:
        #         self.mtstatistics.number_correct += 1
        #         if self.mtstatistics.has_synonym_been_used():
        #             remaining_synonyms = [i for i in self.synonyms if i != self.mtstatistics.used_synonym]
        #             default_answer_str = 'Correct. Default answer: ' + self.response
        #             other_correct_responses_str = 'Other correct responses: ' + ', '.join(remaining_synonyms)
        #             f_default_answer_str = textwrap.fill(default_answer_str, width=80)
        #             f_other_correct_responses_str = textwrap.fill(other_correct_responses_str, width=80)

        #             print(f_default_answer_str)

        #             if remaining_synonyms:
        #                 print(f_other_correct_responses_str)
        #             else:
        #                 print()
        #         else:
        #             print('Correct.')
        #             other_correct_responses_str = 'Other correct responses: ' + ', '.join(self.synonyms)
        #             f_other_correct_responses_str = textwrap.fill(other_correct_responses_str, width=80)

        #             if self.synonyms:
        #                 print(f_other_correct_responses_str)
        #             else:
        #                 print()

        #     else:
        #         self.mtstatistics.number_incorrect += 1
        #         self.mtstatistics.incorrect_responses.append(self.response)
        #         print('Incorrect. Answer: ' + self.response)

        #         other_correct_responses_str = 'Other correct responses: ' + ', '.join(self.synonyms)
        #         f_other_correct_responses_str = textwrap.fill(other_correct_responses_str, width=80)
                
        #         if self.synonyms:
        #             print(f_other_correct_responses_str)
        #         else:
        #             print()

        #     print()

        #     self.mtstatistics.response_number += 1

        #     # Reset
        #     self.mtstatistics.used_synonym = ''

    def header_text(self):
        # Print the first row - version and level
        print(('memtrain ' + self.settings.version).ljust(69) + self.iam + self.question.level_text.rjust(10))
        print()

        if self.mtstatistics.is_last_question():
            # Just print the title
            print(self.settings.settings['title'])
        else:
            # Print the second row - title and number of responses
            title_block = self.settings.settings['title'].ljust(59)
            self.response_number_text = 'Response ' + str(self.mtstatistics.response_number) + '/' + str(self.mtstatistics.total)
            responses_block = (self.response_number_text).rjust(20)

            print(title_block + self.iam + responses_block)

            # Print the third row if we are not on the first response - statistics
            # regarding the number of problems right so far.
            if self.mtstatistics.response_number != 1:
                label_block = 'Correct so far'.ljust(59)
                statistics_block = (str(self.mtstatistics.number_correct) + '/' + str(self.mtstatistics.response_number-1) + ' (' + str(round(self.mtstatistics.percentage, 1)) + '%)').rjust(20)
                print(label_block + self.iam + statistics_block)

    def render_question(self, cue_id, response_id):
        '''Render the question'''
        this_question_id = self.mtstatistics.response_number-1
        self.question.main_data_loop(self.cr_id_pairs[this_question_id][0], self.cr_id_pairs[this_question_id][1], self.mtstatistics)

        if not self.mtstatistics.is_last_question():
            self.cue_id = cue_id
            self.response_id = response_id

            self.cue = self.question.get_cue(self.cue_id)
            self.response = self.question.get_response(self.response_id)
            self.placement = self.question.get_placement(self.cue_id, self.response_id)
            self.synonyms = self.question.get_synonyms()
            self.hints = self.question.get_hints()
            self.mtags = self.question.get_mtags()
            self.mtstatistics.update_percentage()

            # If on Level 1, generate the multiple choice questions.
            if self.settings.level == '1':
                self.question.mchoices = self.question.generate_mchoices()

        self.header_text()

        self.f_cue = self.question.format_cue()
        self.f_cue = textwrap.fill(self.f_cue, initial_indent=' ' * 6,
                                   subsequent_indent=' ' * 6, width=80)
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

        self.question.validate_input()

        # Clear screen.
        os.system('cls')

        if self.mtstatistics.is_input_valid:
            self.question.grade_input()
            self.mtstatistics.times.append(elasped_time)
            self.question.finalize()
            f_correctness_str = textwrap.fill(self.question.correctness_str, width=80)
            print(f_correctness_str)

            if self.question.synonyms:
                f_other_answers_str = textwrap.fill(self.question.other_answers_str, width=80)
                print(f_other_answers_str)

            print()
        else:
            print('Please enter a valid response.')
            print()

    def print_hints(self):
        for hint in self.hints:
            if hint:
                # Format hint to match cue.
                f_hint = textwrap.fill('Hint: ' + hint, subsequent_indent=' ' * 6, width=80)
                print(f_hint)

    def print_mchoices(self):
        '''Print the multiple choices for Level 1'''
        for letter, choice in self.question.mchoices.items():
            this_line = textwrap.fill(choice,
                                        initial_indent=letter + ')' + (' ' * 4),
                                        subsequent_indent=' ' * 6, width=80)
            print(this_line)

    def prompt_for_response(self):
        '''Prompt for a response and return user input'''
        if self.settings.settings['level1']:
            self.question.user_input = input('Enter response choice: ')
        else:
            self.question.user_input = input('Enter response: ')

        self.question.user_input = self.question.user_input.lower()

mtcli = MemtrainCLI()
