import argparse

from datetime import timedelta
from statistics import mean

from memtrain.memtrain_common.engine import Engine
from memtrain.memtrain_common.question import Question

def train(args):
    engine = Engine('', '', '', '', '')

    settings = engine.settings
    database = engine.database
    mtstatistics = engine.mtstatistics
    cr_id_pairs = engine.cr_id_pairs

    question = Question(settings, database)

    for cr_id_pair in cr_id_pairs:
        mtstatistics.is_input_valid = False

        # Don't continue with the loop until a valid response has been
        # entered.
        while not mtstatistics.is_input_valid:
            question.render_question(cr_id_pair[0], cr_id_pair[1], mtstatistics)

    mtstatistics.update_percentage()

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



    # def print_hints(self):
    #     for hint in self.hints:
    #         if hint:
    #             # Format hint to match cue.
    #             f_hint = textwrap.fill('Hint: ' + hint, subsequent_indent=' ' * 6, width=80)
    #             print(f_hint)

    # def print_mchoices(self):
    #     '''Print the multiple choices for Level 1'''
    #     for letter, choice in self.mchoices.items():
    #         this_line = textwrap.fill(choice,
    #                                   initial_indent=letter + ')' + (' ' * 4),
    #                                   subsequent_indent=' ' * 6, width=80)
    #         print(this_line)

    # def render_question(self, cue_id, response_id, mtstatistics):
    #     '''Render the question'''
    #     # self.mtstatistics = mtstatistics

    #     is_last_question = self.cue_id == cue_id and self.response_id == response_id

    #     if not is_last_question:
    #         self.cue_id = cue_id
    #         self.response_id = response_id

    #         self.cue = self.get_cue(self.cue_id)
    #         self.response = self.get_response(self.response_id)
    #         self.placement = self.get_placement(self.cue_id, self.response_id)
    #         self.synonyms = self.get_synonyms()
    #         self.hints = self.get_hints()
    #         self.mtags = self.get_mtags()
    #         self.mtstatistics.update_percentage()

    #         # If on Level 1, generate the multiple choice questions.
    #         if self.settings.settings['level1']:
    #             self.mchoices = self.generate_mchoices()

    #     self.header_text()

    #     self.f_cue = self.format_cue()
    #     self.cue_text = self.f_cue
    #     print()
    #     print(self.f_cue)
    #     print()

    #     if self.settings.settings['level1']:
    #         self.print_mchoices()
    #         print()
    #     elif self.settings.settings['level2']:
    #         self.print_hints()
    #         print()

    #     # Start time
    #     start = time.time()

    #     # Prompt for user input
    #     self.prompt_for_response()

    #     # End time
    #     end = time.time()
    #     elasped_time = end - start

    #     self.validate_input()

    #     # Clear screen.
    #     os.system('cls')

    #     if mtstatistics.is_input_valid:
    #         self.grade_input()
    #         self.mtstatistics.times.append(elasped_time)
    #         self.finalize()
    #     else:
    #         print('Please enter a valid response.')
    #         print()

###############################################################################
# Argument parsing with argparse

# Create the top-level argument parser
parser = argparse.ArgumentParser(
    description='A program for better memory training')
parser.set_defaults(func=train)

# Create arguments
parser.add_argument('-t', '--tags', help='Train these tags only')
parser.add_argument('-x', '--not-tags', help='Do not train these tags')
parser.add_argument('-l', '--level', help='Specify which level to study')
parser.add_argument('-n', '--nquestions', type=int, help='Set the number of questions for this session')
parser.add_argument('csvfile', help='The CSV file to load')

# Parse arguments
args = parser.parse_args()
args.func(args)