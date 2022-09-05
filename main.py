'''
this program creates a sudoku board as an array and performs a wave function collapse to generate random numbers
the random numbers are then used to make buying/selling decisions on crypto positions
'''

#import custom modules for the wave function collapse and the crypto trading functions
import cascade
import trader
import time
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pprint import pprint

#main function to execute the entire trading program
def main():
	#make a cascade instance and generate a random board
	algo = cascade.Cascade()
	algo.randomCollapse()
	boardvalues = algo.boardValues()

	#make a new trader instance with True as the first parameter to indicate paper trading
	trader_person = trader.Trader(True)

	ticker = "SHIBUSD"

	predictions = trader_person.oracle(ticker, "hour", 1, 6)

	trend, vol, vol_change = trader_person.getAssetData(ticker, "hour", 1)

	print()
	print("Predictions for", ticker + ":")
	pprint(predictions)
	print("Actual Trend:", trend)
	print("Actual Volatility Change:", vol_change)
	print()

#execute the main program
main()
