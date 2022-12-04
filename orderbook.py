from typing import Deque, Dict, List
from sortedcontainers import SortedDict
from dataclasses import dataclass
import pandas as pd


@dataclass
class Orderbook:
    buy: SortedDict
    sell: SortedDict
    tick_size: int
    time: float

    @property
    def best_bid(self):
        try:
            return next(reversed(self.buy.keys()))
        except:
            return -9999999

    @property
    def size_at_best_bid(self):
        try:
            sum = 0
            for i in self.buy[self.best_bid]:
                sum += i.Size

            return sum

        except:

            return 0

    @property
    def best_ask(self):
        try:
            return next(iter(self.sell.keys()))
        except:
            return 9999999

    @property
    def size_at_best_ask(self):
        try:
            sum = 0
            for i in self.sell[self.best_ask]:
                sum += i.Size

            return sum

        except:

            return 0

    def size_at_best_n_ask(self, n=10):
        try:
            sum_ask = 0
            for i in self.sell.keys()[:n]:
                for j in self.sell[i]:
                    sum_ask += j.Size

            return sum_ask

        except:

            return 0

    def size_at_best_n_bid(self, n=10):
        try:
            sum_bid = 0
            for i in self.buy.keys()[-n:]:
                for j in self.buy[i]:
                    sum_bid += j.Size

            return sum_bid

        except:

            return 0

    @property
    def midprice(self):
        return (self.best_ask + self.best_bid) / 2

    @property
    def imbalance_at_best_prices(self):
        return (self.size_at_best_bid - self.size_at_best_ask) / (self.size_at_best_bid + self.size_at_best_ask)

    def imbalance_at_best_n(self, n=10):
        imbalance = (self.size_at_best_n_bid(n=n) - self.size_at_best_n_ask(n=n)) / (
                    self.size_at_best_n_bid(n=n) + self.size_at_best_n_ask(n=n) + 1)
        return imbalance

    @property
    def spread(self):
        return self.best_ask - self.best_bid

    def get_snapshot(self, level=20):
        lenght_lob = max(len(self.sell.keys()), len(self.buy.keys()))

        bid = {"Bid Limit": [], "Bid Quantity": []}

        for key, value in self.buy.items():
            sut = 0
            for c in value:
                sut += c.Size
            bid["Bid Limit"].append(key)
            bid["Bid Quantity"].append(sut)

        if len(bid["Bid Limit"]) < lenght_lob:
            for i in range(len(bid["Bid Limit"]) + 1, lenght_lob + 1):
                bid["Bid Limit"].append(-99999999)
                bid["Bid Quantity"].append(0)

        ask = {"Ask Limit": [], "Ask Quantity": []}

        for key, value in self.sell.items():
            sut = 0
            for c in value:
                sut += c.Size
            ask["Ask Limit"].append(key)
            ask["Ask Quantity"].append(sut)

        if len(ask["Ask Limit"]) < lenght_lob:
            for i in range(len(ask["Ask Limit"]) + 1, lenght_lob + 1):
                ask["Ask Limit"].append(999999999)
                ask["Ask Quantity"].append(0)

        bids = pd.DataFrame(bid)
        bids = bids.sort_values('Bid Limit', ascending=False)
        bids.reset_index(drop=True, inplace=True)
        asks = pd.DataFrame(ask)

        return pd.concat([bids, asks], axis=1)[:level]