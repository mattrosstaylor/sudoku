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

	def render(self):
		global screen,log
		sx = self.xscale
		sy = self.yscale

		for x in xrange(0, 9*sx, sx):
			for y in xrange(0, 9*sy, sy):
				for i in range(1, sx):
					screen.addch(y, x+i, '-', curses.color_pair(1))
					screen.addch(y+sy, x+i, '-', curses.color_pair(1))
				for i in range(1, sy):
					screen.addch(y+i, x, '|',curses.color_pair(1))
					screen.addch(y+i, x+sx, '|',curses.color_pair(1))

		for pen in self.json['pens']:
			total = pen[0]
			for cell1 in pen[1]:
				for cell2 in pen[1]:
					self.removeLineBetween(cell1, cell2)
			screen.addstr(int(pen[1][0][0])*sy, int(pen[1][0][1])*sx+1, str(pen[0]), curses.color_pair(2))
	
		for x in xrange(0,9*sx,sx):
			for y in xrange(0,9*sy,sy):
				screen.addch(y, x, '+', curses.color_pair(1))
				screen.addch(y+sy, x, '+', curses.color_pair(1))
				screen.addch(y, x+sx, '+', curses.color_pair(1))
				screen.addch(y+sy, x+sx, '+', curses.color_pair(1))
		
		for x in range(9):
			for y in range(9):
				screen.addch(y*sy+sy/2, x*sx+sx/2, str(1), curses.color_pair(3))

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
					screen.addch((y1+1)*sy, x1*sx+i, ' ')

		if y1 == y2 and x2 == x1+1:
				for i in range(sy):
					screen.addch(y1*sy+i, (x1+1)*sx, ' ')


try:
	logging.basicConfig(filename="output.log", format='%(message)s', level=logging.INFO)
	logging.info("************")

	screen = curses.initscr()
	curses.start_color()
	curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)

	g = Grid(json.load(open(sys.argv[1])))
	g.render()
finally:
	screen.refresh()
	#screen.getch()
	curses.endwin()

