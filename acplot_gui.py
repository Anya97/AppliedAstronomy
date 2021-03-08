#!/usr/bin/env python
# -*- coding: utf-8 -*-

# simple PuQt based gui to plot spectrum density from base files
# openDialog, keyPressEvents, inline matplotlib widget
# with emojies support 😎 f-yeah!
# debug with ipython --gui=qt4
# a = acplot()
# s.show()
# TESTING!

# Author: harmless, mailto: mishin@iaaras.ru or use gitlab project page for feedback
# Have a nice day!

# TODO: re-make PyQt imports!

import sys  # will need that at least at app.exec_()
import os
# PyQt for widgets and such
# may be we should remove * imports for better debug and normal linting
from PyQt4.QtCore import *
from PyQt4.QtGui import *
# matplotlib-related for embedded graphs:
import numpy as np
from matplotlib.figure import Figure
# from matplotlib.backend_bases import key_press_handler we'll not overload Qt keys
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
# from matplotlib.backends import qt4_compat

# our own imports:
import basefile


class acplot(QWidget):
    """docstring for acplot based on QWidget"""
    def __init__(self, parent=None):  # as main window widget
        # basic init, title-size e.t.c.
        # super(acplot,QWidget.__init__(self, parent)) check it!
        QWidget.__init__(self, parent)
        self.setWindowTitle('Spectrum density plot')
        self.resize(800, 600)
        # widgets & layout:
        self.flbl = QLabel('Filename: will be here, once something opened')
        self.apnum = QLabel('Current AP: change value with up/down keys')
        # we'll access this later so self should do the trick
        opnbtn = QPushButton("Open")
        # svbtn = QPushButton("Save") # not needed if using mpl, got one in bar
        exbtn = QPushButton("Exit")
        # matplotlib widget:
        self.create_mpl_frame()
        # connects here:
        self.connect(opnbtn, SIGNAL('clicked()'), self.opendlg)
        # below should work as qApp, SLOT('quit()') -> yep, that worked on debug
        # quit() hangs the entire ipython gui loop, that's not acceptable.
        self.connect(exbtn, SIGNAL('clicked()'), SLOT('close()'))
        # vbox = QVBoxLayout() vbox and hbox works the same way
        # vbox.addWidget(opnbtn)
        grid = QGridLayout()  # assuming 6 by 3 grid
        grid.setSpacing(10)  # test it!
        grid.addWidget(self.flbl, 1, 0)
        grid.addWidget(self.apnum, 1, 2)
        grid.addWidget(self.mpl_frame, 2, 0, 4, 3) 
        grid.addWidget(opnbtn, 6, 0)
        # grid.addWidget(svbtn, 6, 1)
        grid.addWidget(exbtn, 6, 2)
        # clearing figure:
        # self.fig.clf() - we shouldn't remove axis
        # no need to self for child objects, as vbox will be pinned to self, nice!
        self.setLayout(grid)

        # internal vars
        self.lastdir = '/' 
        self.fname = ''
        self.current = 0
        self.bd = None

    def create_mpl_frame(self):
        self.mpl_frame = QWidget()

        self.fig = Figure((5.0, 4.0), dpi=100)
        self.axes = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.mpl_frame)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()

        self.mpl_toolbar = NavigationToolbar(self.canvas, self.mpl_frame)

        # self.canvas.mpl_connect('key_press_event', self.on_key_press) - debug key values
        # we overload default QWidget keyPressEvent
        self.canvas.mpl_connect('key_press_event', self.keyPressEvent)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)  # the matplotlib canvas
        vbox.addWidget(self.mpl_toolbar)
        self.mpl_frame.setLayout(vbox)
        # self.setCentralWidget(self.mpl_frame)

    def on_draw(self):
        pass
        # placeholder, use on plot & resize
        '''self.fig.clear()
        self.axes = self.fig.add_subplot(111)
        #self.axes.plot(self.x, self.y, 'ro')
        self.axes.imshow(self.data, interpolation='nearest')
        #self.axes.plot([1,2,3])
        self.canvas.draw()'''

    def opendlg(self):
        newname = QFileDialog.getOpenFileName(self, 'Open file', self.lastdir,
                                              'Base files (*.base)')
        if newname == '':
            self.canvas.setFocus()
            return
        self.fname = newname
        # do the stuff here
        # update last dir
        # ONCE USED BY QT str becomes QString!!!!
        # convert back to use python string functions and such.
        self.lastdir = os.path.dirname(str(self.fname))
        print ' Now using directory:', self.lastdir
        self.flbl.setText(self.fname)
        self.apnum.setText('Current AP: 0')
        # print 'Label updated to:', self.flbl.text()
        self.bd = basefile.loadMulti(str(self.fname), True)  # will disable it once done
        self.current = 0
        self.maxap = 0
        self.plot()
        self.canvas.setFocus()  # not to loose focus on mpl plot

    def plot(self):
        chan = 1
        data, chans, res, periods, sess, ascan, ast1, ast2 = self.bd[0:8]  # initial data
        bandwidth = 16.0
        self.maxap = periods
        step = bandwidth / res
        x = np.arange(0, bandwidth, step)
        # xt = np.arange(0, bandwidth, 0.5) fix xticks may be?
        rep = abs(data[chan, self.current])
        # self.fig.clf() - entyre fig
        # self.fig.cla() - axis clean up
        self.axes.cla()
        self.axes.plot(x, rep)
        # self.axes.xticks(xt, rotation=90) xticks on subplot???
        self.canvas.draw()  # some layout glitches here

    # placeholder for keyPressEvent on mpl toolbar or graph, we'll not use it for now
    def on_key_press(self, event):
        print('you clicked', event.key)  # just to see if we can access here
        # debugging, later on we'll update keyPressEvent!
        # implement the default mpl key press events described at
        # http://matplotlib.org/users/navigation_toolbar.html#navigation-keyboard-shortcuts
        # key_press_handler(event, self.canvas, self.mpl_toolbar)
    # MPL intercept key handling with different key values 😒

    def keyPressEvent(self, event):
        # if event.key() == Qt.Key_Up or event.key == u'up':
        # first one works with pure PyQt, second one from mpl keys handler!!!
        print('you pressed', event.key)
        # We'll use backup numpad keys, as older matplotlib can't handle arrow keys :(
        # if event.key == Qt.Key_Up or event.key == u'up' or event.key == '8':
        if event.key == u'up' or event.key == '8':
            print 'Key_Up pressed - next AP'
            if self.bd is None:
                return
            self.current += 10
            if self.current > self.maxap:
                self.current = self.maxap
            self.apnum.setText('Current AP: %d' % self.current)
            self.plot()
        # if event.key == Qt.Key_Down or event.key == u'down' or event.key == '2':
        if event.key == u'down' or event.key == '2':
            print 'Key_Down pressed - prev AP'
            if self.bd is None:
                return
            self.current -= 10
            if self.current < 0:
                self.current = 0
            self.apnum.setText('Current AP: %d' % self.current)
            self.plot()
        if event.key == Qt.Key_O or event.key == u'o':  # no register check, be warned!
            print 'Key_o pressed - openDialog here'
            self.opendlg()
        if event.key == Qt.Key_Escape or event.key == u'escape':
            print 'Key_Escape pressed - exit here'
        if event.key == Qt.Key_Enter or event.key == u'enter':
            print 'Key_Enter pressed - update plot'  # not to re-plot on any change in lineEdit

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ap = acplot()
    ap.show()
    sys.exit(app.exec_())
