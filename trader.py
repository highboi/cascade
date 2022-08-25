from dotenv import load_dotenv
from alpaca_trade_api.common import URL
from alpaca_trade_api.stream import Stream
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from datetime import date, datetime
import random
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

		#predict BTCUSD trend and volatility based on other assets
		predictions = self.predictAsset("BTCUSD", ["ETHUSD", "SHIBUSD", "DOGEUSD"])
		print(predictions)

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
	def getAssetData(self, bars):
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
	def correlateAssets(self, benchmark, comparator, timeunit="hour", timeamount=5):
		#get the asset class for the benchmark and comparator
		benchmark_asset = self.alpaca.get_asset(benchmark)
		benchmark_type = benchmark_asset.__getattr__("class")

		comparator_asset = self.alpaca.get_asset(comparator)
		comparator_type = comparator_asset.__getattr__("class")

		#get the proper bar data for each asset
		if (benchmark_type == "crypto"):
			benchmark_bars = self.getCryptoBars(benchmark, timeunit, timeamount)
		elif (benchmark_type == "us_equity"):
			benchmark_bars = self.getStockBars(benchmark, timeunit, timeamount)

		if (comparator_type == "crypto"):
			comparator_bars = self.getCryptoBars(comparator, timeunit, timeamount)
		elif (comparator_type == "us_equity"):
			comparator_bars = self.getStockBars(comparator, timeunit, timeamount)


		#get the trend and volatility for the benchmark market data
		benchmark_trend, benchmark_volatility, benchmark_vol_change = self.getAssetData(benchmark_bars)

		#get the trend and volatility for the comparator market data
		comparator_trend, comparator_volatility, comparator_vol_change = self.getAssetData(comparator_bars)

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

		'''
		print(benchmark, "(Benchmark) Info:")
		print("Trend:", str(benchmark_trend)+"%")
		print("Volatility:", str(benchmark_volatility)+"%")
		print()

		print(comparator, "(Comparator) Info:")
		print("Trend:", str(comparator_trend)+"%")
		print("Volatility:", str(comparator_volatility)+"%")
		print()

		print("Trend and Volatility Relationships:")
		print("Trend Relationship:", trend_relationship)
		print("Volatility Relationship:", volatility_relationship)
		print()
		'''

		#return the trend and volatility relationship between the two assets
		return trend_relationship, volatility_relationship

	#this is a function that buys/sells an asset based on correlations with other assets
	def predictAsset(self, asset_symbol, comparators, timeunit="hour", timeamount=6):
		#a dictionary to store asset relationships, with the asset being predicted inside it
		asset_rels = {"predicted_asset": asset_symbol}

		#get the relationships between the assets
		for comp in comparators:
			#make sure we are not correlating the asset with itself
			if (asset_symbol == comp):
				pass

			#compare the assets from the past
			trend_relationship, volatility_relationship = self.correlateAssets(asset_symbol, comp, timeunit, timeamount)

			#get the asset class of this comparator
			comp_asset = self.alpaca.get_asset(comp)
			comp_class = comp_asset.__getattr__("class")

			#get the bars from the past
			if (comp_class == "crypto"):
				comp_bars = self.getCryptoBars(comp, timeunit, timeamount)
			elif (comp_class == "us_equity"):
				comp_bars = self.getStockBars(comp, timeunit, timeamount)

			#get the trend and volatility data for this asset
			trend, volatility, vol_change = self.getAssetData(comp_bars)

			#predict the future trend of the main asset based on the data from this asset and the relationship between them
			if (trend_relationship == "linear"):
				if (trend > 0):
					trend_prediction = "up"
				elif (trend < 0):
					trend_prediction = "down"
			elif (trend_relationship == "inverse"):
				if (trend > 0):
					trend_prediction = "down"
				elif (trend < 0):
					trend_prediction = "up"

			#predict the future volatility of the main asset based on the data from this asset and the relationship between them
			if (volatility_relationship == "linear"):
				if (vol_change > 0):
					vol_prediction = "up"
				elif (vol_change < 0):
					vol_prediction = "down"
			elif (volatility_relationship == "inverse"):
				if (vol_change > 0):
					vol_prediction = "down"
				elif (vol_change < 0):
					vol_prediction = "up"

			#create keys to access trend and volatility predictions in the dictionary
			trend_key = comp + "_trend_pred"
			volatility_key = comp + "_volatility_pred"

			#store the relationships of the main asset and the comparators in the relationships dictionary
			asset_rels[trend_key] = trend_prediction
			asset_rels[volatility_key] = vol_prediction

		#return a dictionary with the predictions of each comparator asset
		return asset_rels

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
	def getStockBars(self, symbol, unit="hour", timeamount=1):
		#get the current time in the form of a UTC timestamp and make start and end variables
		start = datetime.now()
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
	def getCryptoBars(self, symbol, unit="hour", timeamount=1):
		#get the current time in the form of a UTC timestamp and make start and end variables
		start = datetime.now()
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
