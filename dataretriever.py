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
                 train_period_messages=None,
                 trade_period_messages=None,
                 orders=None
                 ):
        self.ticker = ticker
        self.directory = directory
        self.trade_date = trade_date
        self.messages = messages
        self.initializing_period_messages = initializing_period_messages
        self.train_period_messages = train_period_messages
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
        messages["SenderID"] = "Ex1"

        self.messages = messages

        self.initializing_period_messages =\
            self.messages[self.messages.Time < (dt.datetime.strptime(self.trade_date, '%Y-%m-%d').timestamp() + 37800)]
        self.train_period_messages =\
            self.messages[(self.messages.Time >= (dt.datetime.strptime(self.trade_date, '%Y-%m-%d').timestamp() +
                                                  37800)) and (self.messages.Time < (dt.datetime.strptime(self.trade_date,                                                                                                 '%Y-%m-%d').timestamp() + 37800+3600))]
        self.trade_period_messages =\
            self.messages[self.messages.Time >= (dt.datetime.strptime(self.trade_date, '%Y-%m-%d').timestamp() + 37800+3600)]


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

    #this checks available dates of downloaded in LOBSTER messages files
    def get_available_dates(self, directory=r"C:\Users\Dell\Desktop\LOBSTER"):
        path = os.path.join(directory, self.ticker)
        files = os.listdir(path)
        messages = [x for x in files if "message" in x]
        orders = [x for x in files if "book" in x]
        messages_dates = [x[x.find("_") + 1:x.find("_") + 11] for x in messages]
        order_dates = [x[x.find("_") + 1:x.find("_") + 11] for x in orders]

        if order_dates == order_dates:
            return order_dates
        else:
            return "Messages files and orderbook files and orderbook files have different dates"

    def get_initial_book(self, directory=r"C:\Users\Dell\Desktop\LOBSTER", date="2022-09-05", only_messages=False):

        path = os.path.join(directory, self.ticker)
        list_ = os.listdir(path)
        messages_ = [x for x in list_ if ("message" in x) and (date in x)][0]
        path2 = os.path.join(path, messages_)
        messages = pd.read_csv(path2)
        messages.columns = ["Time", "EventType", "OrderID", "Size", "Price", "Direction", "Extra"]

        def create_cols(level):
            cols = []
            for i in range(1, level + 1):
                cols.append("ASK_PRICE_" + str(i))
                cols.append("ASK_QTY_" + str(i))
                cols.append("BID_PRICE_" + str(i))
                cols.append("BID_QTY_" + str(i))
            return cols

        orders_ = [x for x in list_ if ("book" in x) and (date in x)][0]
        path3 = os.path.join(path, orders_)
        orders = pd.read_csv(path3, nrows=1)
        orders.columns = create_cols(int(orders.shape[1] / 4))
        orders = orders.replace(to_replace=-9999999999, value=0)
        orders = orders.replace(to_replace=9999999999, value=0)
        orders = orders.replace(to_replace=1999999999, value=0)
        orders = orders.replace(to_replace=1999990000, value=0)

        if only_messages:
            return messages
        else:
            return messages, orders
