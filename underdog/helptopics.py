import logging
import textwrap

from typing import Optional

import pandas as pd

from IPython.display import (
    display,
    HTML,
    Image,
    Markdown
)
from tabulate import tabulate

content = {}

content['classes'] = [
('Type', 'Description'),
('[Market, Day, IntraDay]', """
The historic data classes implement a Dict-like interface to access historic stock data. Valid keys are dates, integers, or strings
containing dates in 'YYYY-MM-DD' format. Slices are also supported. Assuming x is an instance, here are some examples: x['2020-01-01'],
x['2020-01-01':'2021-01-01'], x[-252:] (returns last 252 trading days of data). Data is returned in a Panda table.
"""),
('Market', """
The Market class contains 2 years of daily data for all tickers traded.
"""),
('Day', """
The Day class contains 20 years of daily data for a specific ticker.
"""),
('IntraDay', """
The IntraDay class contains about two months of one-minute intraday data for a specific tickers. Includes pre and post market trades.
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

def help(
    topic: Optional[str] = None,
    format: Optional[str] = 'fancy_grid',
    return_df: bool = False
):
    if not topic:
        print('help(topic: str) -> useful information')
        print('Valid help topics: environment, classes, functions')
        return
    if topic not in content:
        print('{0} is not a valid help topic'.format(topic))
        return
    rows = []
    headers = list(content[topic][0])
    for i in range(1, len(content[topic])):
        item = {}
        item[content[topic][0][0]] = content[topic][i][0]
        item[content[topic][0][1]] = '\n'.join(textwrap.wrap(content[topic][i][1]))
        rows.append(item)
    df = pd.DataFrame(rows)
    if format:
        print(tabulate(df, showindex = False, headers = headers, tablefmt = format))
    return df if return_df else None
