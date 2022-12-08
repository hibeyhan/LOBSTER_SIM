import datetime as dt
from exchange import Exchange
from agent import ExchangeAgent
from agent import ImbalanceAgent
import numpy as np
import pandas as pd
from dataretriever import DataRetriever
from models import Order
import random
import copy


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
            orderbook_moments={},
            time_log=[],
            submitted_orders=[],
            order_id_list=[]

    ):
        self.ticker = ticker
        self.directory = directory
        self.date = date
        self.exchange = exchange
        self.messages = messages
        self.historical_midprice = historical_midprice
        self.time = time
        self.orderbook_moments = orderbook_moments
        self.time_log = time_log
        self.submitted_orders = submitted_orders
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

            #self.orderbook_moments[self.exchange.orderbook.time] = copy.deepcopy(self.exchange.orderbook)

    def trading_run(self):

        self.order_id_list = list(self.messages.messages.OrderID)

        for i in np.array(self.messages.trade_period_messages):

            order = self.exchange.agents["Ex1"].generate_order(i)

            self.exchange.order_evaluation(order)

            self.exchange.orderbook.time = order.Time

            self.time_log.append(self.exchange.orderbook.time)

            # self.orderbook_moments[self.exchange.orderbook.time] = copy.deepcopy(self.exchange.orderbook)

            self.order_generation()

            self.historical_midprice.append(self.exchange.orderbook.midprice)

            self.time_log.append(self.exchange.orderbook.time)


    def order_generation(self):

        #the list agents is shuffled to give priority decision randomly to the agents

        agent_name_list = list(self.exchange.agents.keys())

        random.shuffle(agent_name_list)

        for i in agent_name_list:

            if (i != "Ex1") and (self.exchange.agents[i].get_action(self.exchange.orderbook)):

                order_to_submit = self.exchange.agents[i].generate_order(self.exchange.orderbook)

                order_to_submit.OrderId = max(self.order_id_list) + 1

                self.submitted_orders.append(order_to_submit)

                self.order_id_list.append(order_to_submit.OrderId)

                price_impact_before = self.exchange.orderbook.midprice

                self.exchange.order_evaluation(order_to_submit)

                price_impact_after = self.exchange.orderbook.midprice

                #self.orderbook_moments[self.exchange.orderbook.time] = copy.deepcopy(self.exchange.orderbook)

                self.exchange.agents[i].my_price_impact.append(price_impact_after-price_impact_before)

                if order_to_submit in self.exchange.executed_orders:
                    self.exchange.agents[i].clear_order(order_to_submit)

            self.exchange.agents[i].historical_balance.append(self.exchange.agents[i].current_balance)



