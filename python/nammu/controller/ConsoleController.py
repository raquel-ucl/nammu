'''
Created on 15 Apr 2015

Creates the console view and handles console actions.

@author: raquel-ucl
'''

from ..view.ConsoleView import ConsoleView

class ConsoleController():
    
    def __init__(self, mainControler):
        print "I'm the console controller"
        
        #Create view with a reference to its controller to handle events
        self.view = ConsoleView(self)
        
        #Will also need delegating to parent presenter
        self.controller = mainControler