'''
Created on 15 Apr 2015

Initializes the ATF (edit/model) view and sets its layout.

@author: raquel-ucl
'''

import re
from java.awt import Font, BorderLayout, Dimension, Color
from java.awt.event import KeyListener
from javax.swing import JTextPane, JScrollPane, JPanel, BorderFactory
from javax.swing.text import DefaultHighlighter, StyleContext, StyleConstants
from javax.swing.text import SimpleAttributeSet, AbstractDocument
from javax.swing.undo import UndoManager
from javax.swing.event import UndoableEditListener
from pyoracc.atf.atflex import AtfLexer
from .AtfEditArea import AtfEditArea
from .LineNumbersArea import LineNumbersArea


class AtfAreaView(JPanel):

    def __init__(self, controller):
        '''
        Creates default empty text area in a panel for ATF edition.
        It has syntax highlighting based on the ATF parser (pyoracc).
        It also highlights line numbers where there are validations errors
        returned by the ORACC server.
        '''
        # Give reference to controller to delegate action response
        self.controller = controller

        # Make text area occupy all available space and resize with parent
        # window
        self.setLayout(BorderLayout())

        # Create text edition area
        self.editArea = AtfEditArea(self)

        # Create text panel to display the line numbers
        self.line_numbers_area = LineNumbersArea()

        # Needed by syntax highlighter
        self.edit_area_styledoc = self.editArea.getStyledDocument()
        self.line_numbers_styledoc = self.line_numbers_area.getStyledDocument()

        # Set undo/redo manager to edit area
        self.undo_manager = UndoManager()
        self.undo_manager.limit = 3000
        self.edit_listener = AtfUndoableEditListener(self.undo_manager)
        self.editArea.getDocument().addUndoableEditListener(self.edit_listener)

        # Create panel that'll contain the ScrollPane and the line numbers
        container = JPanel(BorderLayout())
        container.add(self.editArea, BorderLayout.CENTER)
        container.add(self.line_numbers_area, BorderLayout.WEST)

        # Will need scrolling controls that scroll line numbers and text lines
        # simultaneously
        scrollingText = JScrollPane(container)
        scrollingText.setPreferredSize(Dimension(1, 500))
        scrollingText.getVerticalScrollBar().setUnitIncrement(16)

        # Add to parent panel
        self.add(scrollingText, BorderLayout.CENTER)

        # Syntax highlight setup
        sc = StyleContext.getDefaultStyleContext()
        self.colorlut = self.create_syntax_highlight_colorlut()
        self.colors = {}
        for color in self.colorlut:
            self.colors[color] = sc.addAttribute(
                                           SimpleAttributeSet.EMPTY,
                                           StyleConstants.Foreground,
                                           Color(*self.colorlut[color]))
        self.editArea.addKeyListener(AtfAreaKeyListener(self))
        self.setup_syntax_highlight_tokens()

        # Needs to be accessible from the AtfEditArea
        self.validation_errors = None


    def error_highlight(self, validation_errors):
        """
        Highlights line numbers and text lines that have errors.
        Receives a dictionary with line numbers and error messages and repaints
        the line numbers and text lines to highlight errors.
        """
        if validation_errors:
            self.validation_errors = validation_errors
            for line_num, error in validation_errors.items():
                attribs = SimpleAttributeSet()
                StyleConstants.setFontFamily(attribs, "Monaco")
                StyleConstants.setFontSize(attribs, 14)
                StyleConstants.setForeground(attribs, Color.red)
                line_numbers_sd = self.line_numbers_area.getStyledDocument()
                edit_area_sd = self.editArea.getStyledDocument()

                text = self.line_numbers_area.text

                # Search for start position and length of line number
                if line_num in text:
                    match = re.search(line_num, text)
                    # This will return the position of the first substring
                    # matching the line num, so we won't run into problems like
                    # getting 122 when we are searching for 12 or 22.
                    position = match.start()
                    # Line numbers are as long as the number + 1 becase it is
                    # followed by a colon
                    length = len(line_num) + 1
                    # Change style in line number panel
                    line_numbers_sd.setCharacterAttributes(position,
                                                           length,
                                                           attribs,
                                                           True)

                    # Calculate postion of text line
                    # text_lines = self.editArea.text.splitlines()
                    # text_line = text_lines[int(line_num) - 1]
                    # match = re.finditer('\n', self.editArea.text)[int(line_num) - 1]
                    position = [m.start() for m in re.finditer(r"\n", self.editArea.text)][int(line_num) - 2:int(line_num)]
                    length = position[1] - position[0]
                    # Highlight text line
                    attribs = SimpleAttributeSet()
                    StyleConstants.setFontFamily(attribs, "Monaco")
                    StyleConstants.setFontSize(attribs, 14)
                    StyleConstants.setBackground(attribs, Color.yellow)
                    edit_area_sd.setCharacterAttributes(position[0],
                                                        length,
                                                        attribs,
                                                        True)


    def syntax_highlight(self):
        """
        Implements syntax highlighting based on pyoracc.
        """
        lexer = AtfLexer(skipinvalid=True).lexer
        text = self.editArea.text
        splittext = text.split('\n')
        lexer.input(text)
        # Reset all styling
        defaultcolor = self.tokencolorlu['default'][0]
        self.edit_area_styledoc.setCharacterAttributes(0, len(text),
                                                    self.colors[defaultcolor],
                                                    True)
        for tok in lexer:
            if tok.type in self.tokencolorlu:
                if type(self.tokencolorlu[tok.type]) is dict:
                    # the token should be styled differently depending
                    # on state
                    try:
                        state = lexer.current_state()
                        color = self.tokencolorlu[tok.type][state][0]
                        styleline = self.tokencolorlu[tok.type][state][1]
                    except KeyError:
                        color = self.tokencolorlu['default'][0]
                        styleline = self.tokencolorlu['default'][1]
                else:
                    color = self.tokencolorlu[tok.type][0]
                    styleline = self.tokencolorlu[tok.type][1]
                if styleline:
                    mylength = len(splittext[tok.lineno-1])
                else:
                    mylength = len(tok.value)
                self.edit_area_styledoc.setCharacterAttributes(tok.lexpos, mylength,
                                                     self.colors[color],
                                                     True)


    def create_syntax_highlight_colorlut(self):
        """
        Returns color lookup table for syntax highlighting.
        """
        # Syntax highlighting colors based on SOLARIZED
        colorlut = {}

        # Black backgroud tones
        colorlut['base03'] = (0, 43, 54)
        colorlut['base02'] = (7, 54, 66)

        # Content tones
        colorlut['base01'] = (88, 110, 117)
        colorlut['base00'] = (101, 123, 131)
        colorlut['base0'] = (131, 148, 150)
        colorlut['base1'] = (147, 161, 161)

        # White background tones
        colorlut['base2'] = (238, 232, 213)
        colorlut['base3'] = (253, 246, 227)

        # Accent Colors
        colorlut['yellow'] = (181, 137, 0)
        colorlut['orange'] = (203, 75, 22)
        colorlut['red'] = (220,  50, 47)
        colorlut['magenta'] = (211,  54, 130)
        colorlut['violet'] = (108, 113, 196)
        colorlut['blue'] = (38, 139, 210)
        colorlut['cyan'] = (42, 161, 152)
        colorlut['green'] = (133, 153, 0)
        colorlut['black'] = (0, 0, 0)
        
        return colorlut


    def setup_syntax_highlight_tokens(self):
        self.tokencolorlu = {}
        self.tokencolorlu['AMPERSAND'] = ('green', True)
        for i in AtfLexer.protocols:
            self.tokencolorlu[i] = ('magenta', False)
        for i in AtfLexer.protocol_keywords:
            self.tokencolorlu[i] = ('magenta', False)
        for i in AtfLexer.structures:
            self.tokencolorlu[i] = ('violet', False)
        for i in AtfLexer.long_argument_structures:
            self.tokencolorlu[i] = ('violet', False)
        self.tokencolorlu['DOLLAR'] = ('orange', False)
        for i in AtfLexer.dollar_keywords:
            self.tokencolorlu[i] = ('orange', False)
        self.tokencolorlu['REFERENCE'] = ('base01', False)
        self.tokencolorlu['COMMENT'] = ('base1', True)
        for i in AtfLexer.translation_keywords:
            self.tokencolorlu[i] = ('green', False)
        self.tokencolorlu['LINELABEL'] = ('yellow', False)
        self.tokencolorlu['LEM'] = ('red', False)
        self.tokencolorlu['SEMICOLON'] = ('red', False)
        self.tokencolorlu['HAT'] = ('cyan', False)

        self.tokencolorlu['NOTE'] = {}
        self.tokencolorlu['NOTE']['flagged'] = ('violet', False)
        self.tokencolorlu['NOTE']['para'] = ('magenta', False)

        self.tokencolorlu['PROJECT'] = {}
        self.tokencolorlu['PROJECT']['flagged'] = ('magenta', False)
        self.tokencolorlu['PROJECT']['transctrl'] = ('green', False)
        self.tokencolorlu['default'] = ('black', False)

    def repaint_line_numbers(self, n_lines):
        """
        Draws line numbers in corresponding panel.
        """
        # Create line numbers
        numbers = ""
        for line in range(n_lines + 1):
            numbers += str(line + 1) + ": \n"

        # Print in line numbers' area
        self.line_numbers_area.setText(numbers)


class AtfAreaKeyListener(KeyListener):
    """
    Listens for user releasing keys to reload the syntax highlighting and the
    line numbers (they'll need to be redrawn when a new line or block is added
    or removed).
    """
    def __init__(self, atfareaview):
        self.atfareaview = atfareaview

    def keyReleased(self, ke):
        self.atfareaview.syntax_highlight()
        # Check length hasn't changed, otherwise repaint line numbers
        number_lines = self.atfareaview.line_numbers_area.text.count('\n')
        text_lines = self.atfareaview.editArea.text.count('\n')
        if number_lines - 1 != text_lines:
            self.atfareaview.repaint_line_numbers(text_lines)

    # We have to implement these since the baseclass versions
    # raise non implemented errors when called by the event.
    def keyPressed(self, ke):
        pass

    def keyTyped(self, ke):
        # It would be more natural to use this event. However
        # this gives the string before typing
        pass


class AtfUndoableEditListener(UndoableEditListener):
    '''
    Overrides the undoableEditHappened functionality to only count INSERT type
    events instead of capturing other changes and events like highlighting, etc.
    '''
    def __init__(self, undo_manager):
        self.undo_manager = undo_manager

    def undoableEditHappened(self, event):
        edit = event.getEdit()
        edit_type = edit.getType()

        if (str(edit_type) == "INSERT" or str(edit_type) == "REMOVE") and edit.significant:
            self.undo_manager.addEdit(edit)
