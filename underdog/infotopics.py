import logging
import textwrap

from typing import Optional

import pandas as pd

from tabulate import tabulate

content = {}

content['classes'] = [
('Type', 'Description'),
('[Market, Day, IntraDay]', """
The historic data classes implement a Dict-like interface to access historic stock data. Valid keys are dates, integers, or strings
containing dates in 'YYYY-MM-DD' format. Slices are also supported. Assuming x is an instance of Market, Day, or IntraDay, here are some examples: x['2020-01-01'],
x['2020-01-01':'2021-01-01'], x[-252:] (returns last 252 trading days of data). Data is returned in a Panda DataFrame and downloaded
and kept up to date automatically.
"""),
('Market()', """
The Market class contains 2 years of daily data for all tickers traded. Market data comes from Polygon which limits
API calls to five a minute. Two years of data takes over an hour to download. The Market class has a special update()
method that updates the data when invoked. When data is less than five days out of date, the class automatically fetches the new data.
However, when the data is more than five days out of date you need to manually invoke the update method.
"""),
('Day(symbol)', """
The Day class contains 20 years of daily data for a specific ticker.
"""),
('IntraDay(symbol, period)', """
The IntraDay class contains intraday data for a specific ticker. The data includes pre and post market trades. You can pass a period
argument to the IntraDay constructor to specify either 1, 5, or 30 minute data. The number of days of data depends on the period.
For example, 30 days of 1 minute data are available (90 days of 5 minute data and one year of 30 minute data).
""")
]

content['functions'] = [
('Function', 'Description'),
('intraday(symbol)', """
Returns current intraday one-minute data for the specified ticker.
"""),
('tickers(update = False)', """
Returns table of all tickers. Set update to True when calling for the first time or to download the latest data.
"""),
('ticker_details(symbol)', """
Returns info about a ticker like market cap, institutional ownership ratio, etc...
"""),
('ticker_news(symbol)', """
Returns list of news items about the specified ticker.
"""),
('quote(symbol)', """
Returns current quote for ticker.
"""),
('option_chain(symbol)', """
Returns current option chain for ticker. This is current, not historic, data.
"""),
('trading_daterange(start, end)', """
Iterator that produces trading dates between specified start and end dates.
"""),
('nth_previous_trading_date(n, anchor)', """
Nth prior trading date from anchor.
"""),
('nth_next_trading_date(n, anchor)', """
Nth future trading date from anchor.
"""),
('trading_days_between(start, end)', """
Number of trading days between start and end.
"""),
('is_trading_date(when)', """
Is specified date a trading day?
"""),
('market_open()', """
Is the market currently open?
""")
]

content['environment'] = [
('Environment Variable', 'Description'),
('POLYGON_API_KEY', """
The API key from your Polygon account.
"""),
('TDA_TOKEN_PATH', """
Path to file where TDA auth token is stored.
"""),
('TDA_API_KEY' , """
The API key from your TDA developer account.
"""),
('TDA_REDIRECT_URI' , """
In most cases this will be https://localhost.
"""),
('TDA_ACCOUNT_ID' , """
Account id for your TDA trading account.
""")
]

logger = logging.getLogger(__name__)

def info(
    topic: Optional[str] = None,
    style: Optional[str] = 'fancy_grid',
    return_df: bool = False
):
    if not topic:
        print('info(topic: str) -> useful information')
        print('Valid info topics: environment, classes, functions')
        return None
    if topic not in content:
        print('{0} is not a valid info topic'.format(topic))
        return None
    rows = []
    headers = list(content[topic][0])
    for i in range(1, len(content[topic])):
        item = {}
        item[content[topic][0][0]] = content[topic][i][0]
        item[content[topic][0][1]] = '\n'.join(textwrap.wrap(content[topic][i][1]))
        rows.append(item)
    df = pd.DataFrame(rows)
    if style:
        print(tabulate(df, showindex = False, headers = headers, tablefmt = style))
    return df if return_df else None
