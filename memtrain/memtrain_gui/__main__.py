import tkinter as tk
import tkinter.filedialog as tk_filedialog
import tkinter.messagebox as tk_messagebox
import tkinter.ttk as tk_ttk

import time

from datetime import timedelta
from functools import partial
from statistics import mean

from memtrain.memtrain_common.engine import Engine
from memtrain.memtrain_common.question import Question


class MemtrainGUI:
    '''Tk GUI for memtrain.'''

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('memtrain v0.4.2')
        self.root.minsize(720, 420)

        self.filename = ''
        self.level = ''
        self.nquestions = ''
        self.tags = ''
        self.not_tags = ''
        self.current_item = None

        self.start_time = None
        self.end_time = None
        self.response_entry_placeholder = True

        self.configure_styles()
        self.build_home_ui()
        self.present_window(self.root, self.select_csv_button)

    def configure_styles(self):
        self.style = tk_ttk.Style()

        try:
            if self.root.tk.call('tk', 'windowingsystem') == 'aqua':
                self.style.theme_use('aqua')
            else:
                self.style.theme_use('clam')
        except tk.TclError:
            pass

        background = '#f6f4ef'
        surface = '#fbfaf7'
        muted = '#5f6b76'
        accent = '#1f6f5f'

        self.root.configure(background=background)

        self.style.configure('Root.TFrame', background=background)
        self.style.configure('Card.TFrame', background=surface)
        self.style.configure('SectionTitle.TLabel', background=background, font=('TkDefaultFont', 13, 'bold'))
        self.style.configure('CardSectionTitle.TLabel', background=surface, font=('TkDefaultFont', 13, 'bold'))
        self.style.configure('Muted.TLabel', background=background, foreground=muted)
        self.style.configure('CardTitle.TLabel', background=surface, font=('TkDefaultFont', 14, 'bold'))
        self.style.configure('CardBody.TLabel', background=surface, font=('TkDefaultFont', 12))
        self.style.configure('Meta.TLabel', background=surface, foreground=muted, font=('TkDefaultFont', 11))
        self.style.configure('Choice.TButton', padding=(10, 8))
        self.style.configure('Primary.TButton', padding=(14, 10))
        self.style.configure('Start.TButton', padding=(12, 8))
        self.style.map('Primary.TButton', foreground=[('!disabled', accent)])

    def present_window(self, window, focus_widget=None):
        window.update_idletasks()
        window.lift()
        window.after_idle(window.lift)

        if focus_widget is not None:
            window.after_idle(focus_widget.focus_set)

    def build_home_ui(self):
        self.root_frame = tk_ttk.Frame(self.root, style='Root.TFrame', padding=20)
        self.root_frame.pack(fill=tk.BOTH, expand=tk.YES)
        self.root_frame.columnconfigure(0, weight=1)

        header = tk_ttk.Frame(self.root_frame, style='Root.TFrame')
        header.grid(row=0, column=0, sticky='ew')
        header.columnconfigure(0, weight=1)

        tk_ttk.Label(header, text='memtrain', style='SectionTitle.TLabel').grid(row=0, column=0, sticky='w')
        tk_ttk.Label(
            header,
            text='Structured recall practice with adaptive study or fixed review modes.',
            style='Muted.TLabel'
        ).grid(row=1, column=0, sticky='w', pady=(6, 0))

        self.settings_card = tk_ttk.LabelFrame(self.root_frame, text='Settings', padding=16)
        self.settings_card.grid(row=1, column=0, sticky='ew', pady=(20, 12))
        self.settings_card.columnconfigure(0, weight=1)

        tk_ttk.Label(
            self.settings_card,
            text='Adjust question count or focus the session with tags.',
            style='Muted.TLabel'
        ).grid(row=0, column=0, sticky='w')
        tk_ttk.Button(
            self.settings_card,
            text='Open Settings',
            command=self.configure_settings
        ).grid(row=0, column=1, sticky='e', padx=(12, 0))

        self.file_card = tk_ttk.LabelFrame(self.root_frame, text='Step 1: Study Set', padding=16)
        self.file_card.grid(row=2, column=0, sticky='ew', pady=(0, 12))
        self.file_card.columnconfigure(0, weight=1)

        self.select_csv_button = tk_ttk.Button(
            self.file_card,
            text='Choose CSV Study Set',
            command=self.select_csv
        )
        self.select_csv_button.grid(row=0, column=0, sticky='w')

        self.step_1_filename_label = tk_ttk.Label(
            self.file_card,
            text='No file selected.',
            style='Muted.TLabel',
            wraplength=640
        )
        self.step_1_filename_label.grid(row=1, column=0, sticky='ew', pady=(12, 0))

        self.start_card = tk_ttk.LabelFrame(self.root_frame, text='Step 2: Start Session', padding=16)
        self.start_card.grid(row=3, column=0, sticky='ew')
        self.start_card.columnconfigure(0, weight=1)

        tk_ttk.Label(
            self.start_card,
            text='Adaptive mode chooses the prompt level for each item. Fixed modes keep the whole session at one level.',
            style='Muted.TLabel',
            wraplength=640,
            justify=tk.LEFT
        ).grid(row=0, column=0, sticky='w')

        buttons = tk_ttk.Frame(self.start_card, style='Root.TFrame')
        buttons.grid(row=1, column=0, sticky='w', pady=(14, 0))

        start_adaptive = partial(self.start_level, '')
        start_level_1 = partial(self.start_level, '1')
        start_level_2 = partial(self.start_level, '2')
        start_level_3 = partial(self.start_level, '3')

        self.adaptive_button = tk_ttk.Button(
            buttons, text='Adaptive', command=start_adaptive, style='Primary.TButton', state=tk.DISABLED
        )
        self.adaptive_button.grid(row=0, column=0, padx=(0, 8))

        self.level_1_button = tk_ttk.Button(
            buttons, text='Level 1', command=start_level_1, style='Start.TButton', state=tk.DISABLED
        )
        self.level_1_button.grid(row=0, column=1, padx=(0, 8))

        self.level_2_button = tk_ttk.Button(
            buttons, text='Level 2', command=start_level_2, style='Start.TButton', state=tk.DISABLED
        )
        self.level_2_button.grid(row=0, column=2, padx=(0, 8))

        self.level_3_button = tk_ttk.Button(
            buttons, text='Level 3', command=start_level_3, style='Start.TButton', state=tk.DISABLED
        )
        self.level_3_button.grid(row=0, column=3)

    def configure_settings(self):
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            self.present_window(self.settings_window, self.nquestions_entry)
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title('Session Settings')
        self.settings_window.transient(self.root)
        self.settings_window.resizable(False, False)

        frame = tk_ttk.Frame(self.settings_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=tk.YES)
        frame.columnconfigure(1, weight=1)

        tk_ttk.Label(frame, text='Questions', style='SectionTitle.TLabel').grid(row=0, column=0, sticky='w', columnspan=2)
        tk_ttk.Label(
            frame,
            text='Leave blank to use the adaptive default session size.',
            style='Muted.TLabel'
        ).grid(row=1, column=0, sticky='w', columnspan=2, pady=(4, 12))

        vcmd = (self.settings_window.register(self.nquestions_validate), '%P')

        tk_ttk.Label(frame, text='Number of questions').grid(row=2, column=0, sticky='w', pady=(0, 10))
        self.nquestions_entry = tk_ttk.Entry(frame, validate='key', validatecommand=vcmd)
        self.nquestions_entry.grid(row=2, column=1, sticky='ew', pady=(0, 10))

        tk_ttk.Label(frame, text='Include tags').grid(row=3, column=0, sticky='w', pady=(0, 10))
        self.tags_entry = tk_ttk.Entry(frame)
        self.tags_entry.grid(row=3, column=1, sticky='ew', pady=(0, 10))

        tk_ttk.Label(frame, text='Exclude tags').grid(row=4, column=0, sticky='w')
        self.not_tags_entry = tk_ttk.Entry(frame)
        self.not_tags_entry.grid(row=4, column=1, sticky='ew')

        buttons = tk_ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=2, sticky='e', pady=(18, 0))

        tk_ttk.Button(buttons, text='Clear', command=self.clear_settings).grid(row=0, column=0, padx=(0, 8))
        tk_ttk.Button(buttons, text='Save', command=self.commit_settings, style='Primary.TButton').grid(row=0, column=1)

        if self.nquestions != '':
            self.nquestions_entry.insert(0, self.nquestions)
        if self.tags != '':
            self.tags_entry.insert(0, self.tags)
        if self.not_tags != '':
            self.not_tags_entry.insert(0, self.not_tags)

        self.present_window(self.settings_window, self.nquestions_entry)

    def clear_settings(self):
        self.nquestions_entry.delete(0, tk.END)
        self.tags_entry.delete(0, tk.END)
        self.not_tags_entry.delete(0, tk.END)

    def commit_settings(self):
        self.nquestions = self.nquestions_entry.get()
        self.tags = self.tags_entry.get()
        self.not_tags = self.not_tags_entry.get()
        self.settings_window.destroy()

    def nquestions_validate(self, input_value):
        if input_value == '':
            return True
        try:
            return int(input_value) > 0
        except ValueError:
            return False

    def initialize_engine_and_core_objects(self):
        self.engine = Engine(self.filename, self.level, self.nquestions, self.tags, self.not_tags)
        self.settings = self.engine.settings
        self.database = self.engine.database
        self.mtstatistics = self.engine.mtstatistics
        self.cr_id_pairs = self.engine.cr_id_pairs
        self.question = Question(self.settings, self.database)

    def select_csv(self):
        self.filename = tk_filedialog.askopenfilename(
            parent=self.root,
            title='Select a memtrain CSV file',
            filetypes=(('CSV files', '*.csv'),)
        )

        if not self.filename:
            self.step_1_filename_label.configure(text='No file selected.')
            return

        self.step_1_filename_label.configure(text=self.filename)

        try:
            self.initialize_engine_and_core_objects()
        except Exception as exc:
            self.step_1_filename_label.configure(text='Failed to load file.')
            tk_messagebox.showerror('Unable to load study set', str(exc), parent=self.root)
            return

        self.configure_start_buttons()
        self.adaptive_button.focus_set()

    def configure_start_buttons(self):
        self.adaptive_button.configure(state=tk.NORMAL)
        self.level_1_button.configure(state=tk.NORMAL if self.settings.settings['level1'] else tk.DISABLED)
        self.level_2_button.configure(state=tk.NORMAL if self.settings.settings['level2'] else tk.DISABLED)
        self.level_3_button.configure(state=tk.NORMAL if self.settings.settings['level3'] else tk.DISABLED)

    def start_level(self, level):
        if not self.filename:
            tk_messagebox.showinfo('Select a study set', 'Choose a CSV file before starting.', parent=self.root)
            return

        self.level = level

        try:
            self.initialize_engine_and_core_objects()
        except Exception as exc:
            tk_messagebox.showerror('Unable to start session', str(exc), parent=self.root)
            return

        self.build_training_window()
        self.render_question()
        self.present_window(self.training_window)

    def build_training_window(self):
        self.training_window = tk.Toplevel(self.root)
        self.training_window.transient(self.root)
        self.training_window.title('memtrain study')
        self.training_window.minsize(840, 560)

        outer = tk_ttk.Frame(self.training_window, padding=18)
        outer.pack(fill=tk.BOTH, expand=tk.YES)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        self.summary_card = tk_ttk.Frame(outer, style='Card.TFrame', padding=18)
        self.summary_card.grid(row=0, column=0, sticky='ew')
        self.summary_card.columnconfigure(0, weight=1)
        self.summary_card.columnconfigure(1, weight=0)

        self.title_label = tk_ttk.Label(self.summary_card, style='CardTitle.TLabel')
        self.title_label.grid(row=0, column=0, sticky='w')

        self.level_label = tk_ttk.Label(self.summary_card, style='CardTitle.TLabel')
        self.level_label.grid(row=0, column=1, sticky='e')

        self.response_number_label = tk_ttk.Label(self.summary_card, style='Meta.TLabel')
        self.response_number_label.grid(row=1, column=0, sticky='w', pady=(6, 0))

        self.correct_number_label = tk_ttk.Label(self.summary_card, style='Meta.TLabel')
        self.correct_number_label.grid(row=1, column=1, sticky='e', pady=(6, 0))

        self.prompt_card = tk_ttk.Frame(outer, style='Card.TFrame', padding=22)
        self.prompt_card.grid(row=1, column=0, sticky='nsew', pady=(14, 0))
        self.prompt_card.columnconfigure(0, weight=1)
        self.prompt_card.rowconfigure(0, weight=1)

        self.cue_label = tk_ttk.Label(
            self.prompt_card,
            style='CardBody.TLabel',
            justify=tk.LEFT,
            wraplength=760
        )
        self.cue_label.grid(row=0, column=0, sticky='nw')

        self.feedback_label = tk_ttk.Label(
            self.prompt_card,
            style='CardBody.TLabel',
            justify=tk.LEFT,
            wraplength=760
        )
        self.feedback_label.grid(row=1, column=0, sticky='ew', pady=(20, 0))
        self.feedback_label.configure(text='After your first response, result feedback will appear here.')

        self.other_answers_label = tk_ttk.Label(
            self.prompt_card,
            style='Meta.TLabel',
            justify=tk.LEFT,
            wraplength=760
        )
        self.other_answers_label.grid(row=2, column=0, sticky='ew', pady=(8, 0))

        self.hint_frame = tk_ttk.Frame(self.prompt_card, style='Card.TFrame')
        self.hint_frame.grid(row=3, column=0, sticky='ew', pady=(20, 0))
        self.hint_frame.columnconfigure(1, weight=1)
        self.hint_title_label = tk_ttk.Label(self.hint_frame, text='Hint', style='CardSectionTitle.TLabel')
        self.hint_title_label.grid(row=0, column=0, sticky='nw')
        self.hint_text_label = tk_ttk.Label(
            self.hint_frame,
            style='CardBody.TLabel',
            justify=tk.LEFT,
            wraplength=680
        )
        self.hint_text_label.grid(row=0, column=1, sticky='ew', padx=(12, 0))

        self.response_card = tk_ttk.Frame(outer, style='Card.TFrame', padding=18)
        self.response_card.grid(row=2, column=0, sticky='ew', pady=(14, 0))
        self.response_card.columnconfigure(0, weight=1)

        self.mchoices_frame = tk_ttk.Frame(self.response_card, style='Card.TFrame')
        self.mchoices_frame.grid(row=0, column=0, sticky='ew')
        self.mchoices_frame.columnconfigure(1, weight=1)

        self.response_frame = tk_ttk.Frame(self.response_card, style='Card.TFrame')
        self.response_frame.grid(row=0, column=0, sticky='ew')
        self.response_frame.columnconfigure(0, weight=1)

        self.response_entry = tk_ttk.Entry(self.response_frame)
        self.response_entry.grid(row=0, column=0, sticky='ew')
        self.response_entry.bind('<Key>', self.response_key)
        self.response_entry.bind('<KeyRelease>', self.response_keyrelease)
        self.response_entry.bind('<FocusIn>', self.response_focusin)

        self.button = tk_ttk.Button(
            self.response_frame,
            text='Submit',
            command=self.submit,
            style='Primary.TButton'
        )
        self.button.grid(row=0, column=1, padx=(10, 0))
        self.training_window.bind('<Return>', self.submit)

        self.response_clear()

    def response_key(self, event=None):
        if self.response_entry_placeholder and event.char != '':
            self.response_entry.delete(0, tk.END)
            self.response_entry_placeholder = False

    def response_keyrelease(self, event=None):
        if not self.response_entry_placeholder and len(self.response_entry.get()) == 0:
            self.response_clear()

    def response_focusin(self, event=None):
        if self.response_entry_placeholder:
            self.response_entry.icursor(0)

    def response_clear(self):
        self.response_entry.delete(0, tk.END)
        self.response_entry.insert(0, 'Enter response')
        self.response_entry_placeholder = True
        self.response_entry.icursor(0)

    def clear_mchoices(self):
        if hasattr(self, 'mchoice_buttons'):
            for button in self.mchoice_buttons.values():
                button.destroy()
        if hasattr(self, 'mchoice_labels'):
            for label in self.mchoice_labels.values():
                label.destroy()

    def configure_prompt_area(self):
        if self.settings.level == '1':
            self.response_frame.grid_remove()
            self.mchoices_frame.grid()
            self.hint_frame.grid_remove()
        else:
            self.mchoices_frame.grid_remove()
            self.response_frame.grid()
            self.response_entry.focus_set()

            if self.settings.level == '2':
                self.hint_frame.grid()
            else:
                self.hint_frame.grid_remove()

    def render_question(self):
        question_index = self.mtstatistics.response_number - 1

        self.current_item = self.engine.current_item(question_index)
        self.settings.level = self.current_item.level
        self.settings.current_stage_label = self.current_item.stage_label
        self.question.main_data_loop(
            self.cr_id_pairs[question_index][0],
            self.cr_id_pairs[question_index][1],
            self.mtstatistics
        )

        title_text = self.question.title_text
        if self.engine.session_mode == 'adaptive':
            title_text += ' [' + self.current_item.stage_label + ']'

        self.title_label.configure(text=title_text)
        self.level_label.configure(text=self.question.level_text)
        self.response_number_label.configure(text=self.question.response_number_text)
        self.correct_number_label.configure(text=self.question.correct_so_far_text)
        self.cue_label.configure(text=self.question.cue_text)
        self.configure_prompt_area()

        if self.settings.level == '2':
            self.hint_text_label.configure(text='; '.join(self.question.hints))

        self.clear_mchoices()

        if self.settings.level == '1':
            self.question.mchoices = self.question.generate_mchoices()
            self.mchoice_buttons = {}
            self.mchoice_labels = {}

            for row_index, (letter, choice) in enumerate(self.question.mchoices.items()):
                command = partial(self.submit, mchoice_letter=letter)
                self.training_window.bind(letter, command)

                button = tk_ttk.Button(
                    self.mchoices_frame,
                    text=letter.upper(),
                    command=command,
                    style='Choice.TButton',
                    width=4
                )
                button.grid(row=row_index, column=0, sticky='w', pady=(0, 8))

                label = tk_ttk.Label(
                    self.mchoices_frame,
                    text=choice,
                    style='CardBody.TLabel',
                    wraplength=660
                )
                label.grid(row=row_index, column=1, sticky='w', padx=(12, 0), pady=(0, 8))

                self.mchoice_buttons[letter] = button
                self.mchoice_labels[letter] = label

            self.mchoice_buttons['a'].focus_set()

        self.start_time = time.time()

    def submit(self, event=None, mchoice_letter=None):
        if self.settings.level == '1':
            self.question.user_input = mchoice_letter
        else:
            if self.response_entry_placeholder:
                self.question.user_input = ''
            else:
                self.question.user_input = self.response_entry.get().lower()

        self.question.validate_input()

        if self.mtstatistics.is_input_valid:
            self.end_time = time.time()
            elapsed_time = self.end_time - self.start_time
            self.mtstatistics.times.append(elapsed_time)

            self.question.grade_input()
            self.engine.record_result(self.current_item, self.mtstatistics.is_input_correct, elapsed_time)
            self.question.finalize()

            self.feedback_label.configure(text=self.question.correctness_str)
            if self.mtstatistics.has_synonym_been_used() or self.question.synonyms:
                self.other_answers_label.configure(text=self.question.other_answers_str)
            else:
                self.other_answers_label.configure(text='')
        else:
            tk_messagebox.showinfo(
                'Invalid response',
                'Sorry, your response is not valid. Please try again.',
                parent=self.training_window
            )

        if not self.mtstatistics.is_last_question():
            if self.settings.level != '1':
                self.response_clear()
            self.render_question()
            return

        self.training_window.destroy()

        result = 'Correct: {}/{} ({:.1f}%)\n'.format(
            self.mtstatistics.number_correct,
            self.mtstatistics.total,
            round(self.mtstatistics.percentage, 1)
        )
        result += 'Average response time: {} seconds'.format(
            timedelta(seconds=mean(self.mtstatistics.times))
        )

        if self.mtstatistics.number_incorrect > 0:
            result += '\nResponses for which answers were incorrect: '
            result += self.mtstatistics.incorrect_responses_as_string()

        tk_messagebox.showinfo('Training session complete', result, parent=self.root)

        if self.level == '1':
            self.level_1_button.focus_set()
        elif self.level == '2':
            self.level_2_button.focus_set()
        elif self.level == '3':
            self.level_3_button.focus_set()
        else:
            self.adaptive_button.focus_set()

    def tk_mainloop(self):
        self.root.mainloop()


def main():
    mtgui = MemtrainGUI()
    mtgui.tk_mainloop()


if __name__ == '__main__':
    main()
