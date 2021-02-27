import tkinter as tk

class memtrain_gui:
    def __init__(self):
        '''Construct the GUI interface'''
        self.root = tk.Tk()
        self.root.title('memtrain v0.3a')

        # Upper area ##########################################################
        self.upper = tk.Frame(master=self.root)
        self.upper.columnconfigure(0, weight=1)
        self.upper.columnconfigure(1, weight=1)

        self.title = tk.Frame(master=self.upper)
        self.title.grid(column=0, row=0, sticky='nsew', rowspan=2)
        self.title_label = tk.Label(master=self.title, text='Test title', anchor='w')
        self.title_label.pack(fill=tk.BOTH, expand=tk.YES)

        self.level = tk.Frame(master=self.upper)
        self.level.grid(column=1, row=0, sticky='nsew')
        self.level_label = tk.Label(master=self.level, text='Level 3', anchor='e')
        self.level_label.pack(fill=tk.X)

        self.total = tk.Frame(master=self.upper)
        self.total.grid(column=1, row=1, sticky='nsew')
        self.total_label = tk.Label(master=self.total, text='Response 1/25', anchor='e')
        self.total_label.pack(fill=tk.X)

        self.upper.pack(fill=tk.X, expand=tk.YES)

        # Middle area #########################################################
        self.middle = tk.Frame(master=self.root)

        self.question = tk.Text(master=self.middle, width=75, height=8)
        self.question.configure(font=('Arial', 10))
        self.question.insert(tk.END, 'This is the text of the question.')
        self.question.pack()

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

    def activate_mainloop(self):
        self.root.mainloop()

mtgui = memtrain_gui()
mtgui.activate_mainloop()
