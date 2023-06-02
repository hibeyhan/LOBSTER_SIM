import abc
import numpy as np
import pandas as pd
from models import Order
from exchange import Exchange
from typing import Deque, Dict, List
from orders import Order
import datetime
import math
from pickle import dump
from pickle import load

class Agent(metaclass=abc.ABCMeta):

    def __init__(
            self,
            assets: int = None,
            cash: float = None,
            exchange: Exchange = None,
            sent_orders: List[Order] = None,
            executed_orders: List = [],
            historical_balance=[[],[]],
            my_price_impact: List=[[],[]],
            model=None
    ):

        self.assets = assets
        self.cash = cash
        self.exchange = exchange
        self.sent_orders = sent_orders
        self.executed_orders = executed_orders
        self.historical_balance = historical_balance
        self.my_price_impact = my_price_impact
        model=model

    @abc.abstractmethod
    def get_action(self, lob_state) -> np.ndarray:
        pass

    @abc.abstractmethod
    def generate_order(self, lob_state) -> Order:
        pass

    @property
    def name(self) -> str:
        return "Agent"

    @property
    def current_balance(self):
        return self.cash + self.assets * self.exchange.orderbook.midprice

    def clear_order(self, order: Order):
        if order.Direction == 1:
            self.assets += order.Size
            self.cash -= order.Size * order.Price
        else:
            self.assets -= order.Size
            self.cash += order.Size * order.Price

        self.executed_orders.append(order)

    def my_price_impact_when_trade(self):

        price_impact = pd.DataFrame({"Date": self.my_price_impact[0], "PriceImpact": self.my_price_impact[1]})

        price_impact["Date"] = price_impact["Date"].apply(lambda x: datetime.datetime.fromtimestamp(x).time())

        return price_impact

    def my_historical_balance_(self):

        historical_balance = pd.DataFrame({"Date": self.historical_balance[0],
                                           "HistoricalBalance": self.historical_balance[1]})

        historical_balance["Date"] = historical_balance["Date"].apply(lambda x: datetime.datetime.fromtimestamp(x).time())

        return historical_balance


class ExchangeAgent(Agent):

    def get_action(self, lob_state: np.ndarray):
        return

    @property
    def name(self) -> str:
        return "ExchangeAgent"

    def generate_order(self, message) -> Order:

        Time = message[0]
        EventType = message[1]
        OrderID = message[2]
        Size = message[3]
        Price = message[4]
        Direction = message[5]
        SenderID = message[6]

        self.sent_orders.append(Order(Time, EventType, OrderID, Size, Price, Direction, SenderID))

        return Order(Time, EventType, OrderID, Size, Price, Direction, SenderID)


class ImbalanceAgent(Agent):

    def get_action(self, ob):

        if ((ob.imbalance_at_best_n(10) < 0.3) & (self.cash > 0)) or (
                (ob.imbalance_at_best_n(10) > 0.7) & (self.assets > 0)) and (ob.time % 60 <= 0.01):
            return True
        else:
            return False

    def name(self):

        return "Imbalance Agent"

    def generate_order(self, ob) -> Order:

        if (ob.imbalance_at_best_n(10) < 0.3) and (self.cash > 0):
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-100,
                         Size=1, Price=ob.best_ask, Direction=1, SenderID='Imb1')

        elif (self.exchange.orderbook.imbalance_at_best_n(10) > 0.7) and (self.assets > 0):
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-200,
                         Size=1, Price=ob.best_bid, Direction=-1, SenderID='Imb1')

        else:

            return Order(Time=ob.time + 0.001, EventType=7, OrderID=-1,
                         Size=1, Price=ob.best_ask, Direction=1, SenderID='Imb1')

    @property
    def current_balance(self):
        return self.cash + self.assets * self.exchange.orderbook.midprice
    
class BollingerAgent(Agent):

    def get_action(self, ob):
        if math.floor(ob.time / 60) != math.floor(self.exchange.time_log[-2] / 60):
            upper = self.bollinger_bands()[0]
            lower = self.bollinger_bands()[1]

            if (ob.midprice > upper) or (ob.midprice < lower):
                return True
            else:
                return False
        else:
            return False

    def name(self):

        return "Bollinger Agent"

    def generate_order(self, ob) -> Order:

        upper = self.bollinger_bands()[0]
        lower = self.bollinger_bands()[1]

        if (ob.best_ask < lower) and (self.cash > 0):

            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-100,
                         Size=1, Price=ob.best_ask, Direction=1, SenderID='Bol1')

        elif (ob.best_ask > upper) and (self.assets > 0):
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-200,
                         Size=1, Price=ob.best_bid, Direction=-1, SenderID='Bol1')

        else:

            return Order(Time=ob.time + 0.001, EventType=7, OrderID=-1,
                         Size=1, Price=ob.best_ask, Direction=1, SenderID='Bol1')

    def clear_order(self, order: Order):
        if order.Direction == 1:
            self.assets += order.Size
            self.cash -= order.Size * order.Price
        else:
            self.assets -= order.Size
            self.cash += order.Size * order.Price

        self.executed_orders.append(order)

    @property
    def current_balance(self):
        return self.cash + self.assets * self.exchange.orderbook.midprice


    def bollinger_bands(self):

        data = [x[1] for x in self.exchange.ts_data]
        rolling_mean = pd.Series(data[-300:]).mean()
        rolling_std = pd.Series(data[-300:]).std()

        # Calculate the upper and lower Bollinger Bands
        upper_band = rolling_mean + rolling_std*1.5
        lower_band = rolling_mean - rolling_std*1.5

        return upper_band, lower_band


class RegressionAgent(Agent):

    def get_action(self, ob):

        if abs(self.model.predict(ob) - self.exchange.orderbook.midprice) > 0:
            return True
        else:
            return False

    def name(self):

        return "Regression Agent"

    def generate_order(self, ob) -> Order:

        if (self.model.predict(ob) > self.exchange.orderbook.midprice) and (self.cash > 0):
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-100,
                         Size=1, Price=ob.best_ask, Direction=1, SenderID='Reg1')

        elif (self.model.predict(ob) < self.exchange.orderbook.midprice) and (self.assets > 0):
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-200,
                         Size=1, Price=ob.best_bid, Direction=-1, SenderID='Reg1')

        else:

            return Order(Time=ob.time + 0.001, EventType=7, OrderID=-1,
                         Size=1, Price=ob.best_ask, Direction=1, SenderID='Reg1')

    @property
    def current_balance(self):
        return self.cash + self.assets * self.exchange.orderbook.midprice


class LstmAgent(Agent):

    def get_action(self, ob):
        if math.floor(ob.time/60) != math.floor(self.exchange.time_log[-2]/60):

            if (self.prediction(self.exchange.orderbook) > ob.midprice) \
                    or (self.prediction(self.exchange.orderbook) < ob.midprice):
                return True
            else:
                return False
        else:
            return False

    def name(self):

        return "LSTM Agent"

    def generate_order(self, ob) -> Order:

        if (self.prediction(self.exchange.orderbook) > ob.midprice*1.0001) and (self.cash > 0):

            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-100,
                         Size=1, Price=ob.best_ask, Direction=1, SenderID='Bol1')

        elif (self.prediction(self.exchange.orderbook) < ob.midprice*0.9999) and (self.assets > 0):
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-200,
                         Size=1, Price=ob.best_bid, Direction=-1, SenderID='Bol1')

        else:

            return Order(Time=ob.time + 0.001, EventType=7, OrderID=-1,
                         Size=1, Price=ob.best_ask, Direction=1, SenderID='Bol1')

    def clear_order(self, order: Order):
        if order.Direction == 1:
            self.assets += order.Size
            self.cash -= order.Size * order.Price
        else:
            self.assets -= order.Size
            self.cash += order.Size * order.Price

        self.executed_orders.append(order)

    @property
    def current_balance(self):

        return self.cash + self.assets * self.exchange.orderbook.midprice

    def prediction(self, ob):
        model = load_model('LSTM_trained.h5')
        a=[]
        for i in self.exchange.second_data[-30:]:
            a.append((ob.midprice - min(self.exchange.second_data)) /
                                                    (max(self.exchange.second_data) - min(self.exchange.second_data)))

        prediction = model.predict(np.array([[a]]))

        converted_prediction = min(self.exchange.second_data) +\
                               prediction*(max(self.exchange.second_data) - min(self.exchange.second_data))

        return converted_prediction

