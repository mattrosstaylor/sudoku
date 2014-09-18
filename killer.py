#!/usr/bin/python

import sys
import json
import curses
import logging

class PermutationGenerator:
	def __init__(self, maxSize):
		self.maxSize = maxSize
		self.permutationsByTotal = {}
		self._generatePermutations([], 0)

	def _generatePermutations(self, current, total):
		if len(current) < self.maxSize:
			for i in range(1,10):
				if not i in current:
					newPermutation = list(current)
					newPermutation.append(i)
					newTotal = total + i
					self._addPermutation(newPermutation, newTotal)
					self._generatePermutations(newPermutation, newTotal)

	def _addPermutation(self, permutation, total):
		if (total in self.permutationsByTotal):
			self.permutationsByTotal[total].append(permutation)
		else:
			self.permutationsByTotal[total] = [permutation]

	def getCandidateLists(self, total, cells):
		candidateLists = []
		for p in self.permutationsByTotal[total]:
			if len(p) == len(cells):
				candidateLists.append(CandidateList(cells, p))
		return candidateLists

class Cell:
	def __init__(self, x, y, value):
		self.x = x
		self.y = y
		self.value = value

	def __str__(self):
		return "[" +str(self.x) +"," +str(self.y) +"]" +str(self.value)

	def __repr__(self):
		return self.__str__()

	def __eq__(self, other):
		return self.x == other.y and self.y == other.y
	def __ne__(self, other):
		return not self.__eq__(other)

class CandidateList:
	def __init__(self, cells, values):
		self.cells = []
		for i in range(len(cells)):
			self.cells.append(Cell(cells[i].x, cells[i].y, values[i]))
		self.size = len(self.cells)

	def __str__(self):
		output = ""
		for c in self.cells:
			output = output +str(c) +' '	
		return output

	def __repr__(self):
		return self.__str__()

class Cage:
	def __init__(self, total, cells):
		self.total = total
		self.cells = cells
		self.filled = False
		self.candidateLists = []

	def __str__(self):
		return "Cage: " +str(self.total) +" " +str(self.cells)
	
	def __repr__(self):
		return self.__str__()

class Grid:
	def __init__(self, json_spec):
		self.json = json_spec

		self.cageLookupByCell = {}

		self.cageLookupByRow = {}
		self.cageLookupByColumn = {}
		self.cageLookupByGroup = {} 

		#initial lookups
		for i in range(9):
			self.cageLookupByRow[i] = []
			self.cageLookupByColumn[i] = []
		for x in range(3):
			for y in range(3):
				self.cageLookupByGroup[x,y] = []

		maxCageSize = 0
		self.cages = []
		for c in self.json['cages']:
			if len(c[1]) > maxCageSize:
				maxCageSize = len(c[1])
			cells = []
			for coords in c[1]:
				cells.append(Cell(coords[0], coords[1], None))
			newCage = Cage(c[0], cells)
			self.cages.append(newCage)

			for cageCell in newCage.cells:
				self.cageLookupByCell[cageCell.x,cageCell.y] = newCage
				self.cageLookupByRow[cageCell.y].append(newCage)
				self.cageLookupByColumn[cageCell.x].append(newCage)
				self.cageLookupByGroup[cageCell.x/3,cageCell.y/3].append(newCage)
		
		permutationGenerator = PermutationGenerator(maxCageSize)

		for c in self.cages:
			c.candidateLists = permutationGenerator.getCandidateLists(c.total, c.cells)

		self.rowCandidates = {}
		for i in range(9):
			self.rowCandidates[i] = range(1,10)
		self.columnCandidates = {}
		for i in range(9):
			self.columnCandidates[i] = range(1,10)
		
		self.groupCandidates = {}
		for x in range(3):
			for y in range(3):
				self.groupCandidates[x,y] = range(1,10)

		self.values = {}
		for x in range(9):
			for y in range(9):
				self.values[x,y] = ' ' 
		self.numSetCells = 0

	def getActiveCandidateLists(self, cage):
		activeCandidateLists = []
		for cl in cage.candidateLists:
			active = True
			for c in cl.cells:
				if self.canSet(c):
					active = False
					break
			if active:
				activeCandidateLists.append(cl)

		return activeCandidateLists

	def canSet(self, c):
		global logging
		output = True

		if self.values[c.x,c.y] != ' ' and self.values[c.x,c.y] != c.value:
			output = False
		elif not c.value in self.columnCandidates[c.x]:
			output = False
		elif not c.value in self.rowCandidates[c.y]:
			output = False
		elif not c.value in self.groupCandidates[c.x/3,c.y/3]:
			output = False
		#logging.info("canSet " +str(c) +" " +str(output))
		return output

	def setCell(self, c):
		global logging
 		#logging.info("setting " +str(c))
		self.values[c.x,c.y] = c.value
		self.numSetCells = self.numSetCells+1
		self.columnCandidates[c.x].remove(c.value)
		self.rowCandidates[c.y].remove(c.value)
		self.groupCandidates[c.x/3,c.y/3].remove(c.value)

	def unsetCell(self, c):
		global logging
		#logging.info("unsetting " +str(c))
		self.values[c.x,c.y] = ' '
		self.numSetCells = self.numSetCells-1
		if not c.value in self.columnCandidates[c.x]:
			self.columnCandidates[c.x].append(c.value)
		if not c.value in self.rowCandidates[c.y]:
			self.rowCandidates[c.y].append(c.value)
		if not c.value in self.groupCandidates[c.x/3,c.y/3]:	
			self.groupCandidates[c.x/3,c.y/3].append(c.value)

	def isSolved(self):
		if self.numSetCells == 9*9:
			return True

class GridRenderer:
	def __init__(self, grid):
		global screen
		self.grid = grid
		self.xscale = 4
		self.yscale = 2
		self.cursorX = 0
		self.cursorY = 0
		self.selectedCombination = None
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
				self.plot(x*sx+sx/2, y*sy+sy/2, str(self.grid.values[x,y]), 3)

		self.plot(self.cursorX*sx+sx/2, self.cursorY*sy+sy/2, str(self.grid.values[self.cursorX, self.cursorY]), 4)

	def _renderInfo(self):
		global logging

		x = self.cursorX
		y = self.cursorY
		w = self.infoWindow
		w.addstr(0,0,"Cell [" +str(x) +"," +str(y) +"]")

		w.addstr(1,1,"Row candidates: " +str(self.grid.rowCandidates[y]))
		w.addstr(2,1,"Col candidates: " +str(self.grid.columnCandidates[x]))
		w.addstr(3,1,"Grp candidates: " +str(self.grid.groupCandidates[x/3, y/3]))
		
		cage = self.grid.cageLookupByCell[x,y]
		w.addstr(4,1,"Cage target: " +str(cage.total))
		activeCl = self.grid.getActiveCandidateLists(cage)
		
		w.addstr(5,1,"Cage candidate combinations: " +str(len(activeCl)))

		if (not self.selectedCombination == None):
			sx = self.xscale
			sy = self.yscale
			w.addstr(6,5, "Showing " +str(self.selectedCombination))
			try:
				cl = activeCl[self.selectedCombination]
				for c in cl.cells:
					self.plot(c.x*sx+sx/2,c.y*sy+sy/2, str(c.value), 2)
				
			except IndexError:
				w.addstr(6,4,"!")

		w.addstr(8,1,"Iterations: " +str(self.iterations))

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

def interationLoop(gr):
	global screen

	while 1:
		gr.render()

		c = screen.getch()
		if c == ord('q'):
			sys.exit()
		elif c == ord('n'):
			break
		elif c == ord('c'):
			if gr.selectedCombination == None:
				gr.selectedCombination = 0
			else:
				gr.selectedCombination = None
		elif c == ord('-') and not gr.selectedCombination == None:
			gr.selectedCombination = gr.selectedCombination - 1
		elif c == ord('=') and not gr.selectedCombination == None:
			gr.selectedCombination = gr.selectedCombination + 1
		
		elif c == curses.KEY_LEFT and gr.cursorX>0:
			gr.cursorX = gr.cursorX -1
		elif c == curses.KEY_RIGHT and gr.cursorX<8:
			gr.cursorX = gr.cursorX + 1
		elif c == curses.KEY_UP and gr.cursorY>0:
			gr.cursorY = gr.cursorY - 1
		elif c == curses.KEY_DOWN and gr.cursorY<8:
			gr.cursorY = gr.cursorY + 1

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

	_simpleSolve(grid, gr)
	_guessCage(grid,gr)

def _simpleSolve(grid, gr):
	global logging

	for x in range(9):
		if len(grid.columnCandidates[x]) == 1:
			#logging.info('x')
			for y in range(9):
				c = Cell(x,y, grid.columnCandidates[x][0])
				if grid.canSet(c):
					grid.setCell(c)
					solve(grid, gr)
					grid.unsetCell(c)

	for y in range(9):
		if len(grid.rowCandidates[y]) == 1:
			#logging.info('y')
			for x in range(9):
				c = Cell(x,y, grid.rowCandidates[y][0])
				if grid.canSet(c):
					grid.setCell(c)
					solve(grid, gr)
					grid.unsetCell(c)

	for x in range(3):
		for y in range(3):
			if len(grid.groupCandidates[x,y]) == 1:
				#logging.info('g')
				for xx in range(3):
					for yy in range(3):
						c = Cell(x*3+xx,y*3+yy, grid.groupCandidates[x,y][0])
						if grid.canSet(c):
							grid.setCell(c)
							solve(grid, gr)
							grid.unsetCell(c)						


def _guessCage(grid, gr):
	global logging

	smallestCage = None
	smallestCageSize = 99999 #lololol

	for cage in grid.cages:
		if cage.filled == False and len(cage.candidateLists) < smallestCageSize:
				smallestCageSize = len(cage.candidateLists)
				smallestCage = cage

	if smallestCage == None:
		#logging.info("Backtracking")
		return

	for cl in smallestCage.candidateLists:
		canSet = True
		for c in cl.cells:
			if not grid.canSet(c):
				canSet = False
				break

		if canSet:
			for c in cl.cells:
				grid.setCell(c)

			smallestCage.filled = True

			solve(grid, gr)

			for c in cl.cells:
				grid.unsetCell(c)
			smallestCage.filled = False


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

