import tkinter as tk

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

        # Upper area ##########################################################
        self.upper = tk.Frame(master=self.root)
        self.upper.columnconfigure(0, weight=1)
        self.upper.columnconfigure(1, weight=1)

        self.title = tk.Frame(master=self.upper)
        self.title.grid(column=0, row=0, sticky='nsew', rowspan=2)
        self.title_label = tk.Label(master=self.title, anchor='w')
        self.title_label.pack(fill=tk.BOTH, expand=tk.YES)

        self.level = tk.Frame(master=self.upper)
        self.level.grid(column=1, row=0, sticky='nsew')
        self.level_label = tk.Label(master=self.level, anchor='e')
        self.level_label.pack(fill=tk.X)

        self.response_number = tk.Frame(master=self.upper)
        self.response_number.grid(column=1, row=1, sticky='nsew')
        self.response_number_label = tk.Label(master=self.response_number, anchor='e')
        self.response_number_label.pack(fill=tk.X)

        self.upper.pack(fill=tk.X, expand=tk.YES)

        # Middle area #########################################################
        self.middle = tk.Frame(master=self.root)

        self.cue_text_widget = tk.Text(master=self.middle, width=75, height=8)
        self.cue_text_widget.configure(font=('Arial', 10))
        self.cue_text_widget.insert(tk.END, 'This is the text of the question.')
        self.cue_text_widget.pack()

        self.middle.pack()

        # Bottom area #########################################################
        self.bottom = tk.Frame(master=self.root)
        self.bottom.columnconfigure(0, weight=1)

        self.response_placeholder = False

        self.response = tk.Entry(master=self.bottom, font='Arial 9 italic')
        self.response.insert(0, 'Enter response')
        self.response_placeholder = True
        self.response.grid(column=0, row=0, sticky='nsew')
        self.response.bind('<Key>', self.response_key)
        self.response.bind('<KeyRelease>', self.response_keyrelease)
        self.response.bind('<FocusIn>', self.response_focus)
        self.response.icursor(0)

        self.button = tk.Button(master=self.bottom, text='Go', bg='green', fg='white', padx=10)
        self.button.grid(column=1, row=0)
        self.button.bind('<Return>')

        self.bottom.pack(fill=tk.X)

        self.response.focus_set()

    def response_key(self, event=None):
        '''Triggered by <Key>, before sending the event to the widget'''
        # If the key pressed isn't a special key, remove placeholder and
        # unitalicize widget text
        if(self.response_placeholder == True and event.char != ""):
            self.response.delete(0, tk.END)
            self.response.configure(font='Arial 9')
            self.response_placeholder = False

    def response_keyrelease(self, event=None):
        '''Triggered by <KeyRelease>, before sending the event to the widget'''
        # If widget is empty, italicize font, then insert placeholder
        if(self.response_placeholder == False and len(self.response.get()) == 0):
            self.response.configure(font='Arial 9 italic')
            self.response.insert(0, 'Enter response')
            self.response_placeholder = True
            self.response.icursor(0)

    def response_focus(self, event=None):
        '''Triggered by placing focus on the widget'''
        if(self.response_placeholder == True):
            self.response.icursor(0)

    def set_cue_text_widget_content(self, content):
        self.cue_text_widget.delete(1.0, tk.END)
        self.cue_text_widget.insert(tk.END, content)

    def data_mainloop(self):
        # Data processing #####################################################
        self.question.main_data_loop(self.cr_id_pairs[0][0], self.cr_id_pairs[0][1], self.mtstatistics)

        self.title_label.configure(text=self.question.title_text)
        self.level_label.configure(text=self.question.level_text)
        self.response_number_label.configure(text=self.question.response_number_text)
        self.set_cue_text_widget_content(self.question.cue_text)
        # for cr_id_pair in self.cr_id_pairs:
            # self.mtstatistics.is_input_valid = False

            # Don't continue with the loop until a valid response has been
            # entered.
            # while not self.mtstatistics.is_input_valid:

                # input('Press Enter to continue.')

    def tk_mainloop(self):
        self.root.mainloop()

mtgui = MemtrainGUI()
mtgui.data_mainloop()
mtgui.tk_mainloop()
