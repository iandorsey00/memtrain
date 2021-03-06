import tkinter as tk
import tkinter.messagebox as tk_messagebox
import tkinter.filedialog as tk_filedialog
import tkinter.ttk as tk_ttk

import time

from functools import partial
from datetime import timedelta
from statistics import mean

from memtrain.memtrain_common.engine import Engine
from memtrain.memtrain_common.question import Question

class MemtrainGUI:
    def __init__(self):
        '''Initialize main variables and the configuration window'''
        self.root = tk.Tk()
        self.root.minsize(300, 100)
        self.root.title('memtrain v0.3a')

        self.filename = ''
        self.level = ''
        self.nquestions = ''
        self.tags = ''
        self.not_tags = ''

        self.start_time = None
        self.end_time = None

        #
        # Configuration window
        #

        # Settings ############################################################
        self.settings_frame = tk.Frame(master=self.root)

        self.settings_label_frame = tk.Frame(master=self.settings_frame)
        self.settings_label_frame.pack(fill=tk.BOTH, expand=tk.YES, pady=10)
        self.settings_label = tk.Label(master=self.settings_label_frame, anchor='w',
                                       text='(Optional) Configure settings')
        self.settings_label.pack(fill=tk.X, expand=tk.YES)

        self.settings_button_frame = tk.Frame(master=self.settings_frame)
        self.settings_button = tk.Button(master=self.settings_frame, text='Settings...', padx=10, command=self.configure_settings)
        self.settings_button.pack()
        self.settings_button_frame.pack(fill=tk.X, expand=tk.YES)

        self.settings_frame.pack(fill=tk.X, expand=tk.YES)

        self.settings_seperator = tk_ttk.Separator(master=self.root, orient='horizontal')
        self.settings_seperator.pack(fill=tk.X, expand=tk.YES, pady=(10, 0))

        # Step 1 ##############################################################
        self.step_1_frame = tk.Frame(master=self.root)

        self.step_1_label_frame = tk.Frame(master=self.step_1_frame)
        self.step_1_label_frame.pack(fill=tk.BOTH, expand=tk.YES, pady=10)
        self.step_1_label = tk.Label(master=self.step_1_label_frame, anchor='w',
                                     text='Step 1. Select file')
        self.step_1_label.pack(fill=tk.X, expand=tk.YES)

        self.step_1_button_frame = tk.Frame(master=self.step_1_frame)
        self.select_csv_button = tk.Button(master=self.step_1_button_frame, text='Select CSV file', padx=10, command=self.select_csv)
        self.select_csv_button.pack()
        self.step_1_button_frame.pack(fill=tk.X, expand=tk.YES)

        self.step_1_filename_frame = tk.Frame(master=self.step_1_frame)
        self.step_1_filename_frame.pack(fill=tk.BOTH, expand=tk.YES, pady=10)
        self.step_1_filename_label = tk.Label(master=self.step_1_filename_frame, text='No file selected.', anchor='w')
        self.step_1_filename_label.pack(fill=tk.X, expand=tk.YES)

        self.step_1_frame.pack(fill=tk.X, expand=tk.YES)

        self.select_csv_button.focus_set()

        self.step_1_seperator = tk_ttk.Separator(master=self.root, orient='horizontal')
        self.step_1_seperator.pack(fill=tk.X, expand=tk.YES)

        # Step 2 ##############################################################
        self.step_2_frame = tk.Frame(master=self.root)

        self.step_2_label_frame = tk.Frame(master=self.step_2_frame)
        self.step_2_label_frame.pack(fill=tk.BOTH, expand=tk.YES, pady=10)
        self.step_2_label = tk.Label(master=self.step_2_label_frame, anchor='w',
                                    text='Step 2. Select level and start')
        self.step_2_label.pack(fill=tk.X, expand=tk.YES)

        start_level_1 = partial(self.start_level, '1')
        start_level_2 = partial(self.start_level, '2')
        start_level_3 = partial(self.start_level, '3')

        # Wait until CSV is loaded to change buttons into normal state.
        self.step_2_button_frame = tk.Frame(master=self.step_2_frame)
        self.level_1_button = tk.Button(master=self.step_2_button_frame, text='Level 1',
                                        padx=10, state=tk.DISABLED, command=start_level_1)
        self.level_1_button.pack(side=tk.LEFT)
        self.level_2_button = tk.Button(master=self.step_2_button_frame, text='Level 2',
                                        padx=10, state=tk.DISABLED, command=start_level_2)
        self.level_2_button.pack(side=tk.LEFT)
        self.level_3_button = tk.Button(master=self.step_2_button_frame, text='Level 3',
                                        padx=10, state=tk.DISABLED, command=start_level_3)
        self.level_3_button.pack(side=tk.LEFT)
        self.step_2_button_frame.pack(expand=tk.YES)

        self.step_2_frame.pack(fill=tk.X, expand=tk.YES, pady=(0, 10))

    def configure_settings(self):
        '''A window for more advanced settings'''
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title('Settings')

        ### nquestions - Number of questions
        self.nquestions_label = tk.Label(master=self.settings_window, text='Number of questions (an integer greater than zero)', anchor='w')
        self.nquestions_label.pack(fill=tk.X, expand=tk.YES)
        
        # nquestions validation command
        vcmd = (self.settings_window.register(self.nquestions_validate), '%P')

        self.nquestions_entry = tk.Entry(master=self.settings_window, validate='key', validatecommand=vcmd)
        self.nquestions_entry.pack(fill=tk.X, expand=tk.YES)

        ### Tags to be included
        self.tags_label = tk.Label(master=self.settings_window, text="Include the following tags (seperated by a comma ',')", anchor='w')
        self.tags_label.pack(fill=tk.X, expand=tk.YES)

        self.tags_entry = tk.Entry(master=self.settings_window)
        self.tags_entry.pack(fill=tk.X, expand=tk.YES)

        ### Tags not to be included
        self.not_tags_label = tk.Label(master=self.settings_window, text="Do not include the following tags (seperated by a comma ',')", anchor='w')
        self.not_tags_label.pack(fill=tk.X, expand=tk.YES)

        self.not_tags_entry = tk.Entry(master=self.settings_window)
        self.not_tags_entry.pack(fill=tk.X, expand=tk.YES)

        ### Buttons
        self.settings_buttons_frame = tk.Frame(master=self.settings_window)

        self.clear_settings_button = tk.Button(master=self.settings_buttons_frame, text='Clear settings',
                                               command=self.clear_settings)
        self.clear_settings_button.pack(side=tk.LEFT)

        self.ok_button = tk.Button(master=self.settings_buttons_frame, text='OK',
                                               command=self.commit_settings)
        self.ok_button.pack(side=tk.LEFT)

        self.settings_buttons_frame.pack()

        # If we have values set already, fill them in.
        if self.nquestions != '':
            self.nquestions_entry.insert(0, self.nquestions)
        if self.tags != '':
            self.tags_entry.insert(0, self.tags)
        if self.not_tags != '':
            self.not_tags_entry.insert(0, self.not_tags)

        # Set focus for better usability.
        self.nquestions_entry.focus_set()

    def clear_settings(self):
        '''Clear all settings Entries'''
        self.nquestions_entry.delete(0, tk.END)
        self.tags_entry.delete(0, tk.END)
        self.not_tags_entry.delete(0, tk.END)

    def commit_settings(self):
        '''Write settings'''
        self.nquestions = self.nquestions_entry.get()
        self.tags = self.tags_entry.get()
        self.not_tags = self.not_tags_entry.get()
        self.settings_window.destroy()

    def nquestions_validate(self, input):
        '''Determine what values can be input into the nquestions Entry'''
        if input == '':
            return True
        else:
            try:
                int(input)
                if int(input) > 0:
                    return True
                else:
                    return False
            except ValueError:
                return False

    def initialize_engine_and_core_objects(self):
        '''Initialize the engine and core objects'''
        # Initialize Engine - memtrain.memtrain_common.engine
        self.engine = Engine(self.filename, self.level, self.nquestions, self.tags, self.not_tags)

        # Initialize core objects
        self.settings = self.engine.settings
        self.database = self.engine.database
        self.mtstatistics = self.engine.mtstatistics
        self.cr_id_pairs = self.engine.cr_id_pairs

        self.question = Question(self.settings, self.database)

    def select_csv(self):
        '''The interface for CSV selection'''
        self.filename = tk_filedialog.askopenfilename(title='Select a memtrain CSV file',
                filetypes=(('CSV files', '*.csv'),))
        self.step_1_filename_label.configure(text='Selected file: ' + self.filename)

        self.initialize_engine_and_core_objects()

        # Whether or not levels are enabled
        settings_truth_list = [self.settings.settings['level1'],
                               self.settings.settings['level2'],
                               self.settings.settings['level3']]

        # Number of levels enabled
        only_one_enabled_level = sum(settings_truth_list) == 1

        # Enable buttons. If there is only enabled level, just start it
        # immediately.
        if self.settings.settings['level1'] == True:
            self.level_1_button.configure(state=tk.NORMAL)
            if only_one_enabled_level:
                self.level_1_button.focus_set()
                self.start_level('1')
        if self.settings.settings['level2'] == True:
            self.level_2_button.configure(state=tk.NORMAL)
            if only_one_enabled_level:
                self.level_2_button.focus_set()
                self.start_level('2')
        if self.settings.settings['level3'] == True:
            self.level_3_button.configure(state=tk.NORMAL)
            if only_one_enabled_level:
                self.level_3_button.focus_set()
                self.start_level('3')

        # If there are multiple levels enabled, set focus the button of the
        # first enabled level.
        if self.settings.settings['level1'] == True:
                self.level_1_button.focus_set()
        elif self.settings.settings['level2'] == True:
                self.level_2_button.focus_set()
        elif self.settings.settings['level3'] == True:
                self.level_3_button.focus_set()

    def start_level(self, level):
        '''Start a level'''
        self.level = level
        
        self.initialize_engine_and_core_objects()

        # Create the training window
        self.training_window = tk.Toplevel(self.root)

        # Upper area ##########################################################
        self.upper_frame = tk.Frame(master=self.training_window)
        self.upper_frame.columnconfigure(0, weight=1)
        self.upper_frame.columnconfigure(1, weight=1)

        self.title_frame = tk.Frame(master=self.upper_frame)
        self.title_frame.grid(row=0, column=0, sticky='nsew')
        self.title_label = tk.Label(master=self.title_frame, anchor='w')
        self.title_label.pack(fill=tk.X, expand=tk.YES)

        self.level_frame = tk.Frame(master=self.upper_frame)
        self.level_frame.grid(row=0, column=1, sticky='nsew')
        self.level_label = tk.Label(master=self.level_frame, anchor='e')
        self.level_label.pack(fill=tk.X)

        self.response_number_frame = tk.Frame(master=self.upper_frame)
        self.response_number_frame.grid(row=1, column=0, sticky='nsew')
        self.response_number_label = tk.Label(master=self.response_number_frame, anchor='w')
        self.response_number_label.pack(fill=tk.X)

        self.correct_number_frame = tk.Frame(master=self.upper_frame)
        self.correct_number_frame.grid(row=1, column=1, sticky='nsew')
        self.correct_number_label = tk.Label(master=self.correct_number_frame, anchor='e')
        self.correct_number_label.pack(fill=tk.X)

        self.upper_frame.pack(fill=tk.X)

        # Middle area #########################################################
        self.middle_frame = tk.Frame(master=self.training_window)

        self.cue_text_widget = tk.Text(master=self.middle_frame, width=75, height=8, font=('Arial', 10),
                                       borderwidth=15, relief=tk.FLAT)
        self.cue_text_widget.insert(tk.END, 'This is the text of the question.')
        self.cue_text_widget.pack(fill=tk.BOTH, expand=tk.YES)

        # For level 2, display a hint.
        if self.level == '2':
            self.hint_frame = tk.Frame(master=self.middle_frame)
            self.hint_label = tk.Label(master=self.hint_frame, text='Hint(s):', anchor='w')
            self.hint_label.pack(side=tk.LEFT)
            self.hint_text_label = tk.Label(master=self.hint_frame, anchor='w', padx=10)
            self.hint_text_label.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES)
            self.hint_frame.pack(fill=tk.X, expand=tk.YES)

        self.correctness_frame = tk.Frame(master=self.middle_frame)
        self.correctness_frame.pack(fill=tk.X, expand=tk.YES)
        self.correctness_label = tk.Label(master=self.correctness_frame, anchor='w')
        self.correctness_label.pack(fill=tk.BOTH, expand=tk.YES)
        self.correctness_label.configure(text='After your first response, correctness information will appear here.')

        self.other_answers_frame = tk.Frame(master=self.middle_frame)
        self.other_answers_frame.pack(fill=tk.X, expand=tk.YES)
        self.other_answers_label = tk.Label(master=self.other_answers_frame, anchor='w')
        self.other_answers_label.pack(fill=tk.BOTH, expand=tk.YES)

        self.middle_frame.pack()

        # Bottom area #########################################################
        self.bottom_frame = tk.Frame(master=self.training_window)

        if self.level == '1':
            self.mchoices_frame = tk.Frame(master=self.bottom_frame)
            self.mchoices_frame.grid(row=0, column=0, sticky='nsew')
            self.mchoices_frame.columnconfigure(0, weight=0)
            self.mchoices_frame.columnconfigure(1, weight=2)
        else:
            self.bottom_frame.columnconfigure(0, weight=1)
            self.response_frame = tk.Frame(master=self.bottom_frame)
            self.response_frame.columnconfigure(0, weight=1)

            self.response_entry_placeholder = False

            self.response_entry = tk.Entry(master=self.response_frame, font='Arial 9 italic')
            self.response_entry.insert(0, 'Enter response')
            self.response_entry_placeholder = True
            self.response_entry.grid(row=2, column=0, sticky='nsew')
            self.response_entry.bind('<Key>', self.response_key)
            self.response_entry.bind('<KeyRelease>', self.response_keyrelease)
            self.response_entry.bind('<FocusIn>', self.response_focusin)
            self.response_entry.icursor(0)

            self.button = tk.Button(master=self.response_frame, text='Go', bg='green', fg='white', padx=10, command=self.submit)
            self.button.grid(row=2, column=1)
            self.training_window.bind('<Return>', self.submit)

            self.response_frame.grid(row=2, column=0, sticky='nsew')

            self.response_entry.focus_set()

        self.bottom_frame.pack(fill=tk.X)
        self.render_question()

    def response_key(self, event=None):
        '''Triggered by <Key>, before sending the event to the widget'''
        # If the key pressed isn't a special key, remove placeholder and
        # unitalicize widget text
        if self.response_entry_placeholder == True and event.char != "":
            self.response_entry.delete(0, tk.END)
            self.response_entry.configure(font='Arial 9')
            self.response_entry_placeholder = False

    def response_keyrelease(self, event=None):
        '''Triggered by <KeyRelease>, before sending the event to the widget'''
        # If widget is empty, italicize font, then insert placeholder
        if self.response_entry_placeholder == False and len(self.response_entry.get()) == 0:
            self.response_entry.configure(font='Arial 9 italic')
            self.response_entry.insert(0, 'Enter response')
            self.response_entry_placeholder = True
            self.response_entry.icursor(0)

    def response_focusin(self, event=None):
        '''Triggered by placing focus on the widget'''
        if self.response_entry_placeholder == True:
            self.response_entry.icursor(0)

    def response_clear(self):
        '''Clear the response Entry'''
        self.response_entry.delete(0, tk.END)
        self.response_entry.configure(font='Arial 9 italic')
        self.response_entry.insert(0, 'Enter response')
        self.response_entry_placeholder = True
        self.response_entry.icursor(0)

    def set_cue_text_widget_content(self, content):
        '''Set cue Text widget content'''
        self.cue_text_widget.delete(1.0, tk.END)
        self.cue_text_widget.insert(tk.END, content)

    def render_question(self):
        '''Render the question and process the necessary data to do so'''
        # Data processing #####################################################
        # Important: The question we are on
        this_question_id = self.mtstatistics.response_number-1

        # See memtrain.memtrain_common.question
        # This method is responsible for processing the data needed to render
        # the question.
        self.question.main_data_loop(self.cr_id_pairs[this_question_id][0], self.cr_id_pairs[this_question_id][1], self.mtstatistics)

        # Change Labels and Text widget text
        self.title_label.configure(text=self.question.title_text)
        self.level_label.configure(text=self.question.level_text)
        self.response_number_label.configure(text=self.question.response_number_text)
        self.correct_number_label.configure(text=self.question.correct_so_far_text)
        self.set_cue_text_widget_content(self.question.cue_text)

        # For level 2, display hints
        if self.level == '2':
            these_hints = '; '.join(self.question.hints)
            self.hint_text_label.configure(text=these_hints)

        # For level 1, display multiple choices
        if self.level == '1':
            self.question.mchoices = self.question.generate_mchoices()

            counter = 0

            # Store mchoice data in dictionaries
            self.mchoice_buttons = dict()
            mchoice_commands = dict()
            self.mchoice_labels = dict()

            # Iterate through mchoices
            for letter, choice in self.question.mchoices.items():
                mchoice_commands[letter] = partial(self.submit, mchoice_letter=letter)
                # Make it so you can press a, b, c, d to select a choice
                self.training_window.bind(letter, mchoice_commands[letter])
                self.mchoice_buttons[letter] = tk.Button(master=self.mchoices_frame, text=letter,
                                                    padx=10, command=mchoice_commands[letter])
                self.mchoice_buttons[letter].grid(row=counter, column=0, sticky='nsew')
                self.mchoice_labels[letter] = tk.Label(master=self.mchoices_frame, text=choice, padx=10, anchor='w')
                self.mchoice_labels[letter].grid(row=counter, column=1, sticky='w')
                self.mchoices_frame.pack(fill=tk.X, expand=tk.YES)

                counter += 1

            self.mchoice_buttons['a'].focus_set()

        self.start_time = time.time()

    def submit(self, event=None, mchoice_letter=None):
        '''Submit response'''
        if self.level == '1':
            self.question.user_input = mchoice_letter
        else:
            self.question.user_input = self.response_entry.get().lower()

        # Validate input
        self.question.validate_input()

        if self.mtstatistics.is_input_valid:
            # Calculate the amount of time elapsed and store it
            self.end_time = time.time()
            elapsed_time = self.end_time - self.start_time
            self.mtstatistics.times.append(elapsed_time)

            # Grade input and do finalization work
            self.question.grade_input()
            self.question.finalize()
            self.correctness_label.configure(text=self.question.correctness_str)

            if self.mtstatistics.has_synonym_been_used():
                self.other_answers_label.configure(text=self.question.other_answers_str)
            else:
                self.other_answers_label.configure(text='')

        else:
            tk_messagebox.showinfo('Invalid response', 'Sorry, your response is not valid. Please try again.')

        # Clean up after a question
        if not self.mtstatistics.is_last_question():
            # Clear response areas
            if self.level == '1':
                for letter, mchoice_button in self.mchoice_buttons.items():
                    mchoice_button.destroy()
                for letter, mchoice_label in self.mchoice_labels.items():
                    mchoice_label.destroy()
            else:
                self.response_clear()

            # Get ready for the next question
            self.render_question()
        # If that was the last question, destroy the training window and
        # display statistics.
        else:
            self.training_window.destroy()

            msg_box_str  = 'Correct: ' + str(self.mtstatistics.number_correct) + '/' + str(self.mtstatistics.total) + ' (' + str(round(self.mtstatistics.percentage, 1)) + '%)\n'
            msg_box_str += 'Average response time: ' + str(timedelta(seconds=mean(self.mtstatistics.times))) + ' seconds'
            
            if(self.mtstatistics.number_incorrect > 0):
                msg_box_str += '\n'
                msg_box_str += 'Responses for which answers were incorrect: '
                msg_box_str += self.mtstatistics.incorrect_responses_as_string()
            
            tk_messagebox.showinfo('Training session complete', msg_box_str)
            
            # Set the level button focus in the configuration window to the
            # button for the level just completed
            if self.settings.level == '1':
                    self.level_1_button.focus_set()
            elif self.settings.level == '2':
                    self.level_2_button.focus_set()
            elif self.settings.level == '3':
                    self.level_3_button.focus_set()

    def tk_mainloop(self):
        self.root.mainloop()

mtgui = MemtrainGUI()
mtgui.tk_mainloop()
