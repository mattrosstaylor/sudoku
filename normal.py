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
			self.removeCandidate(x,i,value)
			self.removeCandidate(i,y,value)
		
		for i in range(3):
			for j in range(3):
				self.removeCandidate((x/3)*3+i,(y/3)*3+j,value)

	def removeCandidate(self,x,y,value):
		if self.cells[x,y].candidates[value] == True:
			self.cells[x,y].candidates[value] = False
			self.cells[x,y].candidateCount = self.cells[x,y].candidateCount - 1

	def unsetCell(self, x, y):		
		value = self.cells[x,y].value
		self.cells[x,y].value = None
		self.numSetCells = self.numSetCells-1

		for i in range(9):
			self.addCandidate(x,i,value)
			self.addCandidate(i,y,value)
		
		for i in range(3):
			for j in range(3):
				self.addCandidate((x/3)*3+i,(y/3)*3+j,value)

	def addCandidate(self,x,y,value):
		if self.cells[x,y].candidates[value] == False:
			self.cells[x,y].candidates[value] = True
			self.cells[x,y].candidateCount = self.cells[x,y].candidateCount + 1

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

	def _renderLineH(self, y, symbol):
		for x in range(9*self.xscale):
			self.plot(x, y*self.yscale, symbol, 1)

	def _renderLineV(self, x, symbol):
		for y in range(9*self.yscale):
			self.plot(x*self.xscale, y, symbol, 1)
		for y in range(10):
			self.plot(x*self.xscale, y*self.yscale, '+', 1)

	def _renderGrid(self):
		sx = self.xscale
		sy = self.yscale

		for i in range(10):
			if i%3 == 0:
				c = '-'
			else:
				c = ' '
			self._renderLineH(i, c)

		for i in range(10):
			if i%3 == 0:
				c = '|'
			else:
				c = ' '
			self._renderLineV(i, c)
		
		for x in range(9):
			for y in range(9):
				cellValue = self.grid.cells[x,y].value
				if cellValue == None:
					cellValue = ' '
				self.plot(x*sx+sx/2, y*sy+sy/2, str(cellValue), 2)

		cellValue = self.grid.cells[self.cursorX,self.cursorY].value
		if cellValue == None:
			cellValue = ' '

		self.plot(self.cursorX*sx+sx/2, self.cursorY*sy+sy/2, str(cellValue), 3)

	def _renderInfo(self):
		global logging

		x = self.cursorX
		y = self.cursorY
		w = self.infoWindow
		w.addstr(0,0,"Cell [" +str(x) +"," +str(y) +"]")
		w.addstr(0,15,"i=" +str(self.iterations))
		
		w.addstr(2,2, str(self.grid.cells[x,y].candidates))

#		cell = self.grid.cells[x,y]
#		w.addstr(1,1,'1 ' +f2per(cell.p[1]))
#		w.addstr(2,1,'2 ' +f2per(cell.p[2]))
#		w.addstr(3,1,'3 ' +f2per(cell.p[3]))
#		w.addstr(1,10,'4 ' +f2per(cell.p[4]))
#		w.addstr(2,10,'5 ' +f2per(cell.p[5]))
#		w.addstr(3,10,'6 ' +f2per(cell.p[6]))
#		w.addstr(1,19,'7 ' +f2per(cell.p[7]))
#		w.addstr(2,19,'8 ' +f2per(cell.p[8]))
#		w.addstr(3,19,'9 ' +f2per(cell.p[9]))

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
	curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
	curses.noecho()
	curses.cbreak()
	
	screen.keypad(1)
	screen.refresh()

	
	g = Grid()
	
	d = [
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

	gr = GridRenderer(g)
	
	solve(g,gr)

finally:
	curses.nocbreak()
	screen.keypad(0)
	curses.echo()
	curses.endwin()