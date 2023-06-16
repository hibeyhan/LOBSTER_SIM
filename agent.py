import abc
import numpy as np
import pandas as pd
from models import Order
from exchange import Exchange
from typing import Deque, Dict, List
from orders import Order
import datetime
import math
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import RandomForestRegressor
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
            model= None,
            data = None
    ):

        self.assets = assets
        self.cash = cash
        self.exchange = exchange
        self.sent_orders = sent_orders
        self.executed_orders = executed_orders
        self.historical_balance = historical_balance
        self.my_price_impact = my_price_impact
        self.model = model
        self.data = data

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

        if ((self.data.iloc[-1] < 0.3) & (self.cash > 0)) or (
                (self.data.iloc[-1] > 0.7) & (self.assets > 0)) and (
                (math.floor(self.exchange.orderbook.time) != math.floor(self.exchange.time_log[-2]))\
                    & (math.floor(self.exchange.orderbook.time) % 10 == 0)):
            return True
        else:
            return False

    def name(self):

        return "Imbalance Agent"

    def generate_order(self, ob) -> Order:

        if ob.imbalance_at_best_n(10) < 0.3:
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-100,
                         Size=1, Price=ob.best_ask, Direction=1, SenderID='Imb1')

        elif ob.imbalance_at_best_n(10) > 0.7:
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
        if math.floor(self.exchange.orderbook.time) != math.floor(self.exchange.time_log[-2]) and (math.floor(self.exchange.orderbook.time) % 10 == 0):
            upper = self.bollinger_bands()[0]
            lower = self.bollinger_bands()[1]

            if ((self.assets > 0) and (ob.best_ask > upper)) or ((self.cash > 0) and (ob.best_bid < lower)):
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

        if (ob.best_bid < lower) and (self.cash > 0):

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

        rolling_mean = self.data[-30:].mean()
        rolling_std = self.data[-30:].std()

        # Calculate the upper and lower Bollinger Bands
        upper_band = rolling_mean + rolling_std*1.5
        lower_band = rolling_mean - rolling_std*1.5

        return upper_band, lower_band


class RandomForest(Agent):

    def get_action(self, ob):
        if (math.floor(self.exchange.orderbook.time) != math.floor(self.exchange.time_log[-2]))\
                    & (math.floor(self.exchange.orderbook.time) % 10 == 0):
            if ((self.model.predict([np.array(self.data.iloc[-1, 1:])]) == 1) and
                    (self.model.predict([np.array(self.data.iloc[-2, 1:])]) == 1)) or\
                    ((self.model.predict([np.array(self.data.iloc[-1, 1:])]) == 0)
                     and (self.model.predict([np.array(self.data.iloc[-2, 1:])]) == 0)):
                return True
            else:
                return False
        else:
            return False

    def name(self):

        return "Random Forest"

    def generate_order(self, ob) -> Order:

        if (self.model.predict([np.array(self.data.iloc[-1, 1:])]) == 1) and (self.cash > 0):

            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-100,
                         Size=1, Price=ob.best_ask, Direction=1, SenderID='RF1')

        elif (self.model.predict([np.array(self.data.iloc[-1, 1:])]) == 0) and (self.assets > 0):
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-200,
                         Size=1, Price=ob.best_bid, Direction=-1, SenderID='RF1')

        else:

            return Order(Time=ob.time + 0.001, EventType=7, OrderID=-1,
                         Size=1, Price=ob.best_ask, Direction=1, SenderID='RF1')

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

    def train_my_model(self):

        features = self.data.copy()
        features["close_shifted"] = features["Midprice"].shift(1)
        features["diff"] = features["Midprice"] - features["close_shifted"]

        def fun(x):
            if x <= 0:
                return 0
            else:
                return 1

        features["actual"] = features["diff"].apply(fun)
        features = features.reset_index()
        features.drop(["Time", "close_shifted", "diff"], axis=1, inplace=True)


        # Create data
        X = features.loc[:, "Midprice":"imbalance20"]
        y = features["actual"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.01)


        # creating a RF classifier
        self.model = RandomForestClassifier(n_estimators=100, random_state=123)

        # Training the model on the training dataset
        # fit function is used to train the model using the training sets as parameters
        self.model.fit(X_train, y_train)





