import os
from my_frame import MyFrame
import ttk
from Tkinter import *
from ttk import *

class HelpWindow(MyFrame):
    def __init__(self,topframe= None):
        MyFrame.__init__(self, topframe=None)
        s = ttk.Style()
        s.theme_use('clam')

	self.set_title('Help')
	self.scrollbar = Scrollbar(self)
	self.scrollbar.pack(side=RIGHT, fill=Y)

	self.text_view = Text(self)
        self.text_view.pack()

	# attach listbox to scrollbar
	self.text_view.config(yscrollcommand=self.scrollbar.set)
	self.scrollbar.config(command=self.text_view.yview)


        f = open('help.txt', 'r')
        text = f.read()
        self.text_view.insert(END, text)
	
