#!/usr/bin/python

import sys
import json
import curses
import logging

########################################

class Cell:
	def __init__(self, x, y, value):
		self.x = x
		self.y = y
		self.value = value
		self.constraints = {1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0,9:0}
		self.candidates = { 1:True, 2:True, 3:True, 4:True, 5:True, 6:True, 7:True, 8:True, 9:True}
		self.candidateCount = 9

	def __str__(self):
		return "[" +str(self.x) +"," +str(self.y) +"]" +str(self.value)

	def __repr__(self):
		return self.__str__()

########################################

class Grid:
	def __init__(self):
		self.cells = {}
		for x in range(9):
			for y in range(9):
				self.cells[x,y] = Cell(x, y, None)
		self.numSetCells = 0

	def fill(self, data):
		for y in range(9):
			for x in range(9):
				if data[y][x] > 0:
					self.setCell(x,y, data[y][x])

	def isSolved(self):
		if self.numSetCells == 9*9:
			return True
		else:
			return False

	def setCell(self, x, y, value):
		self.cells[x,y].value = value
		self.numSetCells = self.numSetCells+1

		for i in range(9):
			self.addRestriction(x,i,value)
			self.addRestriction(i,y,value)
		
		for i in range(3):
			for j in range(3):
				self.addRestriction((x/3)*3+i,(y/3)*3+j,value)

	def addRestriction(self,x,y,value):
		cell = self.cells[x,y]
		cell.constraints[value] = cell.constraints[value] + 1
		if cell.candidates[value] == True and cell.constraints[value] > 0:
			cell.candidates[value] = False
			cell.candidateCount = cell.candidateCount - 1

	def unsetCell(self, x, y):		
		value = self.cells[x,y].value
		self.cells[x,y].value = None
		self.numSetCells = self.numSetCells-1

		for i in range(9):
			self.removeRestriction(x,i,value)
			self.removeRestriction(i,y,value)
		
		for i in range(3):
			for j in range(3):
				self.removeRestriction((x/3)*3+i,(y/3)*3+j,value)

	def removeRestriction(self,x,y,value):
		cell = self.cells[x,y]
		cell.constraints[value] = cell.constraints[value] - 1
		if cell.candidates[value] == False and cell.constraints[value] <= 0:
			cell.candidates[value] = True
			cell.candidateCount = cell.candidateCount + 1

########################################

def solve(grid, gr):
	global logging, iterations

	if grid.isSolved():
		gr.render()
		sys.exit()

	#interactionLoop(gr)
	#gr.render()
	iterations = iterations +1
	gr.iterations = iterations

	smallestCell = None
	smallestCount = 10

	for x in range(9):
		for y in range(9):
			if grid.cells[x,y].value == None and grid.cells[x,y].candidateCount < smallestCount:
				smallestCount = grid.cells[x,y].candidateCount
				smallestCell = grid.cells[x,y]
				if smallestCount == 1:
					break
		if smallestCount == 1:
			break

	for c in range(1,10):
		if smallestCell.candidates[c] == True:
			grid.setCell(smallestCell.x,smallestCell.y,c)
			solve(grid,gr)
			grid.unsetCell(smallestCell.x,smallestCell.y)

########################################

class GridRenderer:
	def __init__(self, grid):
		global screen
		self.grid = grid
		self.xscale = 4
		self.yscale = 2
		self.cursorX = 0
		self.cursorY = 0
		self.iterations = 0

		self.gridWindow = curses.newwin(10*self.yscale+1, 10*self.xscale+1, 0, 0)
		(maxY, maxX) = screen.getmaxyx()
		(offY, offX) = self.gridWindow.getmaxyx()
		self.infoWindow = curses.newwin(maxY, maxX-offX, 0, offX)

	def plot(self, x, y, text, color):
		self.gridWindow.addstr(y,x,text,curses.color_pair(color))

	def render(self):
		self.gridWindow.clear()
		self.infoWindow.clear()
		self._renderGrid()
		self._renderInfo()
		self.gridWindow.refresh()
		self.infoWindow.refresh()

	def _renderGrid(self):
		sx = self.xscale
		sy = self.yscale

		for i in range(9*sx+1):
			for j in range(9*sy+1):
				if i % (3*sx) == 0 or j % (3*sy) == 0:
					c = 1
				else:
					c = 2

				if i%sx == 0 or j%sy == 0:
					if i%sx == 0 and j%sy == 0:
						self.plot(i,j,'+',c)
					else:
						if j%sy:
							self.plot(i,j,'|',c)
						else:
							self.plot(i,j,'-',c)
			
		for x in range(9):
			for y in range(9):
				cellValue = self.grid.cells[x,y].value
				if cellValue == None:
					cellValue = ' '
				self.plot(x*sx+sx/2, y*sy+sy/2, str(cellValue), 3)

		cellValue = self.grid.cells[self.cursorX,self.cursorY].value
		if cellValue == None:
			cellValue = ' '

		self.plot(self.cursorX*sx+sx/2, self.cursorY*sy+sy/2, str(cellValue), 4)

	def _renderInfo(self):
		global logging

		x = self.cursorX
		y = self.cursorY
		w = self.infoWindow
		w.addstr(0,0,"Cell [" +str(x) +"," +str(y) +"]")
		w.addstr(0,15,"i=" +str(self.iterations))
		
		c = self.grid.cells[x,y]
		for i in range(1,10):
			w.addstr(1+i,2, str(i)+":")
			w.addstr(1+i,6, str(c.candidates[i]))
			w.addstr(1+i,14, str(c.constraints[i]))

########################################

def interactionLoop(gr):
	global screen

	while 1:
		gr.render()

		c = screen.getch()
		if c == ord('q'):
			sys.exit()
		elif c == ord('n'):
			break

		elif c == curses.KEY_LEFT and gr.cursorX>0:
			gr.cursorX = gr.cursorX -1
		elif c == curses.KEY_RIGHT and gr.cursorX<8:
			gr.cursorX = gr.cursorX + 1
		elif c == curses.KEY_UP and gr.cursorY>0:
			gr.cursorY = gr.cursorY - 1
		elif c == curses.KEY_DOWN and gr.cursorY<8:
			gr.cursorY = gr.cursorY + 1

########################################

def f2per(f):
	return "{0:.0f}".format(float(f) * 100)

########################################

iterations = 0

try:
	logging.basicConfig(filename="output.log", format='%(message)s', level=logging.INFO)

	screen = curses.initscr()
	curses.start_color()
	curses.use_default_colors()
	curses.init_pair(1, curses.COLOR_YELLOW, -1)
	curses.init_pair(2, curses.COLOR_BLUE, -1)
	curses.init_pair(3, curses.COLOR_WHITE, -1)
	curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
	curses.noecho()
	curses.cbreak()
	
	screen.keypad(1)
	screen.refresh()
	
	g = Grid()
	
	'''d = [
			[0,0,0, 0,0,0, 0,0,0],
			[0,0,0, 0,0,0, 0,0,0],
			[0,0,0, 0,0,0, 0,0,0],

			[0,0,0, 0,0,0, 0,0,0],
			[0,0,0, 0,0,0, 0,0,0],
			[0,0,0, 0,0,0, 0,0,0],

			[0,0,0, 0,0,0, 0,0,0],
			[0,0,0, 0,0,0, 0,0,0],
			[0,0,0, 0,0,0, 0,0,0]
	]

	d = [
			[0,2,8, 0,5,0, 0,0,1],
			[1,0,0, 0,3,0, 0,0,0],
			[0,0,9, 0,0,0, 0,0,4],

			[0,7,0, 6,0,0, 2,0,0],
			[0,6,0, 9,1,5, 0,7,0],
			[0,0,3, 0,0,2, 0,6,0],

			[3,0,0, 0,0,0, 5,0,0],
			[0,0,0, 0,7,0, 0,0,8],
			[2,0,0, 0,6,0, 9,3,0]
	]

	g.fill(d)
'''

	gr = GridRenderer(g)
	
	solve(g,gr)

finally:
	curses.nocbreak()
	screen.keypad(0)
	curses.echo()
	curses.endwin()