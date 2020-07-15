import textwrap
from decimal import Decimal

class MtStatistics:
    '''Keep track of statistics in memtrain'''
    def __init__(self):
        self.response_number = 1
        self.number_correct = 0
        self.number_incorrect = 0
        self.percentage = 0.0
        self.total = 0

        self.is_input_valid = False
        self.is_input_correct = False

        self.times = []

        self.incorrect_responses = []

    def update_percentage(self):
        '''Update percent of problems answered correctly so far'''
        if self.response_number != 1:
            self.percentage = Decimal(self.number_correct) \
                              / Decimal(self.response_number-1) * Decimal(100)
        else:
            self.percentage = 0.0

    def formatted_incorrect_responses(self):
        incorrect_responses_str = ', '.join(self.incorrect_responses)
        f_incorrect_responses = textwrap.fill(incorrect_responses_str,
                                              initial_indent=' ' * 6,
                                              subsequent_indent=' ' * 6,
                                              width=80)
        return f_incorrect_responses
