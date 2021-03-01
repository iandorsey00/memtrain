import tkinter as tk
import tkinter.messagebox as tk_messagebox

import time

from datetime import timedelta
from statistics import mean

from memtrain.memtrain_common.engine import Engine
from memtrain.memtrain_common.question import Question

class MemtrainGUI:
    def __init__(self):
        '''Construct the GUI interface'''
        self.root = tk.Tk()
        self.root.title('memtrain v0.3a')

        self.engine = Engine('C:/Users/iando/Desktop/animals.csv', '3', '', '', '')

        self.settings = self.engine.settings
        self.database = self.engine.database
        self.mtstatistics = self.engine.mtstatistics
        self.cr_id_pairs = self.engine.cr_id_pairs

        self.question = Question(self.settings, self.database)

        self.start_time = None
        self.end_time = None

        # Upper area ##########################################################
        self.upper = tk.Frame(master=self.root)
        self.upper.columnconfigure(0, weight=1)
        self.upper.columnconfigure(1, weight=1)

        self.title = tk.Frame(master=self.upper)
        self.title.grid(row=0, column=0, sticky='nsew')
        self.title_label = tk.Label(master=self.title, anchor='w')
        self.title_label.pack(fill=tk.BOTH, expand=tk.YES)

        self.level = tk.Frame(master=self.upper)
        self.level.grid(row=0, column=1, sticky='nsew')
        self.level_label = tk.Label(master=self.level, anchor='e')
        self.level_label.pack(fill=tk.X)

        self.response_number = tk.Frame(master=self.upper)
        self.response_number.grid(row=1, column=0, sticky='nsew')
        self.response_number_label = tk.Label(master=self.response_number, anchor='w')
        self.response_number_label.pack(fill=tk.X)

        self.correct_number = tk.Frame(master=self.upper)
        self.correct_number.grid(row=1, column=1, sticky='nsew')
        self.correct_number_label = tk.Label(master=self.correct_number, anchor='e')
        self.correct_number_label.pack(fill=tk.X)

        self.upper.pack(fill=tk.X, expand=tk.YES)

        # Middle area #########################################################
        self.middle = tk.Frame(master=self.root)

        self.cue_text_widget = tk.Text(master=self.middle, width=75, height=8, font=('Arial', 10),
                                       borderwidth=15, relief=tk.FLAT)
        self.cue_text_widget.insert(tk.END, 'This is the text of the question.')
        self.cue_text_widget.pack()

        self.middle.pack()

        # Bottom area #########################################################
        self.bottom = tk.Frame(master=self.root)
        self.bottom.columnconfigure(0, weight=1)
        self.bottom.rowconfigure(0, weight=2)
        self.bottom.rowconfigure(1, weight=2)

        self.correctness = tk.Frame(master=self.bottom)
        self.correctness.grid(row=0, column=0, sticky='nsew')
        self.correctness_label = tk.Label(master=self.correctness, anchor='w')
        self.correctness_label.pack(fill=tk.BOTH, expand=tk.YES)
        self.correctness_label.configure(text='After your first response, correctness information will appear here.')

        self.other_answers = tk.Frame(master=self.bottom)
        self.other_answers.grid(row=1, column=0, sticky='nsew')
        self.other_answers_label = tk.Label(master=self.other_answers, anchor='w')
        self.other_answers_label.pack(fill=tk.BOTH, expand=tk.YES)

        self.response = tk.Frame(master=self.bottom)
        self.response.columnconfigure(0, weight=1)

        self.response_entry_placeholder = False

        self.response_entry = tk.Entry(master=self.response, font='Arial 9 italic')
        self.response_entry.insert(0, 'Enter response')
        self.response_entry_placeholder = True
        self.response_entry.grid(row=2, column=0, sticky='nsew')
        self.response_entry.bind('<Key>', self.response_key)
        self.response_entry.bind('<KeyRelease>', self.response_keyrelease)
        self.response_entry.bind('<FocusIn>', self.response_focus)
        self.response_entry.icursor(0)

        self.button = tk.Button(master=self.response, text='Go', bg='green', fg='white', padx=10, command=self.submit)
        self.button.grid(row=2, column=1)
        self.root.bind('<Return>', self.submit)

        self.response.grid(row=2, column=0, sticky='nsew')

        self.bottom.pack(fill=tk.X)

        self.response_entry.focus_set()

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

        is_last_question = self.mtstatistics.response_number == self.mtstatistics.total

        if not is_last_question:
            self.response_clear()
            self.render_question()
        else:
            msg_box_str  = 'Correct: ' + str(self.mtstatistics.number_correct) + '/' + str(self.mtstatistics.total) + ' (' + str(round(self.mtstatistics.percentage, 1)) + '%)\n'
            msg_box_str += 'Average response time: ' + str(timedelta(seconds=mean(self.mtstatistics.times)) + ' seconds')
            
            if(self.mtstatistics.number_incorrect > 0):
                msg_box_str += '\n'
                msg_box_str += 'Responses for which answers were incorrect: '
                msg_box_str += self.mtstatistics.incorrect_responses_as_string()
            
            tk_messagebox.showinfo('Training session complete', msg_box_str)

    def tk_mainloop(self):
        self.root.mainloop()

mtgui = MemtrainGUI()
mtgui.render_question()
mtgui.tk_mainloop()
