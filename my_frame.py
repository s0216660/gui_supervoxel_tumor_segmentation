'''
Created on Apr 27, 2016

@author: alberts
'''
from Tkinter import *
from ttk import *

class MyFrame(Frame):
    
    def __init__(self, topframe=None):

        # Create master
        if topframe is None:
            self.master = Toplevel()
        else:
            self.master = topframe
        self.master.resizable(width=False, height=False)
        # Create main frame
        Frame.__init__(self, self.master,  padding="3 3 3 3")
        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()
        self.pack()
        
        # Set a bit of style
        self._imStyle = Style()
        self._imStyle.configure("Red.TFrame", background="green")
    
    def set_title(self, title):
        """ Set the title of the main widget. """
        
        self.master.title(title)
        
    def start(self):
        """ Start the main widget. """
        
        self.master.mainloop()
        
    def quit(self, terminal=False):
        """Quit this gui widget, if terminal, also quit code execution."""
        
        sub_frames = [attr for attr in vars(self) 
                      if isinstance(getattr(self,attr),
                                    Toplevel)]
        for sub_frame in sub_frames:
            if sub_frame != 'master':
                getattr(self,sub_frame).destroy()
            
        self.update_idletasks()
        self.master.destroy()
        
        if terminal:
            sys.exit()
        

