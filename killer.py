#!/usr/bin/python

import sys
import json
import curses
import logging

class Grid:
	def __init__(self, json_spec):
		self.json = json_spec
		self.xscale = 4
		self.yscale = 2

	def plot(self, x, y, text, color):
		global screen
		screen.addstr(y,x,text,curses.color_pair(color))

	def render(self):
		sx = self.xscale
		sy = self.yscale

		for x in xrange(0, 9*sx, sx):
			for y in xrange(0, 9*sy, sy):
				for i in range(1, sx):
					self.plot(x+i, y, '-', 1)
					self.plot(x+i, y+sy, '-', 1)
				for i in range(1, sy):
					self.plot(x, y+i, '|', 1)
					self.plot(x+sx, y+i, '|', 1)

		for pen in self.json['pens']:
			total = pen[0]
			for cell1 in pen[1]:
				for cell2 in pen[1]:
					self.removeLineBetween(cell1, cell2)
			self.plot(int(pen[1][0][1])*sx+1, int(pen[1][0][0])*sy, str(pen[0]), 2)
	
		for x in xrange(0,10*sx,sx):
			for y in xrange(0,10*sy,sy):
				self.plot(x,y,'+', 1)
		
		for x in range(9):
			for y in range(9):
				self.plot(x*sx+sx/2, y*sy+sy/2, str(2), 3)

	def removeLineBetween(self,cell1,cell2):
		global screen, log
		sx = self.xscale
		sy = self.yscale

		x1 = cell1[1]
		y1 = cell1[0]
		x2 = cell2[1]
		y2 = cell2[0]

		if x1 == x2 and y2 == y1+1:
				for i in range(sx):
					self.plot(x1*sx+i, (y1+1)*sy, ' ', 1)

		if y1 == y2 and x2 == x1+1:
				for i in range(sy):
					self.plot((x1+1)*sx, y1*sy+i, ' ', 1)

try:
	logging.basicConfig(filename="output.log", format='%(message)s', level=logging.INFO)

	screen = curses.initscr()
	curses.start_color()
	curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)

	g = Grid(json.load(open(sys.argv[1])))
	g.render()
finally:
	screen.refresh()
	curses.endwin()

