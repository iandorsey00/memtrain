import tkinter as tk
import tkinter.messagebox as tk_messagebox
import tkinter.filedialog as tk_filedialog

import time

from functools import partial
from datetime import timedelta
from statistics import mean

from memtrain.memtrain_common.engine import Engine
from memtrain.memtrain_common.question import Question

class MemtrainGUI:
    def __init__(self):
        '''Construct the settings interface'''
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

        # Step 1 ##############################################################
        self.step_1 = tk.Frame(master=self.root)

        self.step_1_label_frame = tk.Frame(master=self.step_1)
        self.step_1_label_frame.pack(fill=tk.BOTH, expand=tk.YES, pady=10)
        self.step_1_label = tk.Label(master=self.step_1_label_frame, anchor='w',
                                    text='Step 1. Select file')
        self.step_1_label.pack(fill=tk.X, expand=tk.YES)

        self.step_1_button_frame = tk.Frame(master=self.step_1)
        self.select_csv_button = tk.Button(master=self.step_1_button_frame, text='Select CSV file', padx=10, command=self.select_csv)
        self.select_csv_button.pack()
        self.step_1_button_frame.pack(fill=tk.X, expand=tk.YES)

        self.step_1_filename_frame = tk.Frame(master=self.step_1)
        self.step_1_filename_frame.pack(fill=tk.BOTH, expand=tk.YES, pady=10)
        self.step_1_filename_label = tk.Label(master=self.step_1_filename_frame, anchor='w')
        self.step_1_filename_label.pack(fill=tk.X, expand=tk.YES)

        self.step_1.pack(fill=tk.X, expand=tk.YES)

        self.select_csv_button.focus_set()

        # Step 2 ##############################################################
        self.step_2 = tk.Frame(master=self.root)

        self.step_2_label_frame = tk.Frame(master=self.step_2)
        self.step_2_label_frame.pack(fill=tk.BOTH, expand=tk.YES, pady=10)
        self.step_2_label = tk.Label(master=self.step_2_label_frame, anchor='w',
                                    text='Step 2. Select level and start')
        self.step_2_label.pack(fill=tk.X, expand=tk.YES)

        start_level_1 = partial(self.start_level, '1')
        start_level_2 = partial(self.start_level, '2')
        start_level_3 = partial(self.start_level, '3')

        self.step_2_button_frame = tk.Frame(master=self.step_2)
        self.level_1_button = tk.Button(master=self.step_2_button_frame, text='Level 1', padx=10, command=start_level_1)
        self.level_1_button.pack(side=tk.LEFT)
        self.level_2_button = tk.Button(master=self.step_2_button_frame, text='Level 2', padx=10, command=start_level_2)
        self.level_2_button.pack(side=tk.LEFT)
        self.level_3_button = tk.Button(master=self.step_2_button_frame, text='Level 3', padx=10, command=start_level_3)
        self.level_3_button.pack(side=tk.LEFT)
        self.step_2_button_frame.pack(expand=tk.YES)

        self.step_2.pack(fill=tk.X, expand=tk.YES)

    def select_csv(self):
        self.filename = tk_filedialog.askopenfilename(title='Select a memtrain CSV file',
                filetypes=(('CSV files', '*.csv'),))
        self.step_1_filename_label.configure(text='Selected file: ' + self.filename)

    def start_level(self, level):
        '''Start a level'''
        self.level = level
        # Initialize Engine
        self.engine = Engine(self.filename, self.level, self.nquestions, self.tags, self.not_tags)

        self.settings = self.engine.settings
        self.database = self.engine.database
        self.mtstatistics = self.engine.mtstatistics
        self.cr_id_pairs = self.engine.cr_id_pairs

        self.question = Question(self.settings, self.database)

        # Create the training window
        self.training_window = tk.Toplevel(self.root)
        self.training_window.attributes('-topmost', 'true')

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

        self.middle_frame.pack()

        # Bottom area #########################################################
        self.bottom_frame = tk.Frame(master=self.training_window)
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.rowconfigure(0, weight=2)
        self.bottom_frame.rowconfigure(1, weight=2)

        self.correctness_frame = tk.Frame(master=self.bottom_frame)
        self.correctness_frame.grid(row=0, column=0, sticky='nsew')
        self.correctness_label = tk.Label(master=self.correctness_frame, anchor='w')
        self.correctness_label.pack(fill=tk.BOTH, expand=tk.YES)
        self.correctness_label.configure(text='After your first response, correctness information will appear here.')

        self.other_answers_frame = tk.Frame(master=self.bottom_frame)
        self.other_answers_frame.grid(row=1, column=0, sticky='nsew')
        self.other_answers_label = tk.Label(master=self.other_answers_frame, anchor='w')
        self.other_answers_label.pack(fill=tk.BOTH, expand=tk.YES)

        self.response_frame = tk.Frame(master=self.bottom_frame)
        self.response_frame.columnconfigure(0, weight=1)

        self.response_entry_placeholder = False

        self.response_entry = tk.Entry(master=self.response_frame, font='Arial 9 italic')
        self.response_entry.insert(0, 'Enter response')
        self.response_entry_placeholder = True
        self.response_entry.grid(row=2, column=0, sticky='nsew')
        self.response_entry.bind('<Key>', self.response_key)
        self.response_entry.bind('<KeyRelease>', self.response_keyrelease)
        self.response_entry.bind('<FocusIn>', self.response_focus)
        self.response_entry.icursor(0)

        self.button = tk.Button(master=self.response_frame, text='Go', bg='green', fg='white', padx=10, command=self.submit)
        self.button.grid(row=2, column=1)
        self.training_window.bind('<Return>', self.submit)

        self.response_frame.grid(row=2, column=0, sticky='nsew')

        self.bottom_frame.pack(fill=tk.X)

        self.response_entry.focus_set()
        self.render_question()

    def response_key(self, event=None):
        '''Triggered by <Key>, before sending the event to the widget'''
        # If the key pressed isn't a special key, remove placeholder and
        # unitalicize widget text
        if(self.response_entry_placeholder == True and event.char != ""):
            self.response_entry.delete(0, tk.END)
            self.response_entry.configure(font='Arial 9')
            self.response_entry_placeholder = False

    def response_keyrelease(self, event=None):
        '''Triggered by <KeyRelease>, before sending the event to the widget'''
        # If widget is empty, italicize font, then insert placeholder
        if(self.response_entry_placeholder == False and len(self.response_entry.get()) == 0):
            self.response_entry.configure(font='Arial 9 italic')
            self.response_entry.insert(0, 'Enter response')
            self.response_entry_placeholder = True
            self.response_entry.icursor(0)

    def response_focus(self, event=None):
        '''Triggered by placing focus on the widget'''
        if(self.response_entry_placeholder == True):
            self.response_entry.icursor(0)

    def response_clear(self):
        self.response_entry.delete(0, tk.END)
        self.response_entry.configure(font='Arial 9 italic')
        self.response_entry.insert(0, 'Enter response')
        self.response_entry_placeholder = True
        self.response_entry.icursor(0)

    def set_cue_text_widget_content(self, content):
        self.cue_text_widget.delete(1.0, tk.END)
        self.cue_text_widget.insert(tk.END, content)

    def render_question(self):
        # Data processing #####################################################
        this_question_id = self.mtstatistics.response_number-1
        self.question.main_data_loop(self.cr_id_pairs[this_question_id][0], self.cr_id_pairs[this_question_id][1], self.mtstatistics)

        self.title_label.configure(text=self.question.title_text)
        self.level_label.configure(text=self.question.level_text)
        self.response_number_label.configure(text=self.question.response_number_text)
        self.correct_number_label.configure(text=self.question.correct_so_far_text)
        self.set_cue_text_widget_content(self.question.cue_text)

        # For level 2, display hints
        if self.level == '2':
            these_hints = '; '.join(self.question.hints)
            self.hint_text_label.configure(text=these_hints)

        self.start_time = time.time()
        # self.other_answers_label.configure(text='hhh')
        # for cr_id_pair in self.cr_id_pairs:
            # self.mtstatistics.is_input_valid = False

            # Don't continue with the loop until a valid response has been
            # entered.
            # while not self.mtstatistics.is_input_valid:

                # input('Press Enter to continue.')

    def submit(self, event=None):
        self.question.user_input = self.response_entry.get().lower()
        self.question.validate_input()

        if self.mtstatistics.is_input_valid:
            self.end_time = time.time()
            elapsed_time = self.end_time - self.start_time
            self.mtstatistics.times.append(elapsed_time)

            self.question.grade_input()
            self.question.finalize()
            self.correctness_label.configure(text=self.question.correctness_str)

            if self.mtstatistics.has_synonym_been_used():
                self.other_answers_label.configure(text=self.question.other_answers_str)
            else:
                self.other_answers_label.configure(text='')

        else:
            tk_messagebox.showinfo('Invalid response', 'Sorry, your response is not valid. Please try again.')

        is_last_question = self.mtstatistics.response_number > self.mtstatistics.total

        if not is_last_question:
            self.response_clear()
            self.render_question()
        else:
            msg_box_str  = 'Correct: ' + str(self.mtstatistics.number_correct) + '/' + str(self.mtstatistics.total) + ' (' + str(round(self.mtstatistics.percentage, 1)) + '%)\n'
            msg_box_str += 'Average response time: ' + str(timedelta(seconds=mean(self.mtstatistics.times))) + ' seconds'
            
            if(self.mtstatistics.number_incorrect > 0):
                msg_box_str += '\n'
                msg_box_str += 'Responses for which answers were incorrect: '
                msg_box_str += self.mtstatistics.incorrect_responses_as_string()
            
            tk_messagebox.showinfo('Training session complete', msg_box_str)
            self.training_window.destroy()

    def tk_mainloop(self):
        self.root.mainloop()

mtgui = MemtrainGUI()
mtgui.tk_mainloop()
