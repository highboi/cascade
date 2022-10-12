'''
This is a module to contain the data analytics functions of cascade for quantitative investing
'''
from datetime import datetime, timedelta
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np
import math
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

	#this is a function to return a range of values to plot a wave function
	def getWave(self, wave):
		#get different attributes of the wave
		bar_count = len(wave["order"])
		bar_period = wave["bar_period"]

		#calculate the starting and ending points of each wave
		start = wave["order"][0]*bar_period
		end = wave["order"][-1]*bar_period

		#calculate the lifetime of the wave by getting the difference of the start and end and dividing by 50 to get the hours of activity
		if (end == start):
			wave["lifetime"] = ((end+bar_period) - start) / 50
		else:
			wave["lifetime"] = (end - start) / 50

		#calculate the probability of the wave showing up in the wave's lifetime
		wave["probability"] = (bar_count / wave["lifetime"])

		#calculate the length and cycles of this function
		length = bar_period + end
		final_x_range = np.arange(start, length, length/800)

		#get the x and y value ranges for this function
		wave_x = final_x_range
		wave_y = ( wave["amplitude"] * np.sin(wave_x) ) + wave["intercept"]

		#return the x and y ranges
		return wave_x, wave_y, wave

	#analyze data to make a prediction
	def predictAssetPair(self, asset_symbol, comparator, timeunit="hour", timeamount=8, timestart=datetime.now()):
		#get stock data for this pair of asset data
		asset_pair_data = self.getAssetPairData(asset_symbol, comparator, timeunit, timeamount, timestart)

		x_values = []
		y_values = []

		high_median = 0
		low_median = 0

		#get the amount of x values to represent each bar over
		bar_period = 50

		#loop through market data to plot the data as a wave
		for increment in range(len(asset_pair_data["bars"])):
			#calculate the x values for this set of data
			start_x = bar_period*increment
			end_x = start_x+bar_period
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

			#calculate and update the highest median and lowest median value for this set of bars
			if (median > high_median):
				high_median = median
			elif (median < low_median or low_median == 0):
				low_median = median

		#calculate the different median segments to categorize bars into
		segment_increment = (high_median - low_median) / len(asset_pair_data["bars"])
		segment_increments = []
		for segment in range(len(asset_pair_data["bars"])+1):
			segment_increments.append(low_median + (segment_increment*segment))

		#make an object to contain arrays of bars belonging to their respective segments (the dictionary keys)
		bar_sections = {}
		for segment in segment_increments:
			bar_sections[str(segment)] = []

		#categorize bars of data into different segments
		for bar in asset_pair_data["bars"]:
			#a variable to store the segment the bar is closest too
			close_value = 0

			#calculate the median value of this bar of data
			median = (bar.h - bar.l) / 2
			median = bar.l + median

			#loop through the segments to see which range this bar of data falls into
			for segment in segment_increments:
				#if the close_value is the default, then define it as the current segment
				if (close_value == 0):
					close_value = segment

				#get two difference calculations to compare to each other to find the segment closest to the value of the median
				past_diff = abs(median - close_value)
				current_diff = abs(median - segment)

				#if this segment is closer to this bars median than the previous one, then make the close value the current segment
				if (current_diff < past_diff):
					close_value = segment

			#add the median of this bar of data to the object for later access
			bar.median = median
			bar.order = asset_pair_data["bars"].index(bar)

			#add the bar to the segment it is closest too
			bar_sections[str(close_value)].append(bar)

		#an array to store the average values of the groups of bars (high, low, and median values)
		avg_values = []

		#an array to store the information about each wave and where they show themselves
		waves = []

		#get the average high, low, and median of each group of bar data
		for segment in segment_increments:
			#make empty variables for the sum of all highs, lows, and medians
			high_sum = 0
			low_sum = 0
			median_sum = 0
			vw_sum = 0

			#an array to store the locations of the bars in time
			bar_places = []

			#get the amount of bars to calculate the average of each attribute
			bar_amount = len(bar_sections[str(segment)])

			#skip this iteration of the loop if there are no bars to calculate
			if (bar_amount == 0):
				continue

			#loop through each bar and add the high, low, and median values to the total sum
			for bar in bar_sections[str(segment)]:
				high_sum = high_sum + bar.h
				low_sum = low_sum + bar.l
				median_sum = median_sum + bar.median
				vw_sum = vw_sum + bar.vw

				bar_places.append(bar.order)

			#calculate the average high, low, and median values for all bars in this category
			high_avg = high_sum / bar_amount
			low_avg = low_sum / bar_amount
			median_avg = median_sum / bar_amount
			vw_avg = vw_sum / bar_amount

			#calculate the amplitude of this set of bars in this segment
			amplitude = high_avg - median_avg
			y_intercept = median_avg

			#make a dictionary that represents a wave
			wave = {
				"amplitude": amplitude,
				"intercept": y_intercept,
				"order": bar_places,
				"bar_period": bar_period
			}

			#add this wave to the collection of waves
			waves.append(wave)

			#add the values of this set of bars to be graphed
			for i in range(bar_amount):
				avg_values = avg_values + [median_avg, high_avg, median_avg, low_avg, median_avg]

		print("AMOUNT OF WAVES:", len(waves))

		#graph each wave
		for wave in waves:
			wave_x, wave_y, new_wave = self.getWave(wave)

			plt.plot(wave_x, wave_y)

			print(new_wave)

		#plot the values of market data
		plt.plot(x_values, y_values)

		#plt.plot(x_values, avg_values)

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
