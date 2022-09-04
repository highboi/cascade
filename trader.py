from dotenv import load_dotenv
from alpaca_trade_api.common import URL
from alpaca_trade_api.stream import Stream
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from datetime import date, datetime, timedelta
from pprint import pprint
import random
import time
import math
import os
import alpaca_trade_api as alpaca_api
import pandas as pd
import inspect

#an organized class for stocks/crypto trading
class Trader:
	#initialization of the trader class
	def __init__(self, paper):
		#load the environment variables from the .env file
		load_dotenv()

		#set up the alpaca REST clients (real and paper clients respectively)
		client, paper_client = self.setupAlpaca()

		#check to see if this instance is for paper trading or real trading
		if (paper):
			self.alpaca = paper_client
		else:
			self.alpaca = client

		#initiate an instance of stream for getting live market data
		self.stream = Stream(
				self.alpaca._key_id,
				self.alpaca._secret_key,
				base_url=self.alpaca._base_url,
				data_feed="iex")

		#print out the current portfolio info
		self.getPortfolio()

	#a function that sets up the alpaca REST client
	def setupAlpaca(self):
		#get information to use the alpaca api using the os module
		api_secret = os.environ["API_SECRET"]
		api_key = os.environ["API_KEY"]
		base_url = os.environ["BASE_URL"]

		paper_api_secret = os.environ["PAPER_API_SECRET"]
		paper_api_key = os.environ["PAPER_API_KEY"]
		paper_url = os.environ["PAPER_URL"]

		#initialize the REST client for the alpaca api
		alpaca = alpaca_api.REST(api_key, api_secret, base_url)

		#initialize the paper trading REST client
		alpaca_paper = alpaca_api.REST(paper_api_key, paper_api_secret, paper_url)

		return alpaca, alpaca_paper

	#a function to get the portfolio value of the account
	def getPortfolio(self):
		#get the current alpaca account
		account = self.alpaca.get_account()

		#print important account info
		print("*"*10)
		print("Account Info:")
		print("Portfolio Value:", account.portfolio_value)
		print("Equity:", account.equity)
		print("Long Market Value (Value of Stocks):", account.long_market_value)
		print("Cash:", account.cash)
		print("*"*10)
		print()

		#return the account
		return account

	#this is a function to get the trend and volatility of a set of market data
	def getAssetData(self, asset_symbol, timeunit="hour", timeamount=6, timestart=datetime.now()):
		#get the asset information
		asset = self.alpaca.get_asset(asset_symbol)

		#get market data based on the asset class
		if (asset.__getattr__("class") == "us_equity"):
			bars = self.getStockBars(asset_symbol, timeunit, timeamount, timestart)
		elif(asset.__getattr__("class") == "crypto"):
			bars = self.getCryptoBars(asset_symbol, timeunit, timeamount, timestart)

		#make variables to get the total trend and volatility
		total_trend = 0
		total_volatility = 0

		prev_volatility = 0
		volatility_change = 0

		#analyze the market data
		for bar in bars:
			#calculate trend
			trend = bar.c - bar.o

			#calculate trend in percentage
			percent_trend = trend / (bar.vw/100)

			#add this trend to the total trend calculation
			total_trend = total_trend + percent_trend

			#calculate the percentage volatility up and down
			percent_up = bar.h - bar.vw
			percent_up = percent_up / (bar.vw/100)
			percent_down = bar.vw - bar.l
			percent_down = percent_down / (bar.vw/100)

			#get the total volatility
			percent_volatility = percent_up + percent_down

			#calculate the volatility change based on the volatility of the previous bar
			if (percent_volatility > prev_volatility):
				volatility_change = volatility_change + 1
			elif (percent_volatility < prev_volatility):
				volatility_change = volatility_change - 1

			#add this volatility to the total volatility calculation
			total_volatility = total_volatility + percent_volatility

			#store this bars volatility for analysis in the next loop iteration
			prev_volatility = percent_volatility

		#return the total percent trend and total volatility
		return total_trend, total_volatility, volatility_change

	#this is a function to analyze two assets for correlations
	def correlateAssets(self, benchmark, comparator, timeunit="hour", timeamount=6, timestart=datetime.now()):
		#get the trend and volatility for the benchmark market data
		benchmark_trend, benchmark_volatility, benchmark_vol_change = self.getAssetData(benchmark, timeunit, timeamount, timestart)

		#get the trend and volatility for the comparator market data
		comparator_trend, comparator_volatility, comparator_vol_change = self.getAssetData(comparator, timeunit, timeamount, timestart)

		#calculate the relationship between the trends of the two assets
		if ((benchmark_trend > 0 and comparator_trend > 0) or (benchmark_trend < 0 and comparator_trend < 0)):
			trend_relationship = "linear"
		else:
			trend_relationship = "inverse"

		#calculate the relationship between the volatility of the two assets
		if ((benchmark_vol_change > 0 and comparator_vol_change > 0) or (benchmark_vol_change < 0 and comparator_vol_change < 0)):
			volatility_relationship = "linear"
		else:
			volatility_relationship = "inverse"

		#return the trend and volatility relationship between the two assets
		return trend_relationship, volatility_relationship

	#this is a function that predicts changes in relationships between assets
	def predictAssetRel(self, asset_symbol, comparator, timeunit="hour", timeamount=6, timeincrements=6, timestart=datetime.now()):
		print("Predicting future asset relationship...")

		#make variables for the linearity of the trend and volatility relationship with these two assets
		trend_linearity = 0
		volatility_linearity = 0

		#get the relationship between assets over multiple time increments to predict future relationships
		for x in range(1, timeincrements):
			#get the right time offset based on the time increment of this iteration of the loop
			if (timeunit == "minute"):
				time_offset = timedelta(minutes=timeamount*x)
			elif (timeunit == "hour"):
				time_offset = timedelta(hours=timeamount*x)
			elif (timeunit == "day"):
				time_offset = timedelta(days=timeamount*x)
			elif (timeunit == "week"):
				time_offset = timedelta(weeks=timeamount*x)
			elif (timeunit == "month"):
				time_offset = timedelta(months=timeamount*x)
			elif (timeunit == "year"):
				time_offset = timedelta(years=timeamount*x)

			#get the starting point for this increment of time
			timepoint = timestart - time_offset

			#get the trend relationship for this time period and offset
			trend_relationship, volatility_relationship = self.correlateAssets(asset_symbol, comparator, timeunit, timeamount, timepoint)

			#add to the trend linearity value
			if (trend_relationship == "linear"):
				trend_linearity = trend_linearity + 1
			else:
				trend_linearity = trend_linearity - 1

			#add to the volatility linearity value
			if (volatility_relationship == "linear"):
				volatility_linearity = volatility_linearity + 1
			else:
				volatility_linearity = volatility_linearity - 1

		#calculate the relationship prediction for trend
		if (trend_linearity > 0):
			trend_rel_pred = "linear"
		elif (trend_linearity < 0):
			trend_rel_pred = "inverse"
		else:
			trend_rel_pred = "nochange"

		#calculate the relationship prediction for volatility
		if (volatility_linearity > 0):
			vol_rel_pred = "linear"
		elif (volatility_linearity < 0):
			vol_rel_pred = "inverse"
		else:
			vol_rel_pred = "nochange"

		#return the total prediction of the trend and volatility relationships
		return trend_rel_pred, vol_rel_pred

	#this is a function that predicts an asset based on another asset
	def predictAsset(self, asset_symbol, comparator, timeunit="hour", timeamount=6, timestart=datetime.now()):
		#make sure we are not correlating the asset with itself
		if (asset_symbol == comparator):
			pass

		#compare the assets from the past
		trend_relationship, volatility_relationship = self.correlateAssets(asset_symbol, comparator, timeunit, timeamount, timestart)

		#get the trend and volatility data for this asset
		trend, volatility, vol_change = self.getAssetData(comparator, timeunit, timeamount, timestart)

		#predict the future trend of the main asset based on the data from this asset and the relationship between them
		if (trend_relationship == "linear"):
			if (trend > 0):
				trend_prediction = "up"
			elif (trend < 0):
				trend_prediction = "down"
			else:
				trend_prediction = "none"
		elif (trend_relationship == "inverse"):
			if (trend > 0):
				trend_prediction = "down"
			elif (trend < 0):
				trend_prediction = "up"
			else:
				trend_prediction = "none"

		#predict the future volatility of the main asset based on the data from this asset and the relationship between them
		if (volatility_relationship == "linear"):
			if (vol_change > 0):
				vol_prediction = "up"
			elif (vol_change < 0):
				vol_prediction = "down"
			else:
				vol_prediction = "none"
		elif (volatility_relationship == "inverse"):
			if (vol_change > 0):
				vol_prediction = "down"
			elif (vol_change < 0):
				vol_prediction = "up"
			else:
				vol_prediction = "none"

		#return the trend and volatility prediction of the asset pair
		return trend_prediction, vol_prediction, trend_relationship, volatility_relationship

	#this is a function to produce predictions for an asset and weigh the predictions based on their accuracy
	def crystalBall(self, asset_symbol, timeunit="hour", timeamount=6, timestart=datetime.now(), timeoffset=timedelta(hours=6)):
		#get the asset class
		asset = self.alpaca.get_asset(asset_symbol)
		asset_class = asset.__getattr__("class")

		#get the comparators
		if (asset_class == "crypto"):
			comparators = self.cryptoCoins()
		elif (asset_class == "us_equity"):
			comparators = self.snp500()[:24]

		#an object to add prediction data
		weighted_predictions = {"asset": asset_symbol}

		#loop through each comparator ticker
		for comp in comparators:
			trend_pred_accuracy = 0
			vol_pred_accuracy = 0

			#get the trend predictions, volatility predictions, and relationships
			trend_prediction, vol_prediction, trend_relationship, vol_relationship = self.predictAsset(asset_symbol, comp, timeunit, timeamount, timestart-timeoffset)

			#get the actual data for this time frame
			trend, volatility, vol_change = self.getAssetData(asset_symbol, timeunit, timeamount, timestart)

			#compare the predictions with actual data to measure accuracy of predictions
			if ((trend > 0 and trend_prediction == "up") or (trend < 0 and trend_prediction == "down")):
				trend_pred_accuracy = trend_pred_accuracy + 1
			elif (trend == 0 and trend_prediction == "none"):
				trend_pred_accuracy = trend_pred_accuracy + 1

			if ((vol_change > 0 and vol_prediction == "up") or (vol_change < 0 and vol_prediction == "down")):
				vol_pred_accuracy = vol_pred_accuracy + 1
			elif (vol_change == 0 and vol_prediction == "none"):
				vol_pred_accuracy = vol_pred_accuracy + 1

			#add prediction data to object containing the predictions and their weighted accuracy
			trend_pred_key = comp + "_trend"
			vol_pred_key = comp + "_vol"
			trend_weight_key = comp + "_trend_weight"
			vol_weight_key = comp + "_vol_weight"

			weighted_predictions[trend_pred_key] = trend_prediction
			weighted_predictions[vol_pred_key] = vol_prediction
			weighted_predictions[trend_weight_key] = trend_pred_accuracy
			weighted_predictions[vol_weight_key] = vol_pred_accuracy

		return weighted_predictions, comparators

	#this is a function that measures multiple weighted predictions in order to create accurate final predictions about trend and volatility
	def oracle(self, asset_symbol, timeunit="hour", timeamount=6, increments=12):
		#GET THE CORRECT TIME START VALUE BASED ON THE TIME PERIOD SPECIFIED
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

		#a dictionary to store prediction sets for all time periods
		prediction_sets = {}

		#LOOP THROUGH THE TIME INCREMENTS TO GET MULTIPLE WEIGHTED PREDICTION SETS
		for x in range(1, increments):
			#GET THE TIMESTART FOR THIS LOOP ITERATION
			timestart = datetime.now() - (timeoffset*x)

			#GET THE PREDICTION DATA
			weighted_predictions, comparators = self.crystalBall(asset_symbol, timeunit, timeamount, timestart, timeoffset)

			#ADD THE PREDICTION DATA TO AN OBJECT FOR LATER ANALYSIS
			time_period_key = "pred_set_" + str(x)

			#insert the comparators and iteration number for this prediction set
			weighted_predictions["comparators"] = comparators
			weighted_predictions["number"] = x

			#add the weighted predictions to the prediction sets
			prediction_sets[time_period_key] = weighted_predictions

		#make a dictionary to contain the weighted predictions of each correlated asset
		asset_predictions = {"comparators": []}

		#LOOP THROUGH THE PREDICTIONS TO SET A WEIGHTED VALUE FOR EACH PREDICTION POSSIBILITY
		for key, preds in prediction_sets.items():
			#loop through the comparators for this set to get their prediction values
			for comp in preds["comparators"]:
				#get the prediction values
				trend_value = preds[comp + "_trend"]
				vol_value = preds[comp + "_vol"]
				trend_accuracy = preds[comp + "_trend_weight"]
				vol_accuracy = preds[comp + "_vol_weight"]

				#add accuracy and prediction count values to the dictionary if not already added
				if (comp+"_trend_accuracy" not in asset_predictions):
					asset_predictions[comp+"_trend_accuracy"] = 0

				if (comp+"_vol_accuracy" not in asset_predictions):
					asset_predictions[comp+"_vol_accuracy"] = 0

				if (comp+"_pred_count" not in asset_predictions):
					asset_predictions[comp+"_pred_count"] = 0

				#add the accuracy and prediction count to the dictionary
				asset_predictions[comp+"_trend_accuracy"] = asset_predictions[comp+"_trend_accuracy"] + trend_accuracy
				asset_predictions[comp+"_vol_accuracy"] = asset_predictions[comp+"_vol_accuracy"] + vol_accuracy
				asset_predictions[comp+"_pred_count"] = asset_predictions[comp+"_pred_count"] + 1

				if (preds["number"] == 1):
					asset_predictions[comp+"_trend_pred"] = trend_value
					asset_predictions[comp+"_vol_pred"] = vol_value

			asset_predictions["comparators"] = asset_predictions["comparators"] + preds["comparators"]

		#make the comparators a unique set
		asset_predictions["comparators"] = set(asset_predictions["comparators"])

		#make a dictionary for finalized prediction values
		final_predictions = {"asset": asset_symbol, "trend_up": 0, "trend_down": 0, "trend_same": 0, "vol_up": 0, "vol_down": 0, "vol_same": 0}

		#loop through all involved comparators to get their predictions and accuracies
		for asset in asset_predictions["comparators"]:
			trend = asset_predictions[asset+"_trend_pred"]
			vol = asset_predictions[asset+"_vol_pred"]
			trend_corr_strength = asset_predictions[asset+"_trend_accuracy"] / asset_predictions[asset+"_pred_count"]
			vol_corr_strength = asset_predictions[asset+"_vol_accuracy"] / asset_predictions[asset+"_pred_count"]


			if (trend == "up"):
				final_predictions["trend_up"] = final_predictions["trend_up"] + trend_corr_strength
			elif (trend == "down"):
				final_predictions["trend_down"] = final_predictions["trend_down"] + trend_corr_strength
			else:
				final_predictions["trend_same"] = final_predictions["trend_same"] + trend_corr_strength

			if (vol == "up"):
				final_predictions["vol_up"] = final_predictions["vol_up"] + vol_corr_strength
			elif (vol == "down"):
				final_predictions["vol_down"] = final_predictions["vol_down"] + vol_corr_strength
			else:
				final_predictions["vol_same"] = final_predictions["vol_same"] + vol_corr_strength

		return final_predictions

	#a function that makes decisions based on the final weighted predictions of the oracle() function
	def lohiOracle(self, asset_type, timeunit="hour", timeamount=6, increments=12):
		#get assets to compare to
		if (asset_type == "crypto"):
			tickers = self.cryptoCoins()
		elif (asset_type == "us_equity"):
			tickers = self.snp500()[:24]

		#loop through all of the tickers to buy/sell
		for ticker in tickers:
			self.oracle(ticker, timeunit, timeamount, increments)

			print("Sleeping for 10 seconds...")
			print()
			time.sleep(10)
		'''
	ALL FUNCTIONS BELOW THIS ARE FOR BUYING/SELLING AND RETRIEVING RAW DATA ONLY, NO DATA PROCESSING
	'''

	#the callback function for the live stock data
	async def stockCallback(self, data):
		#get a list of the current stock positions
		positions = self.alpaca.list_positions()
		stock_positions = []
		for pos in positions:
			stock_positions.append(pos.symbol)

		#check to see if this symbol/ticker is available to sell/buy
		if (data.symbol in stock_positions):
			#get the current position for this symbol/ticker
			position = self.alpaca.get_position(data.symbol)
			print(position)

			#get the unrealized profit/loss of this position
			profit = float(position.unrealized_pl)

			print("Profit/loss:", profit)

			#sell the stock or hold depending on the state of the profit/loss
			if (profit >= self.stock_cap):
				print("Liquidating position for a $", profit, " increase.")
				self.sellStock(data.symbol)
			elif (profit <= -self.stock_bottom):
				print("Liquidating position to keep losses at $", profit, ".")
				self.sellStock(data.symbol)
			else:
				print("Holding position for", data.symbol + "...")
		else:
			print("No position for", data.symbol)

	#a function that gets live market data for a stock
	def subscribeStock(self, symbol, cap=1, bottom=5):
		#set values for the cap and bottom values for selling a stock
		self.stock_cap = cap
		self.stock_bottom = bottom

		#subscribe to the live stream of stock bar data
		self.stream.subscribe_bars(self.stockCallback, symbol)

		#run the stream to receive live data
		self.stream.run()

	#returns a list of the stocks on the S&P 500 in random order
	def snp500(self):
		#get a list of the stocks on the current S&P 500 from wikipedia
		table = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")

		#get the raw values of the stock symbols from the wikipedia data
		df = table[0]
		symbols = df.loc[:,"Symbol"].values

		#loop through the symbols to create a normal array
		stocks = []
		for sym in symbols:
			stocks.append(sym)

		#shuffle the values of the stock to make random selections
		random.shuffle(stocks)
		return stocks

	#gets the latest bar of a stock based on the symbol
	def getStockBar(self, symbol):
		stockprice = self.alpaca.get_latest_bar(symbol)

		return stockprice

	#a function to get a set of bars for a stock for analysis
	def getStockBars(self, symbol, unit="hour", timeamount=1, timestart=datetime.now()):
		#get the current time in the form of a UTC timestamp and make start and end variables
		start = timestart
		start = start.timestamp()
		end = start

		#get the value of different units of time in seconds
		minute = 60
		hour = minute*60
		day = hour*24
		week = day*7
		month = week*4
		year = month*12

		#get the starting timestamp based on the time unit and amount of time to go back. also get the right time increment
		if (unit == "minute"):
			start = start - (minute*timeamount)

			timeframe = TimeFrame.Minute
		elif (unit == "hour"):
			start = start - (hour*timeamount)

			timeframe = TimeFrame.Hour
		elif (unit == "day"):
			start = start - (day*timeamount)

			timeframe = TimeFrame.Day
		elif (unit == "week"):
			start = start - (week*timeamount)

			timeframe = TimeFrame.Week
		elif (unit == "month"):
			start = start - (month*timeamount)

			timeframe = TimeFrame.Month
		elif (unit == "year"):
			start = start - (year*timeamount)

			timeframe = TimeFrame.Year

		#make the starting timestamp into an iso timestamp
		start = start - (15*minute)
		start = str(datetime.fromtimestamp(start).isoformat())+"Z"

		#make the ending timestamp 15 minutes ago (free subscription does not allow more recent data) and convert to iso timestamp
		end = end - (15*minute)
		end = str(datetime.fromtimestamp(end).isoformat())+"Z"

		#get bars for stocks
		bars = self.alpaca.get_bars_iter(symbol, timeframe, start, end, adjustment="raw")

		#return the iterable bars
		return bars

	#places an order for a stock
	def buyStock(self, symbol, money):
		#get the price of the stock
		stockprice = self.getStockBar(symbol).close

		print("Quantity to Buy:", float(money)/float(stockprice))

		#check to see if this stock is fractionable
		fractionable = self.alpaca.get_asset(symbol)
		fractionable = fractionable.fractionable

		#place an order or return False depending on if the stock is fractional
		if (fractionable and float(money) >= 1.00):
			#place an order for fractional shares
			return self.alpaca.submit_order(
				symbol=symbol,
				notional=money,
				side="buy",
				type="market",
				time_in_force="day"
			)
		else:
			#the stock is not fractionable so it cannot be bought
			return False

	#places an order to sell all stock in current position
	def sellStock(self, symbol):
		#get the current positions of this account
		positions = self.alpaca.list_positions()

		#get a full array of the positions and their symbols
		stock_positions = []
		for i in positions:
			stock_positions.append(i.symbol)

		#check to see if this is a position that can be sold
		if (symbol in stock_positions):
			#get the amount of shares for this position
			current_position = self.alpaca.get_position(symbol)
			quantity = current_position.qty

			print("Selling", quantity, "stock shares")

			#return an order for selling a stock
			return self.alpaca.submit_order(
				symbol=symbol,
				qty=quantity,
				side="sell",
				type="market",
				time_in_force="day"
			)
		else:
			#return false if this stock is not a currently held position
			return False

	#a function that randomly buys and sells stocks based on the sudoku board values
	def cascadeStocks(self, numbers, hold=False, stocks=0):
		#if there is no list of stocks given, get random S&P 500 stocks
		if (not stocks):
			stocks = self.snp500()

			#get the first 10 random stocks to trade
			stocks = stocks[:10]

		#get the current positions of this account and make a list of the symbols of these positions
		positions = self.alpaca.list_positions()
		stock_positions = []
		for pos in positions:
			stock_positions.append(pos.symbol)

		#get the amount of cash available for the alpaca account
		cash = float(self.alpaca.get_account().cash)

		#get the amount of cash available for each buy/sell decision
		cash_alloted = float(cash)/len(stocks)

		#loop through the board values to make random decisions
		for value in numbers:
			#get the current stock to buy/sell
			stock = stocks[0]
			print(stock + ":")

			#if the number is less than 4, buy the crypto
			if (value < 5):
				print("Buying shares with alloted cash...")
				order = self.buyStock(stock, cash_alloted)
			elif (value > 5 and stock in stock_positions): #if the number is more than 4, sell the crypto
				#check to see if the function is supposed to sell positions
				if (not hold):
					print("Selling all shares in current position...")
					order = self.sellStock(stock)

					#if the selling does not work, buy more of this stock
					if (not order):
						print("Too little shares to sell, buying more shares...")
						order = self.buyStock(stock, cash_alloted)
				else: #the algorithm is supposed to hold/buy positions only
					print("Holding current position...")
					order = False
			else: #if the number is 4, then buy crypto with half of the alloted cash
				print("Buying shares with 1/2 of alloted cash...")
				order = self.buyStock(stock, cash_alloted/2)

			#check to see if the order was carried out
			if (order):
				#print the order
				print(order.side)
				if (order.side == "buy"):
					print("$" + str(order.notional))
				elif (order.side == "sell"):
					print(str(order.qty))
			else:
				print("Order not carried out or HODLing current position.")

			#print newline for organization
			print()

			#remove this stock from the list to move onto the next stock
			stocks.remove(stock)

			#break the loop if there are no more stocks to buy/sell
			if (not len(stocks)):
				break

	#a function that sells stock positions based on unrealized profit/loss
	def sellProfitStocks(self):
		#get the current crypto positions
		positions = self.alpaca.list_positions()

		#loop through current stock positions
		for pos in positions:
			if (pos.asset_class == "us_equity"):
				#get the profit/loss as a float
				profit = float(pos.unrealized_pl)

				print(pos.symbol + ":")
				print("Profit/Loss:", profit)

				#if there is a profit, sell the position
				if (profit > 0):
					#sell the stock
					order = self.sellStock(pos.symbol)

					#print order information
					if (order):
						print(order.side)
						print(order.qty)
					else:
						print("Not sold, too little to sell.")

				print()

	#a function that sells all stock positions
	def sellAllStocks(self):
		#get the current positions of this account and make a list of the symbols of these positions
		positions = self.alpaca.list_positions()
		stock_positions = []
		for pos in positions:
			#make sure this is a stock position
			if (pos.asset_class == "us_equity"):
				stock_positions.append(pos.symbol)

		#loop through the currently held positions and sell
		for symbol in stock_positions:
			print("Selling", symbol + "...")

			#sell the stock
			order = self.sellStock(symbol)

			#print out order information
			if (order):
				print(order.side)
				print(order.qty)
			else:
				print("Not sold, too little to sell.")

			print()

	#a function for short selling a list of stocks (such as biotech stocks)
	def shortStocks(self, stocks):
		#get the amount of cash available on the account
		cash = float(self.alpaca.get_account().cash)

		#divide the cash evenly into each of the stocks
		cash_alloted = cash / len(stocks)

		#loop through the stocks and place short orders for these stocks
		for stock in stocks:
			#create a short order for this stock using the alloted amount of cash
			order = self.alpaca.submit_order(
				symbol=stock,
				notional=cash_alloted,
				side="sell",
				type="market",
				time_in_force="day"
			)

			#print out order information
			if (order):
				print("Shorted", stock)
			else:
				print("Could not carry out short order.")

			print()

	#the callback function for live crypto data
	async def cryptoCallback(self, data):
		#get all currently held crypto position tickers/symbols
		positions = self.alpaca.list_positions()
		crypto_positions = []
		for pos in positions:
			crypto_positions.append(pos.symbol)

		#act based on if this ticker is a held position
		if (data.symbol in crypto_positions):
			#get the current position for this symbol/ticker
			position = self.alpaca.get_position(data.symbol)
			print(position)

			#get the unrealized profit/loss for this symbol/ticker
			profit = float(position.unrealized_pl)

			print("Profit/loss:", profit)

			#sell or hold depending on the crypto cap or bottom
			if (profit >= self.crypto_cap):
				print("Liquidating position for a $", profit, " increase.")
				self.sellCrypto(data.symbol)
			elif (profit <= -self.crypto_bottom):
				print("Liquidating position to keep losses at $", profit, ".")
				self.sellCrypto(data.symbol)
			else:
				print("Holding position for", data.symbol + "...")
		else:
			print("No position for:", data.symbol)

	#a function that gets live market data for a cryptocurrency
	def subscribeCrypto(self, symbol, cap=1, bottom=5):
		#set the cap and bottom for selling this cryptocurrency
		self.crypto_cap = cap
		self.crypto_bottom = bottom

		#subscribe to the data stream of crypto bars
		self.stream.subscribe_crypto_bars(self.cryptoCallback, symbol)

		#run the stream to start receiving live data
		self.stream.run()

	#returns a list of the crypto available on alpaca in random order
	def cryptoCoins(self):
		#array of the accepted coin symbols on alpaca
		coins = [
			"AAVEUSD",
			"ALGOUSD",
			"AVAXUSD",
			"BATUSD",
			"BTCUSD",
			"BCHUSD",
			"LINKUSD",
			"DAIUSD",
			"DOGEUSD",
			"ETHUSD",
			"GRTUSD",
			"LTCUSD",
			"MKRUSD",
			"MATICUSD",
			"NEARUSD",
			"PAXGUSD",
			"SHIBUSD",
			"SOLUSD",
			"SUSHIUSD",
			"USDTUSD",
			"TRXUSD",
			"UNIUSD",
			"WBTCUSD",
			"YFIUSD"
		]

		#shuffle the coin values for random selections
		random.shuffle(coins)
		random.shuffle(coins)

		return coins

	#gets the latest bar of a cryptocurrency based on the symbol and exchange (default exchange is FTX)
	def getCryptoBar(self, symbol, exchange="FTXU"):
		#select the latest crypto bar from specified exchange, the exchanges can be coinbase (CBSE), FTX (FTXU), or ErisX (ERSX)
		cryptoprice = self.alpaca.get_latest_crypto_bar(symbol, exchange)

		return cryptoprice

	#a function to get a set of bars for a crypto for analysis
	def getCryptoBars(self, symbol, unit="hour", timeamount=1, timestart=datetime.now()):
		#get the current time in the form of a UTC timestamp and make start and end variables
		start = timestart
		start = start.timestamp()
		end = start

		#get the value of different units of time in seconds
		minute = 60
		hour = minute*60
		day = hour*24
		week = day*7
		month = week*4
		year = month*12

		#get the starting timestamp based on the time unit and amount of time to go back. also get the right time increment
		if (unit == "minute"):
			start = start - (minute*timeamount)

			timeframe = TimeFrame.Minute
		elif (unit == "hour"):
			start = start - (hour*timeamount)

			timeframe = TimeFrame.Hour
		elif (unit == "day"):
			start = start - (day*timeamount)

			timeframe = TimeFrame.Day
		elif (unit == "week"):
			start = start - (week*timeamount)

			timeframe = TimeFrame.Week
		elif (unit == "month"):
			start = start - (month*timeamount)

			timeframe = TimeFrame.Month
		elif (unit == "year"):
			start = start - (year*timeamount)

			timeframe = TimeFrame.Year

		#make the starting timestamp into an iso timestamp
		start = start - (15*minute)
		start = str(datetime.fromtimestamp(start).isoformat())+"Z"

		#make the ending timestamp 15 minutes ago (free subscription does not allow more recent data) and convert to iso timestamp
		end = end - (15*minute)
		end = str(datetime.fromtimestamp(end).isoformat())+"Z"

		#get bars for stocks with a time frame unit of one hour
		bars = self.alpaca.get_crypto_bars_iter(symbol, TimeFrame.Hour, start, end)

		#return the iterable bars
		return bars

	#places an order for a cryptocurrency
	def buyCrypto(self, symbol, money):
		#get the price of one full coin
		cryptoprice = self.getCryptoBar(symbol).close

		#get information about this crypto asset
		crypto_asset = self.alpaca.get_asset(symbol)
		min_order = crypto_asset.min_order_size
		min_trade_increment = crypto_asset.min_trade_increment

		#calculate the crypto price of the minimum trade increment
		increment_price = float(cryptoprice) * float(min_trade_increment)

		print("Price:", cryptoprice)
		print("Money:", money)
		print("Increment_price:", increment_price)
		print("Quantity Information:")
		print("Minimum Order Amount:", min_order)
		print("Minimum Trade Increment:", min_trade_increment)

		#set the amount of increments this money can buy
		quantity = float(money) // float(increment_price)

		#set the quantity according to the minimum trade increment (ensures 100% liquidity)
		quantity = float(quantity) * float(min_trade_increment)

		print("Quantity to Buy:", quantity)

		#if the quantity is larger than the minimum order number, order crypto
		if (float(money)/float(cryptoprice) >= float(min_order)):
			#return an order for crypto, the time in force is "gtc" for "Good Till Cancelled"
			return self.alpaca.submit_order(
				symbol=symbol,
				qty=quantity,
				side="buy",
				type="market",
				time_in_force="gtc"
			)
		else:
			#return false if this order is too small to be carried out
			return False

	#places an order to sell all cryptocurrency in a position
	def sellCrypto(self, symbol):
		#get the positions of this account
		positions = self.alpaca.list_positions()

		#make a list of the current positions
		crypto_positions = []
		for i in positions:
			crypto_positions.append(i.symbol)

		#check to see if the current symbol is held
		if (symbol in crypto_positions):
			#get the amount of crypto for this position
			current_position = self.alpaca.get_position(symbol)
			quantity = current_position.qty

			#get the minimum order size and trade increment for this order to work
			crypto_asset = self.alpaca.get_asset(symbol)
			min_order = crypto_asset.min_order_size
			min_trade_increment =  crypto_asset.min_trade_increment

			#create a quantity that is based on the minimum trade increment in order for the selling to work
			increment_amount = float(quantity) // float(min_trade_increment)
			quantity = int(increment_amount) * float(min_trade_increment)

			print("Quantity to Sell:", quantity)

			#the quantity to order must be more than the minimum order amount for it to process
			if (float(quantity) >= float(min_order)):
				#return an order for selling a cryptocurrency
				return self.alpaca.submit_order(
					symbol=symbol,
					qty=quantity,
					side="sell",
					type="market",
					time_in_force="gtc"
				)
			else:
				#return false if the quantity is not processable
				return False
		else:
			#return false if this is not a currently held position
			return False

	#a function that randomly buys and sells crypto based on the sudoku board values
	def cascadeCrypto(self, numbers, hold=False):
		#get a random list of crypto coins
		coins = self.cryptoCoins()

		#get the current positions of this account and make a list of the symbols of these positions
		positions = self.alpaca.list_positions()
		crypto_positions = []
		for pos in positions:
			crypto_positions.append(pos.symbol)

		#get the amount of cash available for the alpaca account
		cash = float(self.alpaca.get_account().cash)

		#get the amount of cash available for each buy/sell decision
		cash_alloted = float(cash)/len(coins)

		#loop through the board values to make random decisions
		for value in numbers:
			#get the current coin to buy/sell
			coin = coins[0]
			print(coin + ":")

			#if the number is less than 4, buy the crypto
			if (value < 5):
				print("Buying shares with alloted cash...")
				order = self.buyCrypto(coin, cash_alloted)
			elif (value > 5 and coin in crypto_positions): #if the number is more than 4, sell the crypto
				#check to see if the algorithm is supposed to sell positions
				if (not hold):
					print("Selling all shares in current position...")
					order = self.sellCrypto(coin)

					#if the selling does not work, buy more of this crypto
					if (not order):
						print("Too little shares to sell, buying more shares...")
						order = self.buyCrypto(coin, cash_alloted)
				else: #the algorithm is supposed to hold/buy positions only
					print("Holding current position...")
					order = False
			else: #if the number is 4, then buy crypto with half of the alloted cash
				print("Buying shares with 1/2 of alloted cash...")
				order = self.buyCrypto(coin, cash_alloted/2)

			#check to see if the order was carried out
			if (order):
				#print the order
				print(order.side)
				if (order.side == "buy"):
					print("$" + str(order.notional))
				elif (order.side == "sell"):
					print(str(order.qty))
			else:
				print("Order not carried out or HODLing current position.")

			#print newline for organization
			print()

			#remove this coin from the list to move onto the next coin
			coins.remove(coin)

			#break the loop if there are no more cryptos to buy/sell
			if (not len(coins)):
				break

	#a function that sells crypto positions based on unrealized profit/loss
	def sellProfitCrypto(self):
		#get the current crypto positions
		positions = self.alpaca.list_positions()

		#loop through current crypto positions
		for pos in positions:
			if (pos.asset_class != "us_equity"):
				#get the profit/loss as a float
				profit = float(pos.unrealized_pl)

				print(pos.symbol + ":")
				print("Profit/Loss:", profit)

				#if there is a profit, sell the position
				if (profit > 0):
					#sell the crypto
					order = self.sellCrypto(pos.symbol)

					#print order information
					if (order):
						print(order.side)
						print(order.qty)
					else:
						print("Not sold, too little to sell.")

				print()

	#a function that sells all crypto positions
	def sellAllCrypto(self):
		#get the current positions of this account and make a list of the symbols of these positions
		positions = self.alpaca.list_positions()
		crypto_positions = []
		for pos in positions:
			#check to make sure this is not a stock position
			if (pos.asset_class != "us_equity"):
				crypto_positions.append(pos.symbol)

		#loop through the currently held positions and sell
		for symbol in crypto_positions:
			print("Selling", symbol + "...")

			#sell the crypto
			order = self.sellCrypto(symbol)

			#print out order information
			if (order):
				print(order.side)
				print(order.qty)
			else:
				print("Not sold, too little to sell.")

			print()
