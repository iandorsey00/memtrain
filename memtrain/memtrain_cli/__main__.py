import argparse

from datetime import timedelta
from statistics import mean

import memtrain.memtrain_common.engine as engine

from memtrain.memtrain_common.question import Question

def train(args):
    settings, database, mtstatistics, cr_id_pairs = engine.train(args)

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