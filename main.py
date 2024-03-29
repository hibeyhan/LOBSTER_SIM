import datetime as dt
from exchange import Exchange
from agent import ExchangeAgent
from agent import ImbalanceAgent
from agent import BollingerAgent
from agent import RandomForest
from agent import Regression
from agent import RandomAgent
import numpy as np
import pandas as pd
from dataretriever import DataRetriever
from models import Order
import random
import copy
import math


#this is a class to run the market
class Simulator:

    def __init__(
            self,
            ticker: str = None,
            directory: str = None, #this is where LOBSTER Messages file is stored
            date=None,
            exchange=Exchange(),
            messages=None,
            historical_midprice= [[],[]],
            time=None,
            orderbook_moments={},
            time_log=[],
            submitted_orders=[],
            agent_trade_freq= 10,
            order_id_list=[],
            df_for_ml = {"Time":[], "Midprice":[], "Spread":[], "imbalance1":[], "imbalance2":[], "imbalance3":[],
                         "imbalance4":[], "imbalance5":[],  "imbalance10":[],
                         "imbalance20":[]}

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
        self.agent_trade_freq = agent_trade_freq
        self.order_id_list = order_id_list
        self.df_for_ml = df_for_ml


    #a function that initialize market, adds agents, endows initial wealth
    def initialize_market(self):
        #create a data retriever class
        self.messages = DataRetriever(ticker=self.ticker, directory=self.directory, trade_date=self.date)

        #a function that retrieves messages
        self.messages.get_messages()

        #adding desired agents to the market
        #this ImbalanceAgent who take action on imbalance in limit order book
        order_size = 10
        self.exchange.agents["Rand"] = RandomAgent(assets=1000, cash=1000*self.messages.messages.Price[1],
                                                      exchange=self.exchange, sent_orders=[], executed_orders=[],
                                                      historical_balance=[[],[]],  my_price_impact=[[],[]],
                                                      trade_freq= self.agent_trade_freq,order_size=order_size, model=[],
                                                      data=None)

        self.exchange.agents["Imb1"] = ImbalanceAgent(assets=1000, cash=1000*self.messages.messages.Price[1],
                                                      exchange=self.exchange, sent_orders=[], executed_orders=[],
                                                      historical_balance=[[],[]],  my_price_impact=[[],[]],
                                                      trade_freq= self.agent_trade_freq, order_size=order_size,model=[],
                                                      data=None)

        #this is exchange agent who posts historical LOBSTER orders
        self.exchange.agents["Ex1"] = ExchangeAgent(assets=1000, cash=1000*self.messages.messages.Price[1],
                                                    exchange=self.exchange, sent_orders=[], executed_orders=[],
                                                    historical_balance=[[],[]], my_price_impact=[[],[]],
                                                    trade_freq= self.agent_trade_freq, order_size=order_size,model=[],
                                                    data = None)

        #This BollingerAgent who take action on Bollinger Bands
        self.exchange.agents["Bol1"] = BollingerAgent(assets=1000, cash=1000*self.messages.messages.Price[1],
                                                      exchange=self.exchange, sent_orders=[], executed_orders=[],
                                                      historical_balance=[[],[]], my_price_impact=[[],[]],
                                                      trade_freq= self.agent_trade_freq,order_size=order_size,model=[],
                                                      data=None)


        self.exchange.agents["RF1"] = RandomForest(assets=1000, cash=1000 * self.messages.messages.Price[1],
                                                   exchange=self.exchange, sent_orders=[], executed_orders=[],
                                                   historical_balance=[[], []], my_price_impact = [[],[]],order_size=order_size,
                                                   trade_freq= self.agent_trade_freq,
                                                   model=None, data=None)

        self.exchange.agents["Reg1"] = Regression(assets=1000, cash=1000*self.messages.messages.Price[1],
                                                  exchange=self.exchange, sent_orders=[], executed_orders=[],
                                                  historical_balance=[[],[]],  my_price_impact=[[],[]],
                                                  trade_freq= self.agent_trade_freq,order_size=order_size,model=[],
                                                  data=None)


        #this loop takes a specified period for messages and ExchangeAgent feed them into the exchange, other agents do not take action at this step

        for i in np.array(self.messages.initializing_period_messages):
            #this is to section that keep records of second data
            order = self.exchange.agents["Ex1"].generate_order(i)

            self.exchange.order_evaluation(order)

            self.exchange.orderbook.time = order.Time

            self.exchange.time_log.append(self.exchange.orderbook.time)

            self.exchange.store_timeseries_data(order)

            self.historical_midprice[0].append(self.exchange.orderbook.time)

            self.historical_midprice[1].append(self.exchange.orderbook.midprice)


        for i in np.array(self.messages.train_period_messages):
            #this is to section that keep records of second data
            order = self.exchange.agents["Ex1"].generate_order(i)

            self.exchange.order_evaluation(order)

            self.exchange.orderbook.time = order.Time

            self.exchange.time_log.append(self.exchange.orderbook.time)

            self.exchange.store_timeseries_data(order)

            self.historical_midprice[0].append(self.exchange.orderbook.time)

            self.historical_midprice[1].append(self.exchange.orderbook.midprice)

            # saves moments of orderbook but it increase running time

            self.df_for_ml["Time"].append(self.exchange.orderbook.time)
            self.df_for_ml["Midprice"].append(self.exchange.orderbook.midprice)
            self.df_for_ml["Spread"].append(self.exchange.orderbook.spread)
            self.df_for_ml["imbalance1"].append(self.exchange.orderbook.imbalance_at_best_prices)
            self.df_for_ml["imbalance2"].append(self.exchange.orderbook.imbalance_at_best_n(2))
            self.df_for_ml["imbalance3"].append(self.exchange.orderbook.imbalance_at_best_n(3))
            self.df_for_ml["imbalance4"].append(self.exchange.orderbook.imbalance_at_best_n(4))
            self.df_for_ml["imbalance5"].append(self.exchange.orderbook.imbalance_at_best_n(5))
            self.df_for_ml["imbalance10"].append(self.exchange.orderbook.imbalance_at_best_n(10))
            self.df_for_ml["imbalance20"].append(self.exchange.orderbook.imbalance_at_best_n(20))

        df1 = pd.DataFrame(self.df_for_ml)
        df1["Time"] = df1["Time"].apply(lambda x: np.floor(x / self.agent_trade_freq))
        df1 = df1.groupby(['Time'], as_index=False).mean()
        self.exchange.agents["RF1"].data = df1.copy()
        self.exchange.agents["Reg1"].data = df1.copy()
        self.exchange.agents["Imb1"].data = df1[["imbalance3", "imbalance10"]].copy()
        self.exchange.agents["Bol1"].data = df1["Midprice"].copy()
        self.exchange.agents["RF1"].train_my_model()
        self.exchange.agents["Reg1"].train_my_model()

    #this step is trading period, all agents come into the market and post orders
    def trading_run(self):

        self.order_id_list = list(self.messages.messages.OrderID)

        for i in np.array(self.messages.trade_period_messages):

            order = self.exchange.agents["Ex1"].generate_order(i)

            self.exchange.order_evaluation(order)

            self.exchange.orderbook.time = order.Time

            self.exchange.time_log.append(self.exchange.orderbook.time)

            # saves moments of orderbook but it increase running time
            #if (len(self.exchange.time_log) > 1) and (math.floor(self.exchange.orderbook.time) != math.floor(self.exchange.time_log[-2])):
            #    self.orderbook_moments[math.floor(self.exchange.orderbook.time)-1654669800] = copy.deepcopy(self.exchange.orderbook)

            self.order_generation()

            self.exchange.store_timeseries_data(order)

            self.historical_midprice[0].append(self.exchange.orderbook.time)

            self.historical_midprice[1].append(self.exchange.orderbook.midprice)

            for j in list(self.exchange.agents.keys()):
                self.exchange.agents[j].balance_at_each_moment[0].append(self.exchange.orderbook.time)
                self.exchange.agents[j].balance_at_each_moment[1].append(self.exchange.agents[j].current_balance)


            #self.exchange.time_log.append(self.exchange.orderbook.time)

            # saves moments of orderbook but it increase running time
            #if (len(self.exchange.time_log) > 1) and (math.floor(self.exchange.orderbook.time) != math.floor(self.exchange.time_log[-2])):
            #    self.orderbook_moments[math.floor(self.exchange.orderbook.time)-1654669800] = copy.deepcopy(self.exchange.orderbook)

            self.exchange.agents["Ex1"].historical_balance[0].append(self.exchange.orderbook.time)

            self.exchange.agents["Ex1"].historical_balance[1].append(self.exchange.agents["Ex1"].current_balance)

            self.df_for_ml["Time"].append(self.exchange.orderbook.time)
            self.df_for_ml["Midprice"].append(self.exchange.orderbook.midprice)
            self.df_for_ml["Spread"].append(self.exchange.orderbook.spread)
            self.df_for_ml["imbalance1"].append(self.exchange.orderbook.imbalance_at_best_prices)
            self.df_for_ml["imbalance2"].append(self.exchange.orderbook.imbalance_at_best_n(2))
            self.df_for_ml["imbalance3"].append(self.exchange.orderbook.imbalance_at_best_n(3))
            self.df_for_ml["imbalance4"].append(self.exchange.orderbook.imbalance_at_best_n(4))
            self.df_for_ml["imbalance5"].append(self.exchange.orderbook.imbalance_at_best_n(5))
            self.df_for_ml["imbalance10"].append(self.exchange.orderbook.imbalance_at_best_n(10))
            self.df_for_ml["imbalance20"].append(self.exchange.orderbook.imbalance_at_best_n(20))

            if (math.floor(self.exchange.orderbook.time) != math.floor(self.exchange.time_log[-2]))\
                    & (math.floor(self.exchange.orderbook.time) % self.agent_trade_freq == 0):
                df1 = pd.DataFrame(self.df_for_ml).iloc[:-2]
                df1["Time"] = df1["Time"].apply(lambda x: np.floor(x/self.agent_trade_freq ))
                df1 = df1.groupby(['Time'], as_index=False).mean()
                self.exchange.agents["RF1"].data = df1.copy()
                self.exchange.agents["Reg1"].data = df1.copy()
                self.exchange.agents["Imb1"].data = df1[["imbalance3", "imbalance10"]].copy()
                self.exchange.agents["Bol1"].data = df1["Midprice"].copy()

            print(dt.datetime.fromtimestamp(order.Time).time())

    #this is process that arrange priority of posting orders among agents that all is pseudo-random

    def order_generation(self):

        #the list agents is shuffled to give priority decision randomly to the agents

        agent_name_list = list(self.exchange.agents.keys())

        random.shuffle(agent_name_list)

        for i in agent_name_list:

            if (i != "Ex1") and (self.exchange.agents[i].get_action(self.exchange.orderbook)):

                order_to_submit = self.exchange.agents[i].generate_order(self.exchange.orderbook)

                order_to_submit.OrderId = max(self.order_id_list) + 1

                order_to_submit.Time = order_to_submit.Time + 0.0000001

                self.submitted_orders.append(order_to_submit)

                self.order_id_list.append(order_to_submit.OrderId)


                price_impact_before = self.exchange.orderbook.midprice

                self.exchange.order_evaluation(order_to_submit)

                price_impact_after = self.exchange.orderbook.midprice

                #self.exchange.time_log.append(self.exchange.orderbook.time)

                #self.orderbook_moments[self.exchange.orderbook.time] = copy.deepcopy(self.exchange.orderbook)

                self.exchange.agents[i].my_price_impact[0].append(order_to_submit.Time)

                self.exchange.agents[i].my_price_impact[1].append((price_impact_after-price_impact_before))

                if order_to_submit in self.exchange.executed_orders:

                    self.exchange.agents[i].clear_order(order_to_submit)

                    self.exchange.agents[i].historical_balance[0].append(self.exchange.orderbook.time)

                    self.exchange.agents[i].historical_balance[1].append(self.exchange.agents[i].current_balance)


    #this is function summarize descriptives of stock price

    def price_descriptives(self):

        historical_mid_price = pd.DataFrame({"Date": self.historical_midprice[0],
                                             "Simulation Mid Price": self.historical_midprice[1]})

        real_data = self.messages.messages[self.messages.messages.EventType == 4]

        real_time_trade_price = pd.DataFrame({"Date": real_data.Time, "Real Market Mid Price": real_data.Price})

        return historical_mid_price.describe(), real_time_trade_price.describe()

    #this is used if LSTM trader is trading, could be better organized
    @staticmethod
    def get_data_and_train(midprice):
        df = pd.DataFrame({"midprice": midprice})
        dataset=df.values
        dataX, dataY = [], []

        def create_dataset(dataset1, look_back1=30):
            for i in range(len(dataset1)-look_back1-1):
                a = dataset1[i:(i+look_back1), 0]
                dataX.append(a)
                dataY.append(dataset1[i + look_back1, 0])

            return np.array(dataX), np.array(dataY)

        # fix random seed for reproducibility
        tf.random.set_seed(7)

        # load the dataset
        dataset = dataset.astype('float32')

        # normalize the dataset
        scaler = MinMaxScaler(feature_range=(0, 1))
        dataset = scaler.fit_transform(dataset)

        # split into train and test sets
        train_size = int(len(dataset) * 0.67)
        test_size = len(dataset) - train_size
        train, test = dataset[0:train_size,:], dataset[train_size:len(dataset),:]

        # reshape into X=t and Y=t+1
        look_back = 30
        trainX, trainY = create_dataset(train, look_back)
        testX, testY = create_dataset(test, look_back)

        # reshape input to be [samples, time steps, features]
        trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
        testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))


        # create and fit the LSTM network
        model = Sequential()
        model.add(LSTM(4, input_shape=(trainX.shape[0], 30)))
        model.add(Dense(1))
        model.compile(loss='mean_squared_error', optimizer='adam')

        model.fit(trainX, trainY, epochs=5, batch_size=10, verbose=1)

        return model




