class Question:
    '''Manages the current cue and response interface'''
    def __init__(self, settings, connection, database):
        self.settings = settings
        self.conn = connection
        self.cur = conn.cursor()
        self.database = database

        self.responses = self.database.get_all_responses()

        self.cue_id = 0
        self.response_id = 0
        self.f_cue = ''
        self.mchoices = []

        self.response_number = 0
        self.number_correct = 0
        self.percentage = 0.0

        self.ascii_range = ['a', 'b', 'c', 'd']

        self.response = ''
        self.user_input = ''

        self.times = []

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
        return self.memtrain_get_value('response', response_id)

    def get_mtags(self, response_id):
        # Translate response_id into mtag_id
        self.cur.execute('''SELECT mtag_id FROM responses_to_mtags
                    WHERE response_id = (?)''', (str(response_id), ))
        rows = self.cur.fetchall()
        rows = list(map(lambda x: x[0], rows))

        out = []

        # Translate mtag_id to mtag
        for mtag_id in rows:
            out.append(self.memtrain_get_value('mtag', mtag_id))

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
            rows = self.cur.fetchall()
            response_ids.append(rows[0][0])

        # Translate response_id to response
        out = []

        for response_id in response_ids:
            out.append(memtrain_get_value('response', response_id))

        return out

    def is_plural(self, string):
        return string[-1] == 's'

    # Question rendering ######################################################
    def format_cue(cue):
        self.f_cue = cue.replace('{{}}', '_' * 9)

        if placement == 1:
            self.f_cue = f_cue.replace('{{1}}', '___(1)___')
        else:
            self.f_cue = self.f_cue.replace('{{1}}', '_' * 9)
        if placement == 2:
            self.f_cue = self.f_cue.replace('{{2}}', '___(2)___')
        else:
            self.f_cue = self.f_cue.replace('{{2}}', '_' * 9)
        if placement == 3:
            self.f_cue = self.f_cue.replace('{{3}}', '___(3)___')
        else:
            self.f_cue = self.f_cue.replace('{{3}}', '_' * 9)

        return textwrap.fill(self.f_cue, initial_indent=' ' * 6,
                                    subsequent_indent=' ' * 6, width=80)

    def get_percentage(self, response_number, correct):
        '''Get percent of problems answered correctly so far'''
        return decimal.Decimal(correct) / decimal.Decimal(response_number-1) * decimal.Decimal(100)

    def print_header(self, settings, response_number, percentage):
        '''Print the question header.'''

        # Determine the level
        if settings.settings['level1']:
            level = 'Level 1'
        elif settings.settings['level2']:
            level = 'Level 2'
        elif settings.settings['level3']:
            level = 'Level 3'

        # Print the first row - version and level
        print(('memtrain ' + settings.version).ljust(69) + iam + level.rjust(10))
        print()

        # Print the second row - title and number of responses
        title_block = settings.settings['title'].ljust(59)
        responses_block = ('Response ' + str(response_number) + '/' + str(total)).rjust(20)

        print(title_block + iam + responses_block)

        # Print the third row if we are not on the first response - statistics
        # regarding the number of problems right so far.
        if response_number is not 1:
            label_block = 'Correct so far'.ljust(59)
            statistics_block = (str(correct) + '/' + str(response_number-1) + ' (' + str(round(percentage, 1)) + '%)').rjust(20)
            print(label_block + iam + statistics_block)

    def generate_mchoices(self, mtag, response):
        '''Return the choices for the multiple choice questions'''
        out = []

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
            # Now that we have our choice, insert it into self.mchoices
            out.append((i, f_response))

        return out

    def print_mchoices(self):
        '''Print the multiple choices for Level 1'''
        for mchoice in self.mchoices:
            this_line = textwrap.fill(mchoice[1],
                                      initial_indent=mchoice[0] + ')' + (' ' * 6),
                                      subsequent_indent=' ' * 6, width=80)

    def prompt_for_response(self):
        '''Prompt for a response and return user input'''
        if self.settings.settings['level1']:
            user_input = input('Enter response choice: ')
        else:
            user_input = input('Enter response: ')

        return user_input

    def validate_input(self):
        if self.user_input in self.ascii_range:
            return True
        else:
            return False

    def is_correct(self):
        '''Determine whether input is correct.'''
        if self.settings.settings['level1']:
            # For level 1, check to see if the right letter was entered.
            return response == user_input
        elif self.settings.settings['level2'] or self.settings.settings['level3']:
            # For levels 2 or 3, make sure the right alias was entered.
            if self.user_input in aliases.keys():
                return response.lower() == user_input.lower() or response == aliases[user_input.lower()]
            else:
                return response.lower() == user_input.lower()
    
    def finalize(self):
        '''Notify the user of correctness, update statistics, and print'''
        if correct:
            print('Correct.')
            correct = correct + 1
        else:
            print('Incorrect. Answer: ' + response)
            incorrect = incorrect + 1
            incorrect_responses += response
        print()
        self.response_number = self.response_number + 1

    def render_question(self, cue_id, response_id):
        '''Render the question'''
        is_last_question = self.cue_id == cue_id and self.response_id == response_id

        if not is_last_question:
            cue = self.get_cue(cue_id)
            response = self.get_response(response_id)
            placement = self.get_placement(cue_id, response_id)
            # hints = response_id_to_hints(response_id)
            mtags = self.get_mtags(response_id)
            # Get number of mtags
            n_mtags = len(mtags)
            self.percentage = self.get_percentage()

            # If on level one, generate the multiple choice questions.
            if settings.settings['level1']:
                self.mchoices = self.generate_mchoices()
           
            # elif settings.settings['level2']:
            #     for hint in hints:
            #         # Print hint only if it is not empty.
            #         if len(hint) != 0:
            #             # Format hint to match cue.
            #             f_hint = textwrap.fill('Hint: ' + hint, subsequent_indent=' ' * 6, width=80)
            #             print(f_hint)
            #             print()

        self.print_header(self.settings, self.response_number, self.percentage)

        print()
        print(self.f_cue)
        print()

        if self.settings.settings['level1']:
            self.print_mchoices()

        # Start time
        start = time.time()

        # Prompt for user input
        user_input = self.prompt_for_response()

        # End time
        end = time.time()
        elasped_time = end - start

        valid_input = self.validate_input(user_input, response)
        correct = is_correct(user_input, response)

        # Get elapsed time and add it to times.
        self.times.append(elasped_time)

        # Clear screen.
        os.system('clear')

        self.finalize()
    