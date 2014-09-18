#!/usr/bin/python

import sys
import json
import curses
import logging
import itertools

########################################

class CombinationGenerator:
	def __init__(self, maxSize):
		self.maxSize = maxSize
		self.combinationsByTotal = {}
		self._generateCombinations([], 0)
		self._removeDuplicates()

	def _generateCombinations(self, current, total):
		if len(current) < self.maxSize:
			for i in range(1,10):
				if not i in current:
					newCombination = list(current)
					newCombination.append(i)
					newTotal = total + i
					self._addCombination(newCombination, newTotal)
					self._generateCombinations(newCombination, newTotal)

	def _addCombination(self, combination, total):
		combination.sort()
		if (total in self.combinationsByTotal):
			self.combinationsByTotal[total].append(combination)
		else:
			self.combinationsByTotal[total] = [combination]

	def getCombinations(self, total, cells):
		valid = []
		for p in self.combinationsByTotal[total]:
			if len(p) == len(cells):
				valid.append(p)
		return valid

	def _removeDuplicates(self):
		for k in self.combinationsByTotal.keys():
			l  = sorted(self.combinationsByTotal[k])
		for k in self.combinationsByTotal.keys():
			l  = sorted(self.combinationsByTotal[k])
 			uniqueSets = list(l for l, _ in itertools.groupby(l))
			self.combinationsByTotal[k] = uniqueSets

########################################

class Cell:
	def __init__(self, x, y, value):
		self.x = x
		self.y = y
		self.value = value
		self.p = {}
		for i in range(1,10):
			self.p[i] = 1.0

	def __str__(self):
		return "[" +str(self.x) +"," +str(self.y) +"]" +str(self.value)

	def __repr__(self):
		return self.__str__()

########################################

class Restriction:
	def __init__(self, cells):
		self.cells = cells

########################################

class NineGroup(Restriction):
	def __init__(self, cells):
		super(NineGroup, self, cells).__init__()

########################################

class Cage:
	def __init__(self, total, cells):
		self.total = total
		self.cells = cells
		self.combinationList = []

	def updateP(self):
		p = {}
		for i in range(1,10):
			count = 0
			for combo in self.combinationList:
				if i in combo:
					count = count +1
			if count > 0:
				p[i] = float(count)/len(self.combinationList)/len(self.cells)
			else:
				p[i] = 0
		
		for c in self.cells:
			for i in range(1,10):
				c.p[i] = c.p[i] * p[i]

	def __str__(self):
		return "Cage: " +str(self.total) +" " +str(self.cells)
	
	def __repr__(self):
		return self.__str__()

########################################

class Grid:
	def __init__(self, json_spec):
		self.json = json_spec

		self.cells = {}
		for x in range(9):
			for y in range(9):
				self.cells[x,y] = Cell(x, y, None)
		self.numSetCells = 0

		self.cages = []
		self.cageLookupByCell = {}

		maxCageSize = 0
		for c in self.json['cages']:
			if len(c[1]) > maxCageSize:
				maxCageSize = len(c[1])
			cells = []
			for coords in c[1]:
				cells.append(self.cells[coords[0], coords[1]])
			newCage = Cage(c[0], cells)
			self.cages.append(newCage)

			for cageCell in newCage.cells:
				self.cageLookupByCell[cageCell.x,cageCell.y] = newCage

		combinationGenerator = CombinationGenerator(maxCageSize)

		for c in self.cages:
			c.combinationList = combinationGenerator.getCombinations(c.total, c.cells)
			c.updateP()

	def isSolved(self):
		pass
	

########################################

def solve(grid, gr):
	global logging, iterations

	if grid.isSolved():
		gr.render()
		sys.exit()

	#interationLoop(gr)
	if (iterations % 1000) == 0:
		gr.render()
	
	iterations = iterations +1
	gr.iterations = iterations

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

		self.gridWindow = curses.newwin(10*self.yscale, 10*self.xscale, 0, 0)
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

		for x in xrange(0, 9*sx, sx):
			for y in xrange(0, 9*sy, sy):
				for i in range(1, sx):
					self.plot(x+i, y, '-', 1)
					self.plot(x+i, y+sy, '-', 1)
				for i in range(1, sy):
					self.plot(x, y+i, '|', 1)
					self.plot(x+sx, y+i, '|', 1)

		for c in self.grid.cages:
			for cell1 in c.cells:
				for cell2 in c.cells:
					self.removeLineBetween(cell1, cell2)
			self.plot(int(c.cells[0].x)*sx+1, int(c.cells[0].y)*sy, str(c.total), 2)
	
		for x in xrange(0,10*sx,sx):
			for y in xrange(0,10*sy,sy):
				self.plot(x,y,'+', 1)
		
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
		
		cell = self.grid.cells[x,y]
		w.addstr(1,1,'1 ' +f2per(cell.p[1]))
		w.addstr(2,1,'2 ' +f2per(cell.p[2]))
		w.addstr(3,1,'3 ' +f2per(cell.p[3]))
		w.addstr(1,10,'4 ' +f2per(cell.p[4]))
		w.addstr(2,10,'5 ' +f2per(cell.p[5]))
		w.addstr(3,10,'6 ' +f2per(cell.p[6]))
		w.addstr(1,19,'7 ' +f2per(cell.p[7]))
		w.addstr(2,19,'8 ' +f2per(cell.p[8]))
		w.addstr(3,19,'9 ' +f2per(cell.p[9]))

		cage = self.grid.cageLookupByCell[x,y]
		w.addstr(5,1,"Cage target: " +str(cage.total))
		
		w.addstr(6,1,"Cage combinations: ")
		for i in range(len(cage.combinationList)):
			combo = cage.combinationList[i]
			w.addstr(7+i,3, str(combo))

	def removeLineBetween(self,cell1,cell2):
		sx = self.xscale
		sy = self.yscale

		x1 = cell1.x
		y1 = cell1.y
		x2 = cell2.x
		y2 = cell2.y

		if x1 == x2 and y2 == y1+1:
			for i in range(sx):
				self.plot(x1*sx+i, (y1+1)*sy, ' ', 1)

		if y1 == y2 and x2 == x1+1:
			for i in range(sy):
				self.plot((x1+1)*sx, y1*sy+i, ' ', 1)

########################################

def interationLoop(gr):
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
	return "{0:.0f}%".format(float(f) * 100)

########################################

iterations = 0

try:
	logging.basicConfig(filename="output.log", format='%(message)s', level=logging.INFO)

	screen = curses.initscr()
	curses.start_color()
	curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
	curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_YELLOW)
	curses.noecho()
	curses.cbreak()
	
	screen.keypad(1)
	screen.refresh()

	g = Grid(json.load(open(sys.argv[1])))
	gr = GridRenderer(g)
	
	solve(g,gr)
	interationLoop(gr)

finally:
	curses.nocbreak()
	screen.keypad(0)
	curses.echo()
	curses.endwin()