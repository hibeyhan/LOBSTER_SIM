import pandas as pd
import datetime as dt
from models import Order

class Simulator:

    def __init__(
            self,
            ticker: str = None,
            directory: str = None,
            date=None,
            start: dt.datetime = None,
            end: dt.datetime = None,
            exchange=Exchange(),
            historical_midprice=[],
            time=None,
            time_log=[]

    ):
        self.ticker = ticker
        self.directory = directory
        self.date = date
        self.start = start
        self.end = end
        self.exchange = exchange
        self.historical_midprice = historical_midprice
        self.time = time
        self.time_log = time_log

    def initilize_market(self):

        # Agents are added

        self.exchange.agents.append(ImbalanceAgent("IMB1", 1000, 27322000000, self.exchange, [], pd.DataFrame(), []))
        # 'name', 'assets', 'cash', 'exchange', 'executed_orders', 'messages', and 'historical_balance'
        # load messages from real data

        self.load_messages()

        initial_period_messages = self.data.messages[(self.data.messages.Time >
                                                      dt.datetime.strptime(self.start, '%Y-%m-%d %H:%M').timestamp())
                                                     & (self.data.messages.Time < (
                    dt.datetime.strptime(self.start, '%Y-%m-%d %H:%M').timestamp() + 900))]

        for i in range(initial_period_messages.shape[0]):
            time = initial_period_messages.iloc[i, 0]
            event = initial_period_messages.iloc[i, 1]
            orderID = initial_period_messages.iloc[i, 2]
            size = initial_period_messages.iloc[i, 3]
            price = initial_period_messages.iloc[i, 4]
            direction = initial_period_messages.iloc[i, 5]
            agentid = initial_period_messages.iloc[i, 6]

            order = Order(time, event, orderID, size, price, direction, agentid)

            self.exchange.order_evaluation(order)

            self.exchange.orderbook.time = time

            self.time_log.append(self.exchange.orderbook.time)

    def trading_run(self):
        self.order_id_list = list(self.data.messages.OrderID)
        before = []
        after = []
        trade_period_messages = self.data.messages[
            (self.data.messages.Time >= dt.datetime.strptime(self.start, '%Y-%m-%d %H:%M').timestamp() + 900)]

        for i in range(trade_period_messages.shape[0]):

            time = trade_period_messages.iloc[i, 0]
            event = trade_period_messages.iloc[i, 1]
            orderID = trade_period_messages.iloc[i, 2]
            size = trade_period_messages.iloc[i, 3]
            price = trade_period_messages.iloc[i, 4]
            direction = trade_period_messages.iloc[i, 5]
            agentid = trade_period_messages.iloc[i, 6]

            order = Order(time, event, orderID, size, price, direction, agentid)

            self.exchange.order_evaluation(order)

            if self.exchange.orderbook.time % 60 <= 1:

                if self.exchange.agents[0].get_action(self.exchange.orderbook):

                    order_to_submit = self.exchange.agents[0].generate_order(self.exchange.orderbook)

                    try:
                        order_to_submit.OrderId = max(self.order_id_list) + 1

                        self.order_id_list.append(order_to_submit.OrderId)

                        # measure price impact

                        before.append(self.exchange.orderbook.midprice)

                        self.exchange.order_evaluation(order_to_submit)

                        after.append(self.exchange.orderbook.midprice)

                        if order_to_submit in self.exchange.executed_orders:
                            self.exchange.agents[0].clear_order(order_to_submit)

                    except:

                        print(order_to_submit)

            self.exchange.agents[0].historical_balance.append(self.exchange.agents[0].current_balance(order))

            self.historical_midprice.append(self.exchange.orderbook.midprice)

            self.exchange.orderbook.time = time

            self.time_log.append(self.exchange.orderbook.time)

        self.price_impact = pd.DataFrame({"before": before, "after": after})

    def load_messages(self):

        self.data = DataRetriever(self.ticker, self.directory, self.date)

        self.data.get_messages()

    def get_lob_moment(self):

        return self.exchange.orderbook.get_snapshot(level=50)

    def generate_orders(start, end, messages):

        message_list = messages[(messages.Time > dt.datetime.strptime(start, '%Y-%m-%d %H:%M').timestamp())
                                & (messages.Time < dt.datetime.strptime(end, '%Y-%m-%d %H:%M').timestamp())]

        Orders = []

        for i in range(message_list.shape[0]):
            time = message_list.iloc[i, 0]
            event = message_list.iloc[i, 1]
            orderID = message_list.iloc[i, 2]
            size = message_list.iloc[i, 3]
            price = message_list.iloc[i, 4]
            direction = message_list.iloc[i, 5]
            agentid = message_list.iloc[i, 6]
            Orders.append(Order(time, event, orderID, size, price, direction, agentid))

        return Orders
