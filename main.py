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

#main function to execute the entire trading program
def main():
	#make a cascade instance and generate a random board
	algo = cascade.Cascade()
	algo.randomCollapse()
	boardvalues = algo.boardValues()

	#make a new trader instance with True as the first parameter to indicate paper trading
	trader_person = trader.Trader(True)

	#arrays to store the computed values of the predictions
	trend_predictions = []
	volatility_predictions = []
	trends = []
	volatility = []

	#a value to change the number of increments examined for predictions
	increments = 12

	#add actual data from the present and for the first time offset
	trend, vol, vol_change = trader_person.getAssetData("BTCUSD", "hour", 6)
	trends.append(trend)
	volatility.append(vol_change)

	timestart = datetime.now() - timedelta(hours=6)
	trend, vol, vol_change = trader_person.getAssetData("BTCUSD", "hour", 6, timestart)
	trends.append(trend)
	volatility.append(vol_change)

	#add prediction data from the present and the first time offset increment
	present, offset = trader_person.analyzeAssetData("BTCUSD", True, "hour", 6, "hour", 6)

	trend_predictions.append(present["trend"])
	volatility_predictions.append(present["volatility"])

	trend_predictions.append(offset["trend"])
	volatility_predictions.append(offset["volatility"])

	#loop through 6 hour increments to the past to gather data
	for x in range(12, 6*increments, 6):
		#get the prediction for this asset
		present, offset = trader_person.analyzeAssetData("BTCUSD", False, "hour", 6, "hour", x)

		#get actual data for this asset
		timestart = datetime.now() - timedelta(hours=x)
		trend, vol, vol_change = trader_person.getAssetData("BTCUSD", "hour", 6, timestart)

		#append the necessary data to the prediction lists
		trend_predictions.append(offset["trend"])
		volatility_predictions.append(offset["volatility"])

		#append the actual data to the corresponding lists
		trends.append(trend)
		volatility.append(vol_change)

	#plot the trend and volatility over time
	plt.plot(range(increments), trend_predictions, label="Trend Prediction")
	plt.plot(range(increments), volatility_predictions, label="Volatility Prediction")
	plt.plot(range(increments), trends, label="Actual Trend")
	plt.plot(range(increments), volatility, label="Actual Volatility")

	#label the graph with useful names
	plt.xlabel("Time (starting from the present onto the past)")
	plt.ylabel("Increase/Decrease")
	plt.legend()
	plt.title("Trend and Volatility Patterns:")

	#show the graph
	plt.show()

	#subscribe to a live data stream of crypto bars for day trading
	#trader_person.subscribeCrypto("BTCUSD")

	#sell profitable crypto positions
	#trader_person.sellProfitCrypto()

	#randomly buy crypto (with no selling)
	#trader_person.cascadeCrypto(boardvalues, True)

	#sell all crypto positions
	#trader_person.sellAllCrypto()

	#sell profitable stock positions
	#trader_person.sellProfitStocks()

	#randomly buy and sell stocks
	#trader_person.cascadeStocks(boardvalues, True)

	#sell all stock positions
	#trader_person.sellAllStocks()

#execute the main program
main()
