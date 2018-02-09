from Tkinter import  *
from ttk import *

class LinkedScrollBar(Scrollbar):
    """**Wrapper class for the Tkinter Scrollbar that links it with a value that has a given range**
    
    Members:
    
    - *_minVal* : minimum value of the scroll bar
    - *_maxVal* : maximum value of the scroll bar
    - *_initVal*: initialization method. Can be either *'mid'* or *'max'*
    - *_step*: amount by which the value is increased/decreased when clicking on the arrows 
    - *_sliderWidth*: width of the slider as a percentage of the scroll bar
    - *_actualise*: method to call when the slider is moved
    - *val* current value
    """
    
    def __init__(self, minVal=0,  maxVal=1024,   width=0.05,  initVal='mid', step=1,  command=None,  master=None,  **args):
        Scrollbar.__init__(self,  master,  command=self._adjust,  **args)
        self._minVal=minVal
        if maxVal==minVal:
            self._maxVal=minVal+1
        else:
            self._maxVal=maxVal
        self._initVal=initVal
        self._step=step
        self._sliderWidth=width
        self._actualise=command
        
            
    def _adjust(self,  *args):
        """used when the scrollabr is moved to change the value of the variable"""
        if len(args)==3:
            direction=int(args[1])
            self.val=self.val+direction*self._step
        elif  len(args)==2:
            self.val=self._minVal+float(args[1])*(self._maxVal-self._minVal)
        self.val=min(self.val, self._maxVal)
        self.val=max(self.val, self._minVal)
        self._set_slider()
        self._actualise()
        
    def set_value(self,  val):
        """used to change the value of the scrollbar"""
        self.val=min(val, self._maxVal)
        self.val=max(val, self._minVal)
        self._set_slider()
        self._actualise()
        
    def _set_slider(self):
        """sets the position of the slider according to the value of the variable"""
        #move slider
        xn=(1-self._sliderWidth)*(self.val-self._minVal)/(self._maxVal-self._minVal)
        self.set(xn, xn+0.05)
        
    def reset(self,  maxVal=None,  minVal=None):
        """resets the value of the variable to its default and sets the slider accordingly"""
        if not (minVal is None):
            self._minVal=minVal
        if not (maxVal is None):
            self._maxVal=maxVal
            if maxVal==self._minVal:
                self._maxVal=self._minVal+1
        if self._initVal is 'mid':
            self.val=self._minVal+0.5*(self._maxVal-self._minVal)
        elif self._initVal=='max':
            self.val=self._maxVal
        else:
            raise AttributeError("This initialisation method doesn't exist")
        self._set_slider()
