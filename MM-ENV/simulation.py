from maker import SimpleMarketMaker as MarketMaker, OrderType
from mm_game import MarketData
from typing import Tuple
from logger import Logger
from datetime import datetime
from math import floor
import numpy as np

# Constants
# Time interval for simulation
INTERVAL = 60*390

# Initial buy and sell prices
INIT_BUY = 100.5
INIT_SELL = 99.5

# Initial money
START_MONEY = 10000

class Simulation():
    """
    A class to simulate the market maker game.
    """
    def __init__(self, maker: MarketMaker):
        self.mm = MarketData(INIT_BUY, INIT_SELL)
        self.start_time = datetime.now()
        log_filename = f"log/{self.start_time.strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = Logger(log_filename)
        self.market_maker = maker
        self.buy = []
        self.mmBuy = [INIT_BUY]
        self.mmSell = [INIT_SELL]
        self.buyVolume = []
        self.sellVolume = []
        self.sell = []
        self.profit = []
        self.holding = 0
        self.money = START_MONEY
        # format: [price, volume, buy/sell, from_time, to_time]
        self.limit_order_queue = []

    def checkAndUpdate(self, prevBuy, prevSell, timestamp, logging = False)  -> Tuple[float, int, float, int, OrderType]:
        """
        Check the current market and update the market maker. Make sure that input is valid before
        putting it into the market maker.
        """
        buy, vb, sell, vs, order_type = self.market_maker.update(prevBuy, prevSell, timestamp)
        if(buy < 0):
            if(logging):
                self.logger.warning("Buy price is negative, setting volume to 0")
            vb = 0
        if(sell < 0):
            if(logging):
                self.logger.warning("Sell price is negative, setting volume to 0")
            vs = 0
        if(vb < 0):
            if(logging):
                self.logger.warning("Buying negative volume, setting volume to 0")
            vb = 0
        if(vs < 0):
            if(logging):
                self.logger.warning("Selling negative volume, setting volume to 0")
            vs = 0
        if(vs > self.holding):
            if(logging):
                self.logger.warning("Selling more than holding, setting volume to holding")
            vs = self.holding
        return buy, vb, sell, vs, order_type
    
    def reset(self):
        self.start_time = datetime.now()
        log_filename = f"log/{self.start_time.strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = Logger(log_filename)
        self.mm = MarketData(INIT_BUY, INIT_SELL)
        self.buy = []
        self.mmBuy = [INIT_BUY]
        self.mmSell = [INIT_SELL]
        self.buyVolume = []
        self.sellVolume = []
        self.sell = []
        self.profit = []
        self.holding = 0
        self.limit_order_queue = []

    def executeLimitOrders(self, market_sell, market_buy, timestamp, logging = False):
        """
        Execute limit orders that are valid at the current timestamp

        The buy limit order can only be executed at the limit price or lower (compare to market ask/sell price),
        and a sell limit order can only be executed at the limit price or higher (compare to market bid/buy price).

        :param market_sell: the current market sell price
        :param market_buy: the current market buy price
        :param timestamp: the current timestamp
        :param logging: whether to log the execution of limit orders
        """
        profit = 0.0
        for order in self.limit_order_queue:
            price = order[0]
            volume = order[1]
            buy_sell = order[2]
            from_time = order[3]
            to_time = order[4]
            
            # remove all orders that are expired
            if timestamp > to_time:
                self.limit_order_queue.remove(order)
                continue

            if timestamp < from_time:
                continue

            if buy_sell == "sell" and price >= market_buy and self.holding >= 0:
                if(logging):
                    self.logger.info(f"Executing Limit Order: Selling at {market_buy} with limit price at {price} for {volume}")
                if(volume > self.holding):
                    volume = self.holding
                    if(logging):
                        self.logger.warning(f"Selling more than holding, setting volume to {volume}")
                self.money += market_buy * volume
                self.holding -= volume
                self.limit_order_queue.remove(order)
                profit += price * volume

            if buy_sell == "buy" and price <= market_sell and self.money >= 0:
                if(logging):
                    self.logger.info(f"Executing Limit Order: Buying at {market_buy} with limit price at {price} for {volume}")
                max_buyable_volume = floor(self.money / market_sell)
                if volume > max_buyable_volume:
                    volume = max_buyable_volume
                    if(logging):
                        self.logger.warning(f"Buying more than available money, setting volume to {volume}")
                self.money -= market_sell * volume
                self.holding += volume
                self.limit_order_queue.remove(order)
                profit += -price * volume
        return profit


    def addLimitOrder(self, price, volume, buy_sell, from_time, to_time, logging = False):
        if(logging):
            self.logger.info(f"Adding Limit Order: {buy_sell} at {price} for {volume} from {from_time} to {to_time}")
        self.limit_order_queue.append([price, volume, buy_sell, from_time, to_time])

    def executeOrders(self, market_buy, market_sell, volume_buy, volume_sell, logging = False) -> float:
        """
        Execute market orders
        
        :param market_buy: the current market buy price
        :param market_sell: the current market sell price
        :param volume_buy: the volume to buy
        :param volume_sell: the volume to sell
        :param logging: whether to log the execution of market orders
        """
        
        max_buyable_volume = floor(self.money / market_sell)
        if volume_buy > max_buyable_volume:
            volume_buy = max_buyable_volume
            if(logging):
                self.logger.warning(f"Buying more than available money, setting volume to {volume_buy}")
        if(logging and volume_buy > 0):
            self.logger.info(f"Buying at {market_buy} for {volume_buy}")
        self.money -= market_sell * volume_buy
        self.holding += volume_buy

        if(volume_sell > self.holding):
            volume_sell = self.holding
            if(logging):
                self.logger.warning(f"Selling more than holding, setting volume to {volume_sell}")

        if(logging and volume_sell > 0):
            self.logger.info(f"Selling at {market_sell} with market price at for {volume_sell}")
        self.money += market_sell * volume_sell
        self.holding -= volume_sell

        return 0.0 - (market_sell * volume_buy) + (market_buy * volume_sell)

    def run(self, logging = False):
        """
        Runs the market simulation for a predefined number of intervals.
        """

        i = 0
        mmBuy = self.mmBuy[0]
        mmSell = self.mmSell[0]

        if(logging):
            self.logger.log("Simulation Start")
            self.logger.log(f"Start time: {self.start_time}")
            self.logger.log(f"Initial Market: Buy: {mmBuy} Sell: {mmSell}")
            self.logger.spacing()

        while(i < INTERVAL):
            mb, vb, mS, vs, OrderType = self.checkAndUpdate(mmBuy, mmSell, i, logging)
            if(logging):
                self.logger.log(f"Interval: {i}")
                self.logger.log(f"Market: Buy: {mmBuy} Sell: {mmSell}")
                self.logger.log(f"Buy limit: {mb} Volume: {vb} Sell limit: {mS} Volume: {vs} Order Type: {OrderType}")

            if(OrderType.type == "limit"):
                [mmBuy, mmSell] = self.mm.getNextPrices(mb, vb, mS, vs)
            elif(OrderType.type == "market"):
                mmBuy += np.random.uniform(-mmBuy / 20, mmBuy / 30)
                mmSell += np.random.uniform(-mmSell / 20, mmSell / 30)
                [mmBuy, mmSell] = self.mm.getNextPrices(mmBuy, vb, mmSell, vs)

            self.mmBuy.append(mmBuy)
            self.mmSell.append(mmSell)
            
            self.buy.append(mb)
            self.buyVolume.append(vb)
            self.sell.append(mS)
            self.sellVolume.append(vs)

            profit = 0.0
            if(OrderType.type == "limit"):
                if(vb > 0):
                    self.addLimitOrder(mb, vb, "buy", OrderType.from_time, OrderType.to_time)
                if(vs > 0):
                    self.addLimitOrder(mS, vs, "sell", OrderType.from_time, OrderType.to_time)
            elif(OrderType.type == "market"):
                # execute market orders
                profit += self.executeOrders(mmBuy, mmSell, vb, vs, logging)

            profit += self.executeLimitOrders(mmSell, mmBuy, i, logging)

            self.profit.append(profit)
            if(logging):
                self.logger.log(f"Profit: {self.holding * (self.mmSell[-1]) + self.money - START_MONEY} Net change: {profit} Holding: {self.holding}")
                self.logger.log(f"Cash: {self.money}")
                self.logger.spacing()
            i += 1
    
    def summarize(self, logging = False):
        print(f"Total profit: {self.holding * (self.mmSell[-1]) + self.money - START_MONEY}")
        print(f"Total holding: {self.holding} at price {self.mmSell[-1]} for a total of {self.holding * self.mmSell[-1]}")
        print(f"Total cash: {self.money}")

        if(logging):
            self.logger.log("Simulation End")
            self.logger.log(f"Total profit: {self.holding * (self.mmSell[-1]) + self.money - START_MONEY}")
            self.logger.log(f"Total cash: {self.money}")
            self.logger.log(f"Total holding: {self.holding} at price {self.mmSell[-1]} for a total of {self.holding * self.mmSell[-1]}")
            self.logger.spacing()

        final = self.holding * (self.mmSell[-1]) + self.money
        print(f"Final Revenue: {final}")
        if(logging):
            self.logger.log(f"Final Revenue: {final}")
            self.logger.spacing()

        self.reset()