class Order:

    def __init__(
            self,
            Time: float = None,
            EventType: int = None,
            OrderID: int = None,
            Size: int = None,
            Price: int = None,
            Direction: int =None,
            SenderID: str =None
    ):
        self.Time = Time
        self.EventType = EventType
        self.OrderID = OrderID
        self.Size = Size
        self.Price = Price
        self.Direction = Direction
        self.SenderID = SenderID


    def get_order_attributes(self):

        return [self.Time, self.EventType, self.OrderID, self.Size, self.Price, self.Direction, self.SenderID]



