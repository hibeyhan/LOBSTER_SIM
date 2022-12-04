import datetime as dt
from exchange import Exchange
from agent import ExchangeAgent
from agent import ImbalanceAgent
import numpy as np
import pandas as pd
from dataretriever import DataRetriever


class Simulator:

    def __init__(
            self,
            ticker: str = None,
            directory: str = None,
            date=None,
            exchange=Exchange(),
            messages=None,
            historical_midprice=[],
            time=None,
            time_log=[],
            order_id_list=[]

    ):
        self.ticker = ticker
        self.directory = directory
        self.date = date
        self.exchange = exchange
        self.messages = messages
        self.historical_midprice = historical_midprice
        self.time = time
        self.time_log = time_log
        self.order_id_list = order_id_list

    def initialize_market(self):

        # Agents are added
        self.exchange.agents["Imb1"] = ImbalanceAgent(assets=1000, cash=20000000000,
                                                      exchange=self.exchange, sent_orders=[], executed_orders=[],
                                                      historical_balance=[])

        self.exchange.agents["Ex1"] = ExchangeAgent(assets=10000000, cash=20000000000000,
                                                    exchange=self.exchange, sent_orders=[], executed_orders=[],
                                                    historical_balance=[])

        self.messages = DataRetriever(ticker=self.ticker, directory=self.directory, trade_date=self.date)
        self.messages.get_messages()

        for i in np.array(self.messages.initializing_period_messages):

            order = self.exchange.agents["Ex1"].generate_order(i)

            self.exchange.order_evaluation(order)

            self.exchange.orderbook.time = order.Time

            self.time_log.append(self.exchange.orderbook.time)

    def trading_run(self):

        self.order_id_list = list(self.messages.messages)

        price_impact_before = []
        price_impact_after = []

        for i in np.array(self.messages.trade_period_messages):

            order = self.exchange.agents["Ex1"].generate_order(i)

            self.exchange.order_evaluation(order)

            self.exchange.orderbook.time = order.Time

            self.time_log.append(self.exchange.orderbook.time)

            if self.exchange.orderbook.time % 60 <= 1:

                if self.exchange.agents["Imb1"].get_action():

                    order_to_submit = self.exchange.agents["Imb1"].generate_order()

                    try:
                        order_to_submit.OrderId = max(self.order_id_list) + 1

                        self.order_id_list.append(order_to_submit.OrderId)

                        # measure price impact

                        price_impact_before.append(self.exchange.orderbook.midprice)

                        self.exchange.order_evaluation(order_to_submit)

                        price_impact_after.append(self.exchange.orderbook.midprice)

                        if order_to_submit in self.exchange.executed_orders:

                            self.exchange.agents["Imb1"].clear_order(order_to_submit)

                    except:

                        print("Check order submitted by Imbalance Agent")

            self.exchange.agents["Imb1"].historical_balance.append(self.exchange.agents["Imb1"].current_balance(order))

            self.historical_midprice.append(self.exchange.orderbook.midprice)

            self.time_log.append(self.exchange.orderbook.time)

        price_impact = pd.DataFrame({"before": price_impact_before, "after": price_impact_after})
        self.exchange.agents["Imb1"].price_impact = price_impact["after"] - price_impact["before"]


    def get_lob_moment(self):

        return self.exchange.orderbook.get_snapshot(level=50)


