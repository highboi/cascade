#this program creates a sudoku board as an array and performs a wave function collapse to generate random numbers

from pprint import pprint
from datetime import date
import random

'''
creation of the array of possibilities
'''
mainarray = []

for x in range(9):
	temparray = []
	for y in range(9):
		temparray.append([1, 2, 3, 4, 5, 6, 7, 8, 9])
	mainarray.append(temparray)

'''
randomly deciding the first cell to collapse based on subgrid and cell number
'''
randomsubgrid = random.randint(0, 8)
randomcell = random.randint(0, 8)
randomstate = random.randint(1, 9)
mainarray[randomsubgrid][randomcell] = [randomstate]


'''
collapse the possibilities of cells in the subgrid
'''
for i in range(9):
	if (not i == randomcell):
		mainarray[randomsubgrid][i].remove(randomstate)

'''
collapse the possibilities of cells in the row
'''
#a function to get the correct range of indexes based on a subgrid or cell number (works only for rows and subgrids, not columns)
def getrowrange(number):
	if (number in range(0, 3)):
		rowrange = range(0, 3)
	elif (number in range(3, 6)):
		rowrange = range(3, 6)
	elif (number in range(6, 9)):
		rowrange = range(6, 9)

	return rowrange

#get the correct ranges for the subgrid and cell indexes to collapse the possibilities of
subgridrange = getrowrange(randomsubgrid)
cellrange = getrowrange(randomcell)

#collapse the possibilities of cells in the same row as the initial collapsed cell
for s in subgridrange:
	for c in cellrange:
		if (randomstate in mainarray[s][c] and len(mainarray[s][c]) > 1):
			mainarray[s][c].remove(randomstate)

'''
collapse the possibilities of the cells in the column
'''
#a function to get the correct index numbers based on a subgrid or cell number (works only for columns, not rows or subgrids)
def getcolumnrange(number):
	if (number in [0, 3, 6]):
		return [0, 3, 6]
	elif (number in [1, 4, 7]):
		return [1, 4, 7]
	elif (number in [2, 5, 8]):
		return [2, 5, 8]

#get the correct ranges for the subgrid and cell indexes to collapse the possibilities of
subgridcolumn = getcolumnrange(randomsubgrid)
cellcolumn = getcolumnrange(randomcell)

#collapse the possibilities of cells in the same column as the initial collapsed cell
for s in subgridcolumn:
	for c in cellcolumn:
		if (randomstate in mainarray[s][c] and len(mainarray[s][c]) > 1):
			mainarray[s][c].remove(randomstate)
