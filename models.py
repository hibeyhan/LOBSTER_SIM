# This is a sample Python script.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
from sortedcontainers import SortedDict
import datetime as dt
import datetime as dt
from collections import deque
from dataclasses import dataclass

@dataclass
class Order():
     def __init__(
        self,
        time:float,
        EventType:int,
        OrderId:int,
        Size:int,
        Price:int,
        Direction:int,
        SenderID=None
     ):
        self.Time = Time
        self.EventType = EventType
        self.OrderId = OrderId
        self.Size = Size
        self.Price = Price
        self.Direction = Direction
        self.SenderID = SenderID

