#!/usr/bin/python

import sys
import json
import curses
import logging
import itertools

class CageCandidateSetGenerator:
	def __init__(self, maxSize):
		self.maxSize = maxSize
		self.candidateSetsByTotal = {}
		self.permutedCandidateSetsByTotal = {}
		self._generateCandidateSets([], 0)
		self._removeDuplicates()

	def _generateCandidateSets(self, candidateSet, total):
		if len(candidateSet) < self.maxSize:
			for i in range(1,10):
				if not i in candidateSet:
					newCandidateSet = list(candidateSet)
					newCandidateSet.append(i)
					newTotal = total + i
					self._addCandidateSet(newCandidateSet, newTotal)
					self._generateCandidateSets(newCandidateSet, newTotal)

	def _addCandidateSet(self, candidateSet, total):
		if (total in self.permutedCandidateSetsByTotal):
			self.permutedCandidateSetsByTotal[total].append(candidateSet)
		else:
			self.permutedCandidateSetsByTotal[total] = [candidateSet]

		candidateSet = sorted(candidateSet)
		if (total in self.candidateSetsByTotal):
			self.candidateSetsByTotal[total].append(candidateSet)
		else:
			self.candidateSetsByTotal[total] = [candidateSet]

	def _removeDuplicates(self):
		for k in self.candidateSetsByTotal.keys():
			l  = sorted(self.candidateSetsByTotal[k])
			uniqueSets = list(l for l, _ in itertools.groupby(l))
			self.candidateSetsByTotal[k] = uniqueSets

	def getCandidateSets(self, total, size):
		candidateSets = []
		for cs in self.candidateSetsByTotal[total]:
			if len(cs) == size:
				candidateSets.append(cs)
		return candidateSets

	def getPermutedCandidateSets(self, total, size):
		candidateSets = []
		for cs in self.permutedCandidateSetsByTotal[total]:
			if len(cs) == size:
				candidateSets.append(cs)
		return candidateSets

class Cage:
	def __init__(self, total, cells):
		self.total = total
		self.cells = cells
		self.candidateSets = []
		self.permutedCandidateSets = []

	def remove(self, value):
		self.candidateSets = filter(lambda x: not value in x, self.candidateSets)
		self.permutedCandidateSets = filter(lambda x: not value in x, self.permutedCandidateSets)
		
	def _remove(self, value, cs):
		filter(lambda x: x != value, cs)

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
			newCage = Cage(c[0], c[1])
			self.cages.append(newCage)

			for cageCell in newCage.cells:
				self.cageLookupByCell[cageCell[0],cageCell[1]] = newCage
				self.cageLookupByRow[cageCell[1]].append(newCage)
				self.cageLookupByColumn[cageCell[0]].append(newCage)
				self.cageLookupByGroup[cageCell[0]%3,cageCell[1]%3].append(newCage)
		
		cs = CageCandidateSetGenerator(maxCageSize)

		for c in self.cages:
			c.candidateSets = cs.getCandidateSets(c.total, len(c.cells))
			c.permutedCandidateSets = cs.getPermutedCandidateSets(c.total, len(c.cells))

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

	def step(self):
		global logging
		smallestCage = None
		smallestCageSize = 99999 #lololol
		for cage in self.cages:
			if len(cage.cells) < smallestCageSize:
				smallestCageSize =  len(cage.cells)
				smallestCage = cage

		guess = smallestCage.permutedCandidateSets[0]

		for i in range(len(guess)):
			self.setCell(smallestCage.cells[i][1], smallestCage.cells[i][0], guess[i])

	def setCell(self, x, y, value):
		global logging
		logging.info("Setting [" +str(x) +"," +str(y) +"] to " +str(value))
		self.values[x,y] = value

		self.columnCandidates[x].remove(value)
		self.rowCandidates[y].remove(value)
		self.groupCandidates[x%3,y%3].remove(value)

		for cage in self.cageLookupByColumn[x]:
			cage.remove(value)
		for cage in self.cageLookupByRow[y]:
			cage.remove(value)
		for cage in self.cageLookupByGroup[x%3,y%3]:
			cage.remove(value)


class GridRenderer:
	def __init__(self, grid):
		global screen
		self.grid = grid
		self.xscale = 4
		self.yscale = 2
		self.cursorX = 0
		self.cursorY = 0

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
			self.plot(int(c.cells[0][0])*sx+1, int(c.cells[0][1])*sy, str(c.total), 2)
	
		for x in xrange(0,10*sx,sx):
			for y in xrange(0,10*sy,sy):
				self.plot(x,y,'+', 1)
		
		for x in range(9):
			for y in range(9):
				self.plot(x*sx+sx/2, y*sy+sy/2, str(self.grid.values[x,y]), 3)

		self.plot(self.cursorX*sx+sx/2, self.cursorY*sy+sy/2, str(self.grid.values[self.cursorX, self.cursorY]), 4)

	def _renderInfo(self):
		x = self.cursorX
		y = self.cursorY
		w = self.infoWindow
		w.addstr(0,0,"Cell [" +str(x) +"," +str(y) +"]")

		w.addstr(1,1, "All candidates: " +str(range(1,10)))
		w.addstr(2,1,"Row candidates: " +str(self.grid.rowCandidates[y]))
		w.addstr(3,1,"Col candidates: " +str(self.grid.columnCandidates[x]))
		w.addstr(4,1,"Grp candidates: " +str(self.grid.groupCandidates[x%3, y%3]))
		
		cage = self.grid.cageLookupByCell[x,y]
		w.addstr(5,1,"Cage target: " +str(cage.total))
		w.addstr(6,1,"Cage candidate sets:")

		for i in range(len(cage.candidateSets)):
			w.addstr(7+i,3, str(cage.candidateSets[i]))

	def removeLineBetween(self,cell1,cell2):
		sx = self.xscale
		sy = self.yscale

		x1 = cell1[0]
		y1 = cell1[1]
		x2 = cell2[0]
		y2 = cell2[1]

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
	curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_YELLOW)
	curses.noecho()
	curses.cbreak()
	
	screen.keypad(1)
	screen.refresh()

	g = Grid(json.load(open(sys.argv[1])))
	gr = GridRenderer(g)
	
	while 1:
		gr.render()

		c = screen.getch()
		if c == ord('q'):
			break
		elif c == ord(' '):
			g.step()
		elif c == curses.KEY_LEFT and gr.cursorX>0:
			gr.cursorX = gr.cursorX -1
		elif c == curses.KEY_RIGHT and gr.cursorX<8:
			gr.cursorX = gr.cursorX + 1
		elif c == curses.KEY_UP and gr.cursorY>0:
			gr.cursorY = gr.cursorY - 1
		elif c == curses.KEY_DOWN and gr.cursorY<8:
			gr.cursorY = gr.cursorY + 1

finally:
	curses.nocbreak()
	screen.keypad(0)
	curses.echo()
	curses.endwin()

