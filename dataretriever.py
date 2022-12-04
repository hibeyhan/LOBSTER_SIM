import datetime as dt
import os
import pandas as pd
import time
import datetime as dt
from orders import Order


class DataRetriever:

    def __init__(self,
                 ticker: str = None,
                 directory: str = None,
                 trade_date=None,
                 messages=None,
                 initializing_period_messages=None,
                 trade_period_messages=None,
                 orders=None
                 ):
        self.ticker = ticker
        self.directory = directory
        self.trade_date = trade_date
        self.messages = messages
        self.initializing_period_messages = initializing_period_messages
        self.trade_period_messages = trade_period_messages
        self.orders = orders

    def get_messages(self):

        path = os.path.join(self.directory, self.ticker)
        list_ = os.listdir(path)
        messages_ = [x for x in list_ if (("message" in x) and (self.trade_date in x))][0]
        path2 = os.path.join(path, messages_)
        messages = pd.read_csv(path2, low_memory=False)
        messages.columns = ["Time", "EventType", "OrderID", "Size", "Price", "Direction", "SenderID"]
        messages["Time"] = messages["Time"].apply(lambda n: n + time.mktime(
                                                            dt.datetime.strptime(self.trade_date, "%Y-%m-%d").timetuple()))
        messages["SenderID"] = "EX1"

        self.messages = messages

        self.initializing_period_messages =\
            self.messages[self.messages.Time < (dt.datetime.strptime(self.trade_date, '%Y-%m-%d').timestamp() + 35100)]
        self.trade_period_messages =\
            self.messages[self.messages.Time >= (dt.datetime.strptime(self.trade_date, '%Y-%m-%d').timestamp() + 35100)]


    def get_orders(self, level=50):
        path = os.path.join(self.directory, self.ticker)
        list_ = os.listdir(path)
        cols = []

        for i in range(1, 51):
            cols.append("ASK_PRICE_" + str(i))
            cols.append("ASK_QTY_" + str(i))
            cols.append("BID_PRICE_" + str(i))
            cols.append("BID_QTY_" + str(i))

        orders_ = [x for x in list_ if ("book" in x) and (self.trade_date in x)][0]
        path3 = os.path.join(path, orders_)
        orders = pd.read_csv(path3, nrows=1000)
        orders.columns = cols

        # sorting outliers

        orders = orders.replace(to_replace=-9999999999, value=0)
        orders = orders.replace(to_replace=9999999999, value=0)
        orders = orders.replace(to_replace=1999999999, value=0)
        orders = orders.replace(to_replace=1999990000, value=0)

        self.orders = orders



    def get_filtered_messages(self, start, end):
        messages1 = self.messages[(self.messages.Time > dt.datetime.strptime(start, '%Y-%m-%d %H:%M').timestamp())
                                  & (self.messages.Time < dt.datetime.strptime(end, '%Y-%m-%d %H:%M').timestamp())]
        return messages1