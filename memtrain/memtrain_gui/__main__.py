import tkinter as tk

root = tk.Tk()
root.title('memtrain v0.3a')

# Upper area ##################################################################
upper = tk.Frame(master=root)
upper.columnconfigure(0, weight=1)
upper.columnconfigure(1, weight=1)

title = tk.Frame(master=upper)
title.grid(column=0, row=0, sticky='nsew', rowspan=2)
title_label = tk.Label(master=title, text='Test title', anchor='w')
title_label.pack(fill=tk.BOTH, expand=tk.YES)

level = tk.Frame(master=upper)
level.grid(column=1, row=0, sticky='nsew')
level_label = tk.Label(master=level, text='Level 3', anchor='e')
level_label.pack(fill=tk.X)

total = tk.Frame(master=upper)
total.grid(column=1, row=1, sticky='nsew')
total_label = tk.Label(master=total, text='Response 1/25', anchor='e')
total_label.pack(fill=tk.X)

upper.pack(fill=tk.X, expand=tk.YES)

# Middle area #################################################################
middle = tk.Frame(master=root)

question = tk.Text(master=middle, width=75, height=8)
question.configure(font=('Arial', 10))
question.insert(tk.END, 'This is the text of the question.')
question.pack()

middle.pack()

# Bottom area #################################################################
bottom = tk.Frame(master=root)
bottom.columnconfigure(0, weight=1)

response = tk.Entry(master=bottom, font='Arial 9 italic')
response.insert(0, 'Enter response')
response.grid(column=0, row=0, sticky='nsew')

button = tk.Button(master=bottom, text='Go', bg='green', fg='white', padx=10)
button.grid(column=1, row=0)

bottom.pack(fill=tk.X)

root.mainloop()
