import textwrap

from decimal import Decimal


class SessionStatistics:
    '''Keep track of session-level statistics in memtrain.'''

    def __init__(self):
        self.response_number = 1
        self.number_correct = 0
        self.number_incorrect = 0
        self.percentage = 0.0
        self.total = 0

        self.is_input_valid = False
        self.is_input_correct = False

        self.times = []
        self.used_response = ''
        self.used_synonym = ''
        self.incorrect_responses = []

    def update_percentage(self):
        '''Update the percentage answered correctly so far.'''
        if self.response_number == 1:
            self.percentage = 0.0
            return

        self.percentage = (
            Decimal(self.number_correct)
            / Decimal(self.response_number - 1)
            * Decimal(100)
        )

    def has_synonym_been_used(self):
        return bool(self.used_synonym)

    def incorrect_responses_as_string(self):
        return ', '.join(self.incorrect_responses)

    def is_last_question(self):
        return self.response_number > self.total

    def formatted_incorrect_responses(self):
        return textwrap.fill(
            self.incorrect_responses_as_string(),
            initial_indent=' ' * 6,
            subsequent_indent=' ' * 6,
            width=80,
        )


# Backward-compatible name for existing imports.
MtStatistics = SessionStatistics
