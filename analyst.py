'''
This is a module to contain the data analytics functions of cascade for quantitative investing
'''
from datetime import datetime, timedelta
from pprint import pprint
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

		#analyze the market data
		for bar in bars:
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
		return total_trend, total_volatility, vol_change, vol_trend

	#this is a function to analyze two assets for correlations
	def correlateAssets(self, benchmark, comparator, timeunit="hour", timeamount=1, timestart=datetime.now()):
		#get the trend and volatility for the benchmark market data
		benchmark_trend, benchmark_volatility, benchmark_vol_change, benchmark_vol_trend = self.getAssetData(benchmark, timeunit, timeamount, timestart)

		#get the trend and volatility for the comparator market data
		comparator_trend, comparator_volatility, comparator_vol_change, comp_vol_trend = self.getAssetData(comparator, timeunit, timeamount, timestart)

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
	def getAssetPredData(self, asset_symbol, comparator, timeunit="hour", timeamount=1, timestart=datetime.now()):
		#get the relationship between the asset and the comparator
		trend_rel, vol_rel = self.correlateAssets(asset_symbol, comparator, timeunit, timeamount, timestart)

		#get the data for the same time frame the relationships were measured
		trend, vol, vol_change, vol_trend = self.getAssetData(asset_symbol, timeunit, timeamount, timestart)

		#wrap this data into a dictionary
		input_data = {
			"trend": trend,
			"vol": vol,
			"vol_change": vol_change,
			"vol_trend": vol_trend,
			"trend_rel": trend_rel,
			"vol_rel": vol_rel
		}

		return input_data

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
			trend, vol, vol_change, vol_trend = self.getAssetData(asset_symbol, timeunit, timeamount, starting_point)

			#a dictionary to store data attributes
			data_dict = {
				"number": x,
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

	#this is a function to compare historical data with predictions
	def backtest(self, asset_symbol):
		#get historical data for this ticker
		market_data = self.retrieveData(asset_symbol)

		#loop through all of the market data sets
		for data in market_data:
			#loop through this market data set
			for index in range(len(data)-1):
				#get two increments of data to compare
				bar = data[index]
				bar2 = data[index+1])
