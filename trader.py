from dotenv import load_dotenv
import random
import math
import os
import alpaca_trade_api as alpaca_api
import pandas as pd

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

		print(len(stocks))

		#shuffle the values of the stock to make random selections
		random.shuffle(stocks)
		return stocks

	#gets the latest bar of a stock based on the symbol
	def getStockBar(self, symbol):
		stockprice = self.alpaca.get_latest_bar(symbol)

		return stockprice

	#places an order for a stock
	def buyStock(self, symbol, money):
		#check to see if this stock is fractionable
		fractionable = self.alpaca.get_asset(symbol)
		fractionable = fractionable.fractionable

		#place an order or return False depending on if the stock is fractional
		if (fractionable):
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

			#get the minimum order size and trade increment for this order to work
			stock_asset = self.alpaca.get_asset(symbol)
			min_order = stock_asset.min_order_size
			min_trade_increment =  stock_asset.min_trade_increment

			#create a quantity that is based on the minimum trade increment in order for the selling to work
			increment_amount = math.floor(float(quantity)/float(min_trade_increment))
			quantity = int(increment_amount) * float(min_trade_increment)

			#the quantity to order must be more than the minimum order amount for it to process
			if (float(quantity) >= float(min_order)):
				#return an order for selling a stock
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
			#return false if this stock is not a currently held position
			return False

	#a function that randomly buys and sells stocks based on the sudoku board values
	def cascadeStocks(self, numbers):
		#get a random list of stocks
		stocks = self.snp500()

		#get the current positions of this account and make a list of the symbols of these positions
		positions = self.alpaca.list_positions()
		stock_positions = []
		for pos in positions:
			stock_positions.append(pos.symbol)

		#get the amount of cash available for the alpaca account and set half aside for buying positions
		cash = float(self.alpaca.get_account().cash)/2

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
				print("Selling all shares in current position...")
				order = self.sellStock(stock)

				#if the selling does not work, buy more of this crypto
				if (not order):
					print("Too little shares to sell, buying more shares...")
					order = self.buyStock(stock, cash_alloted)
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
				print("Order not carried out.")

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

	#places an order for a cryptocurrency
	def buyCrypto(self, symbol, money):
		#get the price of the coin and the minimum quantity for an order to work
		cryptoprice = self.getCryptoBar(symbol).close
		min_order = self.alpaca.get_asset(symbol).min_order_size

		print("Quantity to Buy:", float(money)/float(cryptoprice))

		#if the quantity is larger than the minimum order number, order crypto
		if (float(money)/float(cryptoprice) >= float(min_order)):
			#return an order for crypto, the time in force is "gtc" for "Good Till Cancelled"
			return self.alpaca.submit_order(
				symbol=symbol,
				notional=money,
				side="buy",
				type="market",
				time_in_force="gtc"
			)
		else:
			#return false if this order is too small to be carried out
			return false

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
			increment_amount = math.floor(float(quantity)/float(min_trade_increment))
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
	def cascadeCrypto(self, numbers):
		#get a random list of crypto coins
		coins = self.cryptoCoins()

		#get the current positions of this account and make a list of the symbols of these positions
		positions = self.alpaca.list_positions()
		crypto_positions = []
		for pos in positions:
			crypto_positions.append(pos.symbol)

		#get the amount of cash available for the alpaca account and set half aside for buying positions
		cash = float(self.alpaca.get_account().cash)/2

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
				print("Selling all shares in current position...")
				order = self.sellCrypto(coin)

				#if the selling does not work, buy more of this crypto
				if (not order):
					print("Too little shares to sell, buying more shares...")
					order = self.buyCrypto(coin, cash_alloted)
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
				print("Order not carried out.")

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
