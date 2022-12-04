from models import Order
@dataclass
class HistoricalOrderBook:
       ticker: int
       path: str
       eventType = {1: "New Order Submission", 2: "Cancellation",
                          3: "Deletion", 4: "Visible Order Execution", 5: "Hidden Order Execution",
                          6: "Cross Trade", 7: "Trading Halt"}

    def add_order(self, order: Order):


    def get_snapshot(self, start_time, end_time):
        start = start_time.timestamp() - (self.date - datetime.fromtimestamp(0.0)).total_seconds() + 3600
        end = end_time.timestamp() - (self.date - datetime.fromtimestamp(0.0)).total_seconds() + 3600
        sliced_book = self.messages[(self.messages.Time >= start) & (self.messages.Time <= end)]
        return sliced_book

    def snapshot_descriptives(self, start_time, end_time):
        start = start_time.timestamp() - (self.date - datetime.fromtimestamp(0.0)).total_seconds() + 3600
        end = end_time.timestamp() - (self.date - datetime.fromtimestamp(0.0)).total_seconds() + 3600
        sliced_book = self.messages[(self.messages.Time >= start) & (self.messages.Time <= end)]
        descriptives = sliced_book.describe(include='all')
        means = sliced_book.groupby(['Direction', "EventType"])[["Size", "Price"]].mean()
        means.rename(index=self.eventType, level=1, inplace=True)
        counts = sliced_book.groupby(['Direction', "EventType"])[["Size"]].count()
        counts.rename(index=self.eventType, level=1, inplace=True)
        return descriptives, means, counts