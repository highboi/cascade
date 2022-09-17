'''
This is a module to contain the data analytics functions of cascade for quantitative investing
'''
from datetime import datetime, timedelta
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np
import math
import pywt
import time
import trader
import json

#a class to analyze market data and predict the future based on mathematical models
class Analyst:
	#an initialization function for the class taking a boolean value for paper trading
	def __init__(self, paper=True):
		self.trader = trader.Trader(paper)

	#this is a function to get the trend and volatility of a set of market data
	def getAssetData(self, asset_symbol, timeunit="hour", timeamount=1, timestart=datetime.now()):
		#get the asset information
		asset = self.trader.alpaca.get_asset(asset_symbol)

		#get market data based on the asset class
		if (asset.__getattr__("class") == "us_equity"):
			bars = self.trader.getStockBars(asset_symbol, timeunit, timeamount, timestart)
		elif(asset.__getattr__("class") == "crypto"):
			bars = self.trader.getCryptoBars(asset_symbol, timeunit, timeamount, timestart)

		#make variables to get the total trend and volatility
		total_trend = 0
		total_volatility = 0

		prev_volatility = 0
		vol_change = 0

		vol_trend = 0

		bars_array = []

		#analyze the market data
		for bar in bars:
			bars_array.append(bar)

			#calculate trend
			trend = bar.c - bar.o

			#calculate trend in percentage
			percent_trend = (trend*100) / bar.vw

			#add this trend to the total trend calculation
			total_trend = total_trend + percent_trend

			#calculate the percentage volatility up and down
			percent_up = bar.h - bar.vw
			percent_up = (percent_up*100) / bar.vw
			percent_down = bar.vw - bar.l
			percent_down = (percent_down*100) / bar.vw

			vol_trend_current = (bar.h - bar.vw) - (bar.vw - bar.l)
			vol_trend = vol_trend + vol_trend_current

			#get the total volatility
			percent_volatility = percent_up + percent_down

			#calculate the volatility change based on the volatility of the previous bar
			if (percent_volatility > prev_volatility):
				vol_change = vol_change + 1
			elif (percent_volatility < prev_volatility):
				vol_change = vol_change - 1

			#add this volatility to the total volatility calculation
			total_volatility = total_volatility + percent_volatility

			#store this bars volatility for analysis in the next loop iteration
			prev_volatility = percent_volatility

		#return the total percent trend and total volatility
		return bars_array, total_trend, total_volatility, vol_change, vol_trend

	#this is a function to analyze two assets for correlations
	def correlateAssets(self, benchmark, comparator, timeunit="hour", timeamount=1, timestart=datetime.now()):
		#get the trend and volatility for the benchmark market data
		benchmark_bars, benchmark_trend, benchmark_volatility, benchmark_vol_change, benchmark_vol_trend = self.getAssetData(benchmark, timeunit, timeamount, timestart)

		#get the trend and volatility for the comparator market data
		comparator_bars, comparator_trend, comparator_volatility, comparator_vol_change, comp_vol_trend = self.getAssetData(comparator, timeunit, timeamount, timestart)

		#calculate the relationship between the trends of the two assets
		if ((benchmark_trend > 0 and comparator_trend > 0) or (benchmark_trend < 0 and comparator_trend < 0) or (benchmark_trend == 0 and comparator_trend == 0)):
			trend_relationship = "linear"
		else:
			trend_relationship = "inverse"

		#calculate the relationship between the volatility of the two assets
		if ((benchmark_vol_change > 0 and comparator_vol_change > 0) or (benchmark_vol_change < 0 and comparator_vol_change < 0) or (benchmark_vol_change == 0 and comparator_vol_change == 0)):
			volatility_relationship = "linear"
		else:
			volatility_relationship = "inverse"

		#return the trend and volatility relationship between the two assets
		return trend_relationship, volatility_relationship

	#this is a function that returns the data and relationships for an asset over a specific time frame
	def getAssetPairData(self, asset_symbol, comparator, timeunit="hour", timeamount=1, timestart=datetime.now()):
		#get the relationship between the asset and the comparator
		trend_rel, vol_rel = self.correlateAssets(asset_symbol, comparator, timeunit, timeamount, timestart)

		#get the data for the same time frame the relationships were measured
		bars, trend, vol, vol_change, vol_trend = self.getAssetData(asset_symbol, timeunit, timeamount, timestart)

		#wrap this data into a dictionary
		input_data = {
			"bars": bars,
			"trend": trend,
			"vol": vol,
			"vol_change": vol_change,
			"vol_trend": vol_trend,
			"trend_rel": trend_rel,
			"vol_rel": vol_rel
		}

		return input_data

	#analyze data to make a prediction
	def predictAssetPair(self, asset_symbol, comparator, timeunit="hour", timeamount=8, timestart=datetime.now()):
		#get stock data for this pair of asset data
		asset_pair_data = self.getAssetPairData(asset_symbol, comparator, timeunit, timeamount, timestart)

		x_values = []
		y_values = []

		high_median = 0
		low_median = 0
		medians = []

		#loop through market data to plot the data as a wave
		for increment in range(len(asset_pair_data["bars"])):
			#calculate the x values for this set of data
			start_x = 50*increment
			end_x = start_x+50
			fourth_x = start_x + ( (end_x-start_x)/4 )
			mid_x = start_x + ( (end_x-start_x)/2 )
			three_fourth_x = start_x + ( ((end_x-start_x)/4)*3 )

			#get the current bar of asset data
			bar = asset_pair_data["bars"][increment]

			#get the x and y values to depict this bar of data
			x_values = x_values + [start_x, fourth_x, mid_x, three_fourth_x, end_x]
			y_values = y_values + [bar.o, bar.h, bar.vw, bar.l, bar.c]

			#calculate the median value for the high and low of this bar of data
			median = (bar.h - bar.l) / 2
			median = bar.l + median

			medians.append(median)

			#calculate and update the highest median and lowest median value for this set of bars
			if (median > high_median):
				high_median = median
			elif (median < low_median or low_median == 0):
				low_median = median

		#calculate the different median segments
		segment_increment = (high_median - low_median) / len(asset_pair_data["bars"])
		segment_increments = []
		for segment in range(len(asset_pair_data["bars"])+1):
			segment_increments.append(low_median + (segment_increment*segment))

		bar_sections = {}

		for segment in segment_increments:
			bar_sections[str(segment)] = []

		#categorize bars of data into different segments
		for bar in asset_pair_data["bars"]:
			close_value = 0

			print("***")
			for segment in segment_increments:
				median = bar.h - bar.l / 2
				median = bar.l + median

				print(close_value)

				if (close_value == 0):
					close_value = segment

				if (abs(median - segment) < abs(median - close_value)):
					close_value = segment

			print(close_value)
			print()

		#plot the values of market data
		plt.plot(x_values, y_values)

		#plot lines to separate each increment of data
		for val in range(math.floor(len(x_values)/5)):
			plt.axvline(x_values[val*5])

		#plot lines to depict the median value (high - low) of each bar of market data
		for median in medians:
			plt.axhline(median)

		#get the approximation and detail coefficients of the market data
		(A, D) = pywt.dwt(y_values, "db1")

		#plot the graph
		plt.show()

	'''
	THE FUNCTIONS BELOW ARE FOR DATA ANALYTICS AND BACKTESTING OF MODELS
	'''

	#this is a function to gather and store historical market data
	def gatherData(self, asset_symbol, timeunit="hour", timeamount=1, increments=6, timestart=datetime.now()):
		#get the correct time offset
		if (timeunit == "minute"):
			timeoffset = timedelta(minutes=timeamount)
		elif (timeunit == "hour"):
			timeoffset = timedelta(hours=timeamount)
		elif (timeunit == "day"):
			timeoffset = timedelta(days=timeamount)
		elif (timeunit == "week"):
			timeoffset = timedelta(weeks=timeamount)
		elif (timeunit == "month"):
			timeoffset = timedelta(months=timeamount)
		elif (timeunit == "year"):
			timeoffset = timedelta(years=timeamount)

		#make a dictionary to store the datasets
		datasets = {"timestart": timestart.timestamp(), "data": []}

		#go over the time increments to extract data
		for x in range(0, increments):
			#get the starting point from which to extract data
			starting_point = timestart - (timeoffset*x)

			#get data for this time increment
			bars, trend, vol, vol_change, vol_trend = self.getAssetData(asset_symbol, timeunit, timeamount, starting_point)

			#a dictionary to store data attributes
			data_dict = {
				"number": x,
				"bars": bars,
				"asset": asset_symbol,
				"trend": trend,
				"vol": vol,
				"vol_change": vol_change,
				"vol_trend": vol_trend,
				"starting_point": starting_point.timestamp(),
				"timeunit": timeunit,
				"timeamount": timeamount
			}

			#append this dataset to the dictionary
			datasets["data"].append(data_dict)

		#turn the data dictionary into a json object
		json_datasets = json.dumps(datasets)

		#write the data object into a json file
		with open("data.json", "r+") as json_file:
			#load the json file data
			json_data = json.load(json_file)

			#add the new market data to the current file data
			json_data["data"].append(json_datasets)

			#set the position of the file seeker to the beginning (0)
			json_file.seek(0)

			#dump the new data into the json file
			json.dump(json_data, json_file, indent=4)

			#close the file
			json_file.close()

	#this is a function to read market data from a json file
	def retrieveData(self, asset_symbol):
		#retrieve historical data from the json file
		json_file = open("data.json", "r+")

		#get the json data from the file
		json_data = json.load(json_file)

		#an array to store sets of market data
		market_data = []

		#loop through the data to find correct data
		for bars in json_data["data"]:
			#get the market data
			bar_data = json.loads(bars)["data"]

			#check to see if this data matches the ticker being analyzed
			if bar_data[0]["asset"] == asset_symbol:
				market_data.append(bar_data)

		#return the market data for analysis
		return market_data
