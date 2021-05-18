```python
from underdog import info
```

## Overview
**Status**: Development

**Tested**: Windows only

**Requires**: Python 3.8+

The *underdog* package provides Python classes and functions to easily access free equity-related data via Panda DataFrames. Data is automatically downloaded, kept up to date, and cached on disk for convenience and to improve performance and limit API requests to the data providers (which often rate limit the APIs). Currently, data is pulled from [Polygon](https://polygon.io), [finviz](https://finviz.com), and [TD Ameritrade](https://www.tdameritrade.com/home.html).

Real-time streams of time and sales, level one quotes, and one minute candle data are also supported. The data streams are written to a persistent log and the data can be accessed from multiple processes.

The package is basically a convience wrapper over the underlying data services and the excellent [tda-api](https://tda-api.readthedocs.io/en/latest/index.html) package.

Feel free to send questions, comments or feedback to: nanoonan at marvinsmind dot com.

## Installation

1. Install [parkit](https://github.com/nanoonan/parkit), which provides the storage layer.

2. Install _underdog_ by opening a command prompt, navigating to the top-level directory of the git installation, and running the following command.

```
python -m pip install .
```

3. You'll need a free account with [Polygon](https://polygon.io) and a developer account with TD Ameritrade. The documentation for [tda-api](https://tda-api.readthedocs.io/en/latest/index.html) has more information on setting up a TDA developer account.

4. Finally, set up the environment variables used to access data from your accounts. The next cell describes these variables.


```python
info('environment')
```

    ╒════════════════════════╤═══════════════════════════════════════════════╕
    │ Environment Variable   │ Description                                   │
    ╞════════════════════════╪═══════════════════════════════════════════════╡
    │ POLYGON_API_KEY        │ The API key from your Polygon account.        │
    ├────────────────────────┼───────────────────────────────────────────────┤
    │ TDA_TOKEN_PATH         │ Path to file where TDA auth token is stored.  │
    ├────────────────────────┼───────────────────────────────────────────────┤
    │ TDA_API_KEY            │ The API key from your TDA developer account.  │
    ├────────────────────────┼───────────────────────────────────────────────┤
    │ TDA_REDIRECT_URI       │ In most cases this will be https://localhost. │
    ├────────────────────────┼───────────────────────────────────────────────┤
    │ TDA_ACCOUNT_ID         │ Account id for your TDA trading account.      │
    ╘════════════════════════╧═══════════════════════════════════════════════╛


## API


```python
# The main classes for accessing historic data
info('classes')
```

    ╒══════════════════════════╤════════════════════════════════════════════════════════════════════════╕
    │ Type                     │ Description                                                            │
    ╞══════════════════════════╪════════════════════════════════════════════════════════════════════════╡
    │ [Market, Day, IntraDay]  │ The historic data classes implement a Dict-like interface to access    │
    │                          │ historic stock data. Valid keys are dates, integers, or strings        │
    │                          │ containing dates in 'YYYY-MM-DD' format. Slices are also supported.    │
    │                          │ Assuming x is an instance of Market, Day, or IntraDay, here are some   │
    │                          │ examples: x['2020-01-01'], x['2020-01-01':'2021-01-01'], x[-252:]      │
    │                          │ (returns last 252 trading days of data). Data is returned in a Panda   │
    │                          │ DataFrame and downloaded and kept up to date automatically.            │
    ├──────────────────────────┼────────────────────────────────────────────────────────────────────────┤
    │ Market()                 │ The Market class contains 2 years of daily data for all tickers        │
    │                          │ traded. Market data comes from Polygon which limits API calls to five  │
    │                          │ a minute. Two years of data takes over an hour to download. The Market │
    │                          │ class has a special update() method that updates the data when         │
    │                          │ invoked. When data is less than five days out of date, the class       │
    │                          │ automatically fetches the new data. However, when the data is more     │
    │                          │ than five days out of date you need to manually invoke the update      │
    │                          │ method.                                                                │
    ├──────────────────────────┼────────────────────────────────────────────────────────────────────────┤
    │ Day(symbol)              │ The Day class contains 20 years of daily data for a specific ticker.   │
    ├──────────────────────────┼────────────────────────────────────────────────────────────────────────┤
    │ IntraDay(symbol, period) │ The IntraDay class contains intraday data for a specific ticker. The   │
    │                          │ data includes pre and post market trades. You can pass a period        │
    │                          │ argument to the IntraDay constructor. Data will be resampled to match  │
    │                          │ the request period in minutes. The default period is one minute.       │
    ╘══════════════════════════╧════════════════════════════════════════════════════════════════════════╛



```python
info('functions')
```

    ╒══════════════════════════════════════╤═══════════════════════════════════════════════════════════════════════╕
    │ Function                             │ Description                                                           │
    ╞══════════════════════════════════════╪═══════════════════════════════════════════════════════════════════════╡
    │ intraday(symbol)                     │ Returns current intraday one-minute data for the specified ticker.    │
    ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ tickers(update = False)              │ Returns table of all tickers. Set update to True when calling for the │
    │                                      │ first time or to download the latest data.                            │
    ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ ticker_details(symbol)               │ Returns info about a ticker like market cap, institutional ownership  │
    │                                      │ ratio, etc...                                                         │
    ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ ticker_news(symbol)                  │ Returns list of news items about the specified ticker.                │
    ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ quote(symbol)                        │ Returns current quote for ticker.                                     │
    ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ option_chain(symbol)                 │ Returns current option chain for ticker. This is current, not         │
    │                                      │ historic, data.                                                       │
    ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ trading_daterange(start, end)        │ Iterator that produces trading dates between specified start and end  │
    │                                      │ dates.                                                                │
    ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ nth_previous_trading_date(n, anchor) │ Nth prior trading date from anchor.                                   │
    ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ nth_next_trading_date(n, anchor)     │ Nth future trading date from anchor.                                  │
    ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ trading_days_between(start, end)     │ Number of trading days between start and end.                         │
    ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ is_trading_date(when)                │ Is specified date a trading day?                                      │
    ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ market_open()                        │ Is the market currently open?                                         │
    ╘══════════════════════════════════════╧═══════════════════════════════════════════════════════════════════════╛


## Examples


```python
from underdog import Market
market = Market()
# Invoke this once to download 2 years of data...will take over an hour
market.update()
```




    True




```python
# Get a dataframe of last two years of daily data for all tickers
market[:]
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>symbol</th>
      <th>volume</th>
      <th>vwap</th>
      <th>open</th>
      <th>close</th>
      <th>high</th>
      <th>low</th>
      <th>date</th>
      <th>twap</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>A</td>
      <td>1609122</td>
      <td>77.1685</td>
      <td>76.9800</td>
      <td>77.4200</td>
      <td>77.4600</td>
      <td>76.3000</td>
      <td>2019-04-26</td>
      <td>76.86806</td>
    </tr>
    <tr>
      <th>1</th>
      <td>AA</td>
      <td>2257704</td>
      <td>26.9973</td>
      <td>27.0500</td>
      <td>26.9100</td>
      <td>27.2500</td>
      <td>26.8400</td>
      <td>2019-04-26</td>
      <td>27.046952</td>
    </tr>
    <tr>
      <th>2</th>
      <td>AAAU</td>
      <td>30402</td>
      <td>12.8574</td>
      <td>12.8200</td>
      <td>12.8450</td>
      <td>12.8700</td>
      <td>12.8200</td>
      <td>2019-04-26</td>
      <td>12.845833</td>
    </tr>
    <tr>
      <th>3</th>
      <td>AABA</td>
      <td>3279169</td>
      <td>76.1562</td>
      <td>76.4400</td>
      <td>76.1200</td>
      <td>76.6800</td>
      <td>75.5300</td>
      <td>2019-04-26</td>
      <td>76.101546</td>
    </tr>
    <tr>
      <th>4</th>
      <td>AAC</td>
      <td>85690</td>
      <td>1.5970</td>
      <td>1.5900</td>
      <td>1.6400</td>
      <td>1.6600</td>
      <td>1.5250</td>
      <td>2019-04-26</td>
      <td>1.591701</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>4573296</th>
      <td>RBIN</td>
      <td>1</td>
      <td>27.6500</td>
      <td>27.7602</td>
      <td>27.7602</td>
      <td>27.7602</td>
      <td>27.7602</td>
      <td>2021-05-14</td>
      <td>RBIN</td>
    </tr>
    <tr>
      <th>4573297</th>
      <td>QPT</td>
      <td>10</td>
      <td>24.1599</td>
      <td>24.2188</td>
      <td>24.2188</td>
      <td>24.2188</td>
      <td>24.2188</td>
      <td>2021-05-14</td>
      <td>QPT</td>
    </tr>
    <tr>
      <th>4573298</th>
      <td>RODI</td>
      <td>100</td>
      <td>115.0628</td>
      <td>116.7316</td>
      <td>116.7316</td>
      <td>116.7316</td>
      <td>116.7316</td>
      <td>2021-05-14</td>
      <td>RODI</td>
    </tr>
    <tr>
      <th>4573299</th>
      <td>PSMR</td>
      <td>344</td>
      <td>21.0786</td>
      <td>21.1585</td>
      <td>21.1585</td>
      <td>21.1585</td>
      <td>21.1585</td>
      <td>2021-05-14</td>
      <td>PSMR</td>
    </tr>
    <tr>
      <th>4573300</th>
      <td>RODE</td>
      <td>101</td>
      <td>28.4830</td>
      <td>28.8299</td>
      <td>28.8299</td>
      <td>28.8299</td>
      <td>28.8299</td>
      <td>2021-05-14</td>
      <td>RODE</td>
    </tr>
  </tbody>
</table>
<p>4573301 rows × 9 columns</p>
</div>




```python
from underdog import ticker_details
# Get useful information about a ticker
ticker_details('TSLA')
```




    {'market_cap': 555680000000,
     'shares_float': 774230000,
     'shares_outstanding': 963330000,
     'insider_ownership': 0.0,
     'institutional_ownership': 0.44,
     'retail_ownership': 0.56,
     'short_float': 0.05,
     'employees': 70757,
     'has_options': True,
     'is_shortable': True}




```python
from underdog import IntraDay
# Last five days of TSLA intraday three minute data
df = IntraDay('TSLA', period = 3)[-5:]
# Filter for only regular hours trading (1 = pre-market, 2 = regular hours, 3 = extended hours)
df[df['trading_segment'] == 2]
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>timestamp</th>
      <th>open</th>
      <th>close</th>
      <th>low</th>
      <th>high</th>
      <th>volume</th>
      <th>twap</th>
      <th>trading_segment</th>
      <th>timeslot</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>71</th>
      <td>2021-05-10 09:30:00-04:00</td>
      <td>664.9000</td>
      <td>660.2812</td>
      <td>659.0100</td>
      <td>665.0500</td>
      <td>416090</td>
      <td>661.934012</td>
      <td>2</td>
      <td>110</td>
    </tr>
    <tr>
      <th>72</th>
      <td>2021-05-10 09:33:00-04:00</td>
      <td>660.1693</td>
      <td>658.0200</td>
      <td>658.0000</td>
      <td>661.3300</td>
      <td>215961</td>
      <td>659.731306</td>
      <td>2</td>
      <td>111</td>
    </tr>
    <tr>
      <th>73</th>
      <td>2021-05-10 09:36:00-04:00</td>
      <td>658.1900</td>
      <td>656.7279</td>
      <td>655.3400</td>
      <td>658.4299</td>
      <td>253527</td>
      <td>656.850914</td>
      <td>2</td>
      <td>112</td>
    </tr>
    <tr>
      <th>74</th>
      <td>2021-05-10 09:39:00-04:00</td>
      <td>656.5568</td>
      <td>655.1838</td>
      <td>653.4100</td>
      <td>656.8100</td>
      <td>287776</td>
      <td>655.077686</td>
      <td>2</td>
      <td>113</td>
    </tr>
    <tr>
      <th>75</th>
      <td>2021-05-10 09:42:00-04:00</td>
      <td>655.0050</td>
      <td>656.0800</td>
      <td>653.1200</td>
      <td>656.8400</td>
      <td>316319</td>
      <td>654.968006</td>
      <td>2</td>
      <td>114</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>1422</th>
      <td>2021-05-14 15:45:00-04:00</td>
      <td>588.0100</td>
      <td>589.8700</td>
      <td>587.8400</td>
      <td>590.3400</td>
      <td>227810</td>
      <td>589.114091</td>
      <td>2</td>
      <td>235</td>
    </tr>
    <tr>
      <th>1423</th>
      <td>2021-05-14 15:48:00-04:00</td>
      <td>589.9169</td>
      <td>589.7850</td>
      <td>588.7513</td>
      <td>589.9599</td>
      <td>145852</td>
      <td>589.354121</td>
      <td>2</td>
      <td>236</td>
    </tr>
    <tr>
      <th>1424</th>
      <td>2021-05-14 15:51:00-04:00</td>
      <td>589.8600</td>
      <td>590.9129</td>
      <td>589.5000</td>
      <td>591.1700</td>
      <td>260416</td>
      <td>590.329323</td>
      <td>2</td>
      <td>237</td>
    </tr>
    <tr>
      <th>1425</th>
      <td>2021-05-14 15:54:00-04:00</td>
      <td>590.8686</td>
      <td>590.0015</td>
      <td>590.0000</td>
      <td>590.9500</td>
      <td>228326</td>
      <td>590.485509</td>
      <td>2</td>
      <td>238</td>
    </tr>
    <tr>
      <th>1426</th>
      <td>2021-05-14 15:57:00-04:00</td>
      <td>590.0100</td>
      <td>589.7200</td>
      <td>589.5000</td>
      <td>590.9600</td>
      <td>328648</td>
      <td>590.233636</td>
      <td>2</td>
      <td>239</td>
    </tr>
  </tbody>
</table>
<p>650 rows × 9 columns</p>
</div>




```python
from underdog import Day
# Last 20 years of daily XOM data
df = Day('XOM')[:]
df
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>open</th>
      <th>high</th>
      <th>low</th>
      <th>close</th>
      <th>volume</th>
      <th>date</th>
      <th>twap</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>44.100</td>
      <td>44.720</td>
      <td>44.050</td>
      <td>44.530</td>
      <td>9779400</td>
      <td>2001-05-14</td>
      <td>44.393036</td>
    </tr>
    <tr>
      <th>1</th>
      <td>44.530</td>
      <td>44.770</td>
      <td>44.325</td>
      <td>44.725</td>
      <td>9016800</td>
      <td>2001-05-15</td>
      <td>44.543466</td>
    </tr>
    <tr>
      <th>2</th>
      <td>44.725</td>
      <td>45.000</td>
      <td>44.520</td>
      <td>44.750</td>
      <td>16337000</td>
      <td>2001-05-16</td>
      <td>44.760015</td>
    </tr>
    <tr>
      <th>3</th>
      <td>44.575</td>
      <td>44.580</td>
      <td>44.135</td>
      <td>44.365</td>
      <td>11597600</td>
      <td>2001-05-17</td>
      <td>44.350867</td>
    </tr>
    <tr>
      <th>4</th>
      <td>44.475</td>
      <td>45.125</td>
      <td>44.400</td>
      <td>45.100</td>
      <td>14289200</td>
      <td>2001-05-18</td>
      <td>44.756795</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>5029</th>
      <td>63.240</td>
      <td>64.020</td>
      <td>62.530</td>
      <td>62.580</td>
      <td>31956561</td>
      <td>2021-05-10</td>
      <td>63.293827</td>
    </tr>
    <tr>
      <th>5030</th>
      <td>61.625</td>
      <td>62.385</td>
      <td>60.385</td>
      <td>60.590</td>
      <td>34563768</td>
      <td>2021-05-11</td>
      <td>61.404912</td>
    </tr>
    <tr>
      <th>5031</th>
      <td>60.010</td>
      <td>61.680</td>
      <td>59.750</td>
      <td>60.040</td>
      <td>34426479</td>
      <td>2021-05-12</td>
      <td>60.715042</td>
    </tr>
    <tr>
      <th>5032</th>
      <td>59.000</td>
      <td>60.450</td>
      <td>58.750</td>
      <td>59.300</td>
      <td>24268233</td>
      <td>2021-05-13</td>
      <td>59.603531</td>
    </tr>
    <tr>
      <th>5033</th>
      <td>59.930</td>
      <td>60.875</td>
      <td>59.930</td>
      <td>60.770</td>
      <td>20735400</td>
      <td>2021-05-14</td>
      <td>60.415423</td>
    </tr>
  </tbody>
</table>
<p>5034 rows × 7 columns</p>
</div>



## Stream Support (Experimental)


```python
from underdog import (
    StreamReader,
    StreamType,
    StreamWriter
)
```


```python
# Define a stream reader to handle each stream event. A reader
# runs as a background thread once started. Note: the reader
# does not need to run in the same process as the writer.
# Multiple readers can read the same stream. Events are represented
# as tuples with event type, symbol, timestamps, and relevant price and size
# info.
class MyReader(StreamReader):

    def on_event(self, event):
        print(event)

reader = MyReader('stockstream')
reader.start()
```


```python
# Start a stream writer for a set of symbols. In this example
# the stream includes time and sales, candle, and level 1 quote events
# for the symbols. The stream writer writes to a persistent
# log identified by the name passed to the constructor. One or
# more stream readers can read the events from multiple processes.
symbols = ['TSLA', 'NIO']
writer = StreamWriter(
    'stockstream', {
        StreamType.Chart: symbols,
        StreamType.Quote: symbols,
        StreamType.Trade: symbols
    },
    realtime = True
)
writer.start()
```

    (2, 1621287113617, 'TSLA', 1621287000000, 573.38, 573.4, 573.49, 573.27, 697)
    (2, 1621287113617, 'NIO', 1621287000000, 33.73, 33.72, 33.73, 33.72, 2701)
    (1, 1621287118654, 'TSLA', 1621287095495, 573.1, 573.29, 1621287117722, 573.1, None)
    (1, 1621287118654, 'NIO', 1621287114614, 33.72, 33.73, 1621287114614, 33.73, 1)
    (1, 1621287123693, 'TSLA', 1621287121682, 573, None, 1621287121681, None, None)
    (1, 1621287123693, 'NIO', 1621287120388, None, None, None, None, None)



```python
# Stop the writer thread.
writer.stop()
```


```python

```
