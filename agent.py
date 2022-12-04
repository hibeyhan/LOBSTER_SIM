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
            historical_balance: List = []
    ):

        self.assets = assets
        self.cash = cash
        self.exchange = exchange
        self.sent_orders = sent_orders
        self.executed_orders = executed_orders
        self.historical_balance = historical_balance

    @abc.abstractmethod
    def get_action(self, lob_state: np.ndarray) -> np.ndarray:
        pass

    @abc.abstractmethod
    def generate_order(self, message=None) -> Order:
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

    def get_action(self):

        if ((self.exchange.orderbook.imbalance_at_best_n(10) < -0.5) & (self.cash > 0)) or (
                (self.exchange.orderbook.imbalance_at_best_n(10) > 0.5) & (self.assets > 0)):
            return True
        else:
            return False

    def name(self):

        return "Imbalance Agent"

    def generate_order(self) -> Order:

        if (self.exchange.orderbook.imbalance_at_best_n(10) < -0.5) and (self.cash > 0):
            return Order(Time=self.exchange.orderbook.time + 0.001, EventType=1, OrderID=-100,
                         Size=100, Price=self.exchange.orderbook.best_ask + 200, Direction=1, SenderID='Imb1')

        elif (self.exchange.orderbook.imbalance_at_best_n(10) > 0.5) and (self.assets > 0):
            return Order(Time=self.exchange.orderbook.time + 0.001, EventType=1, OrderID=-200,
                         Size=100, Price=self.exchange.orderbook.best_bid - 200, Direction=-1, SenderID='Imb1')

        else:

            return Order(Time=self.exchange.orderbook.time + 0.001, EventType=7, OrderID=-1,
                         Size=1, Price=self.exchange.orderbook.best_ask + 2000, Direction=1, SenderID='Imb1')

    def clear_order(self, order: Order):
        if order.Direction == 1:
            self.assets += order.Size
            self.cash -= order.Size * order.Price
        else:
            self.assets -= order.Size
            self.cash += order.Size * order.Price

        self.executed_orders.append(order)

    def current_balance(self, order):
        return self.cash + self.assets * order.Price