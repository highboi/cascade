'''
this program creates a sudoku board as an array and performs a wave function collapse to generate random numbers
the random numbers are then used to make buying/selling decisions on crypto positions
'''

#import custom modules for the wave function collapse and the crypto trading functions
#import cascade
import analyst
import trader
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pprint import pprint

#main function to execute the entire trading program
def main():
	#make a cascade instance and generate a random board
	'''
	algo = cascade.Cascade()
	algo.randomCollapse()
	boardvalues = algo.boardValues()
	'''

	#make a new trader instance with True as the first parameter to indicate paper trading
	analyzer = analyst.Analyst(True)

	ticker = "DOGEUSD"

	analyzer.predictAssetPair(ticker, "BTCUSD")

#execute the main program
main()
