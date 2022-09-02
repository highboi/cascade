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
	increments = 24

	#add actual data from the present and for the first time offset
	trend, vol, vol_change = trader_person.getAssetData("DOGEUSD", "hour", 1)
	trends.append(trend)
	volatility.append(vol_change)

	timestart = datetime.now() - timedelta(hours=1)
	trend, vol, vol_change = trader_person.getAssetData("DOGEUSD", "hour", 1, timestart)
	trends.append(trend)
	volatility.append(vol_change)

	#add prediction data from the present and the first time offset increment
	present, offset = trader_person.analyzeAssetData("DOGEUSD", True, "hour", 1, "hour", 1)

	trend_predictions.append(present["trend"])
	volatility_predictions.append(present["volatility"])

	trend_predictions.append(offset["trend"])
	volatility_predictions.append(offset["volatility"])

	#loop through 1 hour increments to the past to gather data
	for x in range(2, 1*increments, 1):
		#get the prediction for this asset
		present, offset = trader_person.analyzeAssetData("DOGEUSD", False, "hour", 1, "hour", x)

		#get actual data for this asset
		timestart = datetime.now() - timedelta(hours=x)
		trend, vol, vol_change = trader_person.getAssetData("DOGEUSD", "hour", 1, timestart)

		#append the necessary data to the prediction lists
		trend_predictions.append(offset["trend"])
		volatility_predictions.append(offset["volatility"])

		#append the actual data to the corresponding lists
		trends.append(trend)
		volatility.append(vol_change)

	#make variables to store the trend and volatility accuracy
	trend_accuracy = 0
	vol_accuracy = 0

	print()
	print("Trend Data (prediction and result):")

	#loop through all trend predictions
	for x in range(len(trend_predictions)-1):
		#get the prediction and the resulting value of the next interval of time
		values = [trend_predictions[x], trends[x+1]]
		print(values[0], "|", values[1])

		#get the difference in the value of the results
		results = []
		for i in values:
			if (i > 0):
				results.append("up")
			elif (i < 0):
				results.append("down")
			else:
				results.append("nochange")

		#see if the prediction and result are matching or not
		if (results[0] == results[1]):
			print("Correct Prediction")
			trend_accuracy = trend_accuracy + 1
		else:
			print("Incorrect Prediction")
	print()

	print()
	print("Volatility Data (prediction and result):")
	for x in range(len(volatility_predictions)-1):
		#get the prediction and the resulting value of the next interval of time
		values = [volatility_predictions[x], volatility[x+1]]
		print(values[0], "|", values[1])

		#get the difference in value of the results
		results = []
		for i in values:
			if (i > 0):
				results.append("up")
			elif (i < 0):
				results.append("down")
			else:
				results.append("nochange")

		#see if the prediction and result are matching or not
		if (results[0] == results[1]):
			print("Correct Prediction")
			vol_accuracy = vol_accuracy + 1
		else:
			print("Incorrect Prediction")
	print()

	#print out the trend and volatility accuracy as a number from 0 to 1 (to measure percentage)
	print("Trend Accuracy:")
	print( (trend_accuracy / (len(trend_predictions)-1)) * 100, "%")
	print("Volatility Accuracy:")
	print( (vol_accuracy / (len(volatility_predictions)-1)) * 100, "%")

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
	#trader_person.subscribeCrypto("DOGEUSD")

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
