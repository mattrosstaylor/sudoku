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

		for x in xrange(0,9*sx,sx):
			for y in xrange(0,9*sy,sy):
				for i in range(1,sx):
					screen.addch(y,x+i,'-')
					screen.addch(y+sy,x+i,'-')
				for i in range(1,sy):
					screen.addch(y+i,x,'|')
					screen.addch(y+i,x+sx,'|')

		for pen in self.json['pens']:
			total = pen[0]
			for cell1 in pen[1]:
				for cell2 in pen[1]:
					self.removeLineBetween(cell1,cell2)
			screen.addstr(int(pen[1][0][0])*sy,int(pen[1][0][1])*sx+1,str(pen[0]))
	
		for x in xrange(0,9*sx,sx):
			for y in xrange(0,9*sy,sy):
				screen.addch(y,x, '+')
				screen.addch(y+sy,x, '+')
				screen.addch(y,x+sx, '+')
				screen.addch(y+sy, x+sx, '+')
		
		for x in range(9):
			for y in range(9):
				screen.addch(y*sy+sy/2, x*sx+sx/2, str(1))

	def removeLineBetween(self,cell1,cell2):
		global screen, log
		sx = self.xscale
		sy = self.yscale

		x1 = cell1[1]
		y1 = cell1[0]
		x2 = cell2[1]
		y2 = cell2[0]

		if x1 == x2:
			if y2 == y1+1:
				for i in range(sx):
					screen.addch((y1+1)*sy, x1*sx+i, ' ')

		if y1 == y2:
			if x2 == x1+1:
				for i in range(sy):
					screen.addch(y1*sy+i, (x1+1)*sx, ' ')


try:
	logging.basicConfig(filename="output.log", format='%(message)s', level=logging.INFO)
	logging.info("************")

	screen = curses.initscr()

	g = Grid(json.load(open(sys.argv[1])))
	g.render()
finally:
	screen.refresh()
	#screen.getch()
	curses.endwin()

