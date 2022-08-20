'''
this program creates a sudoku board as an array and performs a wave function collapse to generate random numbers
the random numbers are then used to make buying/selling decisions on crypto positions
'''

#import custom modules for the wave function collapse and the crypto trading functions
import cascade
import trader

#main function to execute the entire trading program
def main():
	#make a cascade instance and generate a random board
	algo = cascade.Cascade()
	algo.randomCollapse()
	boardvalues = algo.boardValues()

	#make a new trader instance with True as the first parameter to indicate paper trading
	trader_person = trader.Trader(True)

	#sell profitable crypto positions
	#trader_person.sellProfitCrypto()

	#randomly buy and sell crypto
	#trader_person.cascadeCrypto(boardvalues)

	#sell all crypto positions
	#trader_person.sellAllCrypto()

	#sell profitable stock positions
	#trader_person.sellProfitStocks()

	#randomly buy and sell stocks
	trader_person.cascadeStocks(boardvalues)

	#sell all stock positions
	#trader_person.sellAllStocks()

#execute the main program
main()
