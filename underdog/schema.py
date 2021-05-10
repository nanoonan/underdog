import enum

class Timespan(enum.Enum):
    Unspecified = 0
    Second = 1
    Minute = 2
    Hour = 3
    Day = 4
    Week = 5
    Month = 6
    Year = 7

class TradingSegment(enum.Enum):
    Unspecified = 0
    PreMarket = 1
    RegularHours = 2
    ExtendedHours = 3
    Closed = 4
