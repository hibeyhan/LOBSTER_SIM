import abc
import numpy as np
import pandas as pd
import os
from models import Order
from exchange import Exchange
from typing import Deque, Dict, List
from orders import Order


class Agent(metaclass=abc.ABCMeta):

    def __init__(
            self,
            assets: int = None,
            cash: float = None,
            exchange: Exchange = None,
            sent_orders: List[Order] = None,
            executed_orders: List = [],
            historical_balance: List = [],
            my_price_impact: List =[]
    ):

        self.assets = assets
        self.cash = cash
        self.exchange = exchange
        self.sent_orders = sent_orders
        self.executed_orders = executed_orders
        self.historical_balance = historical_balance
        self.my_price_impact = my_price_impact

    @abc.abstractmethod
    def get_action(self, lob_state) -> np.ndarray:
        pass

    @abc.abstractmethod
    def generate_order(self, message) -> Order:
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

        if ((ob.imbalance_at_best_n(10) < -0.5) & (self.cash > 0)) or (
                (ob.imbalance_at_best_n(10) > 0.5) & (self.assets > 0)) and (ob.time % 60 <= 0.01):
            return True
        else:
            return False

    def name(self):

        return "Imbalance Agent"

    def generate_order(self, ob) -> Order:

        if (ob.imbalance_at_best_n(10) < -0.5) and (self.cash > 0):
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-100,
                         Size=20, Price=ob.best_ask + 200, Direction=1, SenderID='Imb1')

        elif (self.exchange.orderbook.imbalance_at_best_n(10) > 0.5) and (self.assets > 0):
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-200,
                         Size=20, Price=ob.best_bid - 200, Direction=-1, SenderID='Imb1')

        else:

            return Order(Time=ob.time + 0.001, EventType=7, OrderID=-1,
                         Size=1, Price=ob.best_ask + 2000, Direction=1, SenderID='Imb1')

    def clear_order(self, order: Order):
        if order.Direction == 1:
            self.assets += order.Size
            self.cash -= order.Size * order.Price
        else:
            self.assets -= order.Size
            self.cash += order.Size * order.Price

        self.executed_orders.append(order)

    def current_balance(self):
        return self.cash + self.assets * self.exchange.orderbook.midprice


class BollingerAgent(Agent):

    def get_action(self, ob):

        if ((ob.imbalance_at_best_n(10) < -0.5) & (self.cash > 0)) or (
                (ob.imbalance_at_best_n(10) > 0.5) & (self.assets > 0)):
            return True
        else:
            return False

    def name(self):

        return "Imbalance Agent"

    def generate_order(self, ob) -> Order:

        if (ob.imbalance_at_best_n(10) < -0.5) and (self.cash > 0):
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-100,
                         Size=20, Price=ob.best_ask + 200, Direction=1, SenderID='Imb1')

        elif (self.exchange.orderbook.imbalance_at_best_n(10) > 0.5) and (self.assets > 0):
            return Order(Time=ob.time + 0.001, EventType=1, OrderID=-200,
                         Size=20, Price=ob.best_bid - 200, Direction=-1, SenderID='Imb1')

        else:

            return Order(Time=ob.time + 0.001, EventType=7, OrderID=-1,
                         Size=1, Price=ob.best_ask + 2000, Direction=1, SenderID='Imb1')

    def clear_order(self, order: Order):
        if order.Direction == 1:
            self.assets += order.Size
            self.cash -= order.Size * order.Price
        else:
            self.assets -= order.Size
            self.cash += order.Size * order.Price

        self.executed_orders.append(order)

    def current_balance(self):
        return self.cash + self.assets * self.exchange.orderbook.midprice

