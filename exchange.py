import datetime
from typing import Deque, Dict, List
from orderbook import Orderbook
from orders import Order
import datetime
from typing import Deque, Dict, List
from sortedcontainers import SortedDict
from collections import deque
import math
import os

#this is class for exchange
class Exchange:

    def __init__(
            self,
            name: str = "NASDAQ",
            ticker: str = "TSLA",
            tick_size: int = 100,
            orderbook: Orderbook = Orderbook(SortedDict(), SortedDict(), 100, 2000000000),
            time: datetime.datetime = None,
            agents={},
            executed_orders: List[Order] = [],
            ts_data=[],
            time_log=[],
            second_data={"time":[], "midprice":[], "imb10":[]}
    ):
        self.name = name
        self.ticker = ticker
        self.tick_size = tick_size
        self.orderbook = orderbook
        self.time = time
        self.agents = agents
        self.executed_orders = executed_orders
        self.ts_data = ts_data
        self.time_log = time_log
        self.second_data = second_data

    # function that doing order evaluation as exchange receives 7 types of order
    def order_evaluation(self, x: Order):

        if x.EventType == 5:
            pass

        elif x.EventType == 6:
            pass

        elif x.EventType == 7:
            pass

        elif x.EventType == 2:
            self.cancellation(x)

        elif x.EventType == 3:
            self.deletion(x)

        elif x.EventType == 1:
            if self.is_executable(x):
                self.execute_order(x)
            else:
                self.new_submission(x)

        elif x.EventType == 4:
            x.Direction = -x.Direction
            if self.is_executable(x):
                self.execute_order(x)
            else:
                self.new_submission(x)

        self.orders_fillable()

    def is_executable(self, order: Order):

        if order.Direction == 1:

            if order.Price >= self.orderbook.best_ask:
                return True
            else:
                return False

        elif order.Direction == -1:

            if order.Price <= self.orderbook.best_bid:
                return True
            else:
                return False

    def execute_order(self, order: Order):

        if order.Direction == -1:
            while order.Price <= self.orderbook.best_bid:
                if order.Size < self.orderbook.size_at_best_bid:
                    if order.Size > self.next_order_to_buy.Size:
                        order.Size -= self.next_order_to_buy.Size
                        self.executed_orders.append(self.next_order_to_buy)
                        del self.orderbook.buy[next(reversed(self.orderbook.buy))][0]
                        if len(self.orderbook.buy[self.orderbook.best_bid]) == 0:
                            del self.orderbook.buy[self.orderbook.best_bid]

                    elif order.Size == self.next_order_to_buy.Size:
                        order.Size -= self.next_order_to_buy.Size
                        self.executed_orders.append(self.next_order_to_buy)
                        del self.orderbook.buy[next(reversed(self.orderbook.buy))][0]
                        if len(self.orderbook.buy[self.orderbook.best_bid]) == 0:
                            del self.orderbook.buy[self.orderbook.best_bid]

                    elif order.Size < self.next_order_to_buy.Size:
                        self.orderbook.buy[next(reversed(self.orderbook.buy))][0].Size -= order.Size
                        self.executed_orders.append(order)

                        if len(self.orderbook.buy[self.orderbook.best_bid]) == 0:
                            del self.orderbook.buy[self.orderbook.best_bid]

                        break

                elif order.Size == self.orderbook.size_at_best_bid:
                    if order.Size > self.next_order_to_buy.Size:
                        order.Size -= self.next_order_to_buy.Size
                        self.executed_orders.append(self.next_order_to_buy)
                        del self.orderbook.buy[next(reversed(self.orderbook.buy))][0]
                        if len(self.orderbook.buy[self.orderbook.best_bid]) == 0:
                            del self.orderbook.buy[self.orderbook.best_bid]

                    elif order.Size == self.next_order_to_buy.Size:
                        self.next_order_to_buy.Size -= order.Size
                        self.executed_orders.append(self.next_order_to_buy)
                        del self.orderbook.buy[next(reversed(self.orderbook.buy))][0]
                        if len(self.orderbook.buy[self.orderbook.best_bid]) == 0:
                            del self.orderbook.buy[self.orderbook.best_bid]

                    elif order.Size < self.next_order_to_buy.Size:
                        self.next_order_to_buy.Size -= order.Size
                        self.executed_orders.append(order)
                        if len(self.orderbook.buy[self.orderbook.best_bid]) == 0:
                            del self.orderbook.buy[self.orderbook.best_bid]

                elif order.Size > self.orderbook.size_at_best_bid:
                    if len(self.orderbook.buy[self.orderbook.best_bid]) != 0:
                        if order.Size > self.next_order_to_buy.Size:
                            order.Size -= self.next_order_to_buy.Size
                            self.executed_orders.append(self.next_order_to_buy)
                            del self.orderbook.buy[next(reversed(self.orderbook.buy))][0]
                            if len(self.orderbook.buy[self.orderbook.best_bid]) == 0:
                                del self.orderbook.buy[self.orderbook.best_bid]
                    else:
                        del self.orderbook.buy[self.orderbook.best_bid]
            else:
                order.Direction = order.Direction
                self.new_submission(order)

        else:

            while order.Price >= self.orderbook.best_ask:
                if order.Size < self.orderbook.size_at_best_ask:
                    if order.Size > self.next_order_to_sell.Size:
                        order.Size -= self.next_order_to_sell.Size
                        self.executed_orders.append(self.next_order_to_sell)
                        del self.orderbook.sell[next(iter(self.orderbook.sell))][0]
                        if len(self.orderbook.sell[self.orderbook.best_ask]) == 0:
                            del self.orderbook.sell[self.orderbook.best_ask]

                    elif order.Size == self.next_order_to_sell.Size:
                        order.Size -= self.next_order_to_sell.Size
                        self.executed_orders.append(self.next_order_to_sell)
                        del self.orderbook.sell[next(iter(self.orderbook.sell))][0]
                        if len(self.orderbook.sell[self.orderbook.best_ask]) == 0:
                            del self.orderbook.sell[self.orderbook.best_ask]

                    elif order.Size < self.next_order_to_sell.Size:
                        self.next_order_to_sell.Size -= order.Size
                        self.executed_orders.append(order)
                        if len(self.orderbook.sell[self.orderbook.best_ask]) == 0:
                            del self.orderbook.sell[self.orderbook.best_ask]

                        break

                elif order.Size == self.orderbook.size_at_best_ask:
                    if order.Size > self.next_order_to_sell.Size:
                        order.Size -= self.next_order_to_sell.Size
                        self.executed_orders.append(self.next_order_to_sell)
                        del self.orderbook.sell[next(iter(self.orderbook.sell))][0]
                        if len(self.orderbook.sell[self.orderbook.best_ask]) == 0:
                            del self.orderbook.sell[self.orderbook.best_ask]

                    elif order.Size == self.next_order_to_sell.Size:
                        self.next_order_to_sell.Size -= order.Size
                        self.executed_orders.append(self.next_order_to_sell)
                        del self.orderbook.sell[next(iter(self.orderbook.sell))][0]
                        if len(self.orderbook.sell[self.orderbook.best_ask]) == 0:
                            del self.orderbook.sell[self.orderbook.best_ask]

                    elif order.Size < self.next_order_to_sell.Size:
                        self.next_order_to_sell.Size -= order.Size
                        self.executed_orders.append(order)

                elif order.Size > self.orderbook.size_at_best_ask:
                    if len(self.orderbook.sell[self.orderbook.best_ask]) != 0:
                        if order.Size > self.next_order_to_sell.Size:
                            order.Size -= self.next_order_to_sell.Size
                            self.executed_orders.append(self.next_order_to_sell)
                            del self.orderbook.sell[next(iter(self.orderbook.sell))][0]
                            if len(self.orderbook.sell[self.orderbook.best_ask]) == 0:
                                del self.orderbook.sell[self.orderbook.best_ask]
                    else:
                        del self.orderbook.sell[self.orderbook.best_ask]
            else:
                order.Direction = order.Direction
                self.new_submission(order)

    def new_submission(self, order: Order):

        if order.Direction == 1:

            if order.Price in self.orderbook.buy:
                self.orderbook.buy[order.Price].append(order)
            else:
                self.orderbook.buy[order.Price] = deque([order])
        else:
            if order.Price in self.orderbook.sell:
                self.orderbook.sell[order.Price].append(order)
            else:
                self.orderbook.sell[order.Price] = deque([order])

    def cancellation(self, order: Order):

        if order.Direction == 1:

            position = self.find_order_position(order, self.orderbook.buy)

            if order.Price in self.orderbook.buy:
                if position == "NA":
                    pass
                elif position != "NA":
                    if self.orderbook.buy[order.Price][position].Size >= order.Size:
                        self.orderbook.buy[order.Price][position].Size -= order.Size

                        if self.orderbook.buy[order.Price][position].Size == 0:
                            del self.orderbook.buy[order.Price][position]

                        if len(self.orderbook.buy[order.Price]) == 0:
                            del self.orderbook.buy[order.Price]
                    else:
                        pass


        elif order.Direction == -1:

            position = self.find_order_position(order, self.orderbook.sell)

            if order.Price in self.orderbook.sell:
                if position == "NA":
                    pass
                elif position != "NA":
                    if self.orderbook.sell[order.Price][position].Size >= order.Size:
                        self.orderbook.sell[order.Price][position].Size -= order.Size
                        if self.orderbook.sell[order.Price][position].Size == 0:
                            del self.orderbook.sell[order.Price][position]

                        if len(self.orderbook.sell[order.Price]) == 0:
                            del self.orderbook.sell[order.Price]
                    else:
                        pass

    def deletion(self, order: Order):

        if order.Direction == 1:

            position = self.find_order_position(order, self.orderbook.buy)

            if order.Price not in self.orderbook.buy:
                pass

            elif order.Price in self.orderbook.buy:
                if position == "NA":
                    pass
                elif position != "NA":
                    if order.Size >= self.orderbook.buy[order.Price][position].Size:
                        del self.orderbook.buy[order.Price][position]
                        if len(self.orderbook.buy[order.Price]) == 0:
                            del self.orderbook.buy[order.Price]
                else:
                    pass

        elif order.Direction == -1:

            position = self.find_order_position(order, self.orderbook.sell)

            if order.Price not in self.orderbook.sell:
                pass

            elif order.Price in self.orderbook.sell:
                if position == "NA":
                    pass
                elif position != "NA":
                    if order.Size >= self.orderbook.sell[order.Price][position].Size:
                        del self.orderbook.sell[order.Price][position]
                        if len(self.orderbook.sell[order.Price]) == 0:
                            del self.orderbook.sell[order.Price]
                else:
                    pass

    def orders_fillable(self):

        while self.orderbook.best_bid >= self.orderbook.best_ask:

            if self.next_order_to_buy.Size > self.next_order_to_sell.Size:

                self.orderbook.buy[next(reversed(self.orderbook.buy))][0].Size -= self.next_order_to_sell.Size
                self.executed_orders.append(self.orderbook.sell[next(iter(self.orderbook.sell))][0])
                del self.orderbook.sell[next(iter(self.orderbook.sell))][0]
                if len(self.orderbook.sell[self.orderbook.best_ask]) == 0:
                    del self.orderbook.sell[self.orderbook.best_ask]

            elif self.next_order_to_buy.Size == self.next_order_to_sell.Size:

                self.executed_orders.append(self.orderbook.sell[next(iter(self.orderbook.sell))][0])
                self.executed_orders.append(self.orderbook.buy[next(reversed(self.orderbook.buy))][0])

                del self.orderbook.sell[next(iter(self.orderbook.sell))][0]
                del self.orderbook.buy[next(reversed(self.orderbook.buy))][0]

                if len(self.orderbook.sell[self.orderbook.best_ask]) == 0:
                    del self.orderbook.sell[self.orderbook.best_ask]

                if len(self.orderbook.buy[self.orderbook.best_bid]) == 0:
                    del self.orderbook.buy[self.orderbook.best_bid]


            elif self.next_order_to_buy.Size < self.next_order_to_sell.Size:

                self.orderbook.sell[next(iter(self.orderbook.sell))][0].Size -= self.next_order_to_buy.Size
                self.executed_orders.append(self.orderbook.buy[next(reversed(self.orderbook.buy))][0])
                del self.orderbook.buy[next(reversed(self.orderbook.buy))][0]

                if len(self.orderbook.buy[self.orderbook.best_bid]) == 0:
                    del self.orderbook.buy[self.orderbook.best_bid]


    @property
    def best_sell_price(self):
        return next(iter(self.orderbook.sell.keys()), np.infty)

    @property
    def best_buy_price(self):
        return next(reversed(self.orderbook.buy), 0)

    @property
    def orderbook_price_range(self):
        sell_prices = reversed(self.orderbook.sell)
        buy_prices = iter(self.orderbook.buy.keys())
        return sell_prices, buy_prices

    @property
    def next_order_to_buy(self):
        return self.orderbook.buy[next(reversed(self.orderbook.buy))][0]

    @property
    def next_order_to_sell(self):
        return self.orderbook.sell[next(iter(self.orderbook.sell))][0]

    @staticmethod
    def find_order_position(x: Order, y):
        position = 0
        if x.Price in y:
            for i, j in enumerate(y[x.Price]):
                if j.OrderID == x.OrderID:
                    position = i
                    break
                else:
                    position = "NA"
        return position

    def store_timeseries_data(self, order):
        if len(self.time_log) > 2:
            if math.floor(order.Time / 15) != math.floor(self.time_log[-2] / 15):
                self.ts_data.append((order.Time, order.Price))

