```python
from underdog import info
```

## Overview
**Status**: Development

**Tested**: Windows only

**Requires**: Python 3.8+

The *underdog* package provides Python classes and functions to easily access free equity-related data through Panda dataframes. Data is cached on disk to improve performance and limit API requests to the data providers (which often rate limit the APIs). Currently, data is pulled from [Polygon](https://polygon.io), [finViz](https://finviz.com), and TD Ameritrade.

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
info()
```

    info(topic: str) -> useful information
    Valid info topics: environment, classes, functions



```python
# The main classes for accessing historic data
info('classes')
```

    ╒═════════════════════════╤════════════════════════════════════════════════════════════════════════╕
    │ Type                    │ Description                                                            │
    ╞═════════════════════════╪════════════════════════════════════════════════════════════════════════╡
    │ [Market, Day, IntraDay] │ The historic data classes implement a Dict-like interface to access    │
    │                         │ historic stock data. Valid keys are dates, integers, or strings        │
    │                         │ containing dates in 'YYYY-MM-DD' format. Slices are also supported.    │
    │                         │ Assuming x is an instance of Market, Day, or IntraDay, here are some   │
    │                         │ examples: x['2020-01-01'], x['2020-01-01':'2021-01-01'], x[-252:]      │
    │                         │ (returns last 252 trading days of data). Data is returned in a Panda   │
    │                         │ dataframe.                                                             │
    ├─────────────────────────┼────────────────────────────────────────────────────────────────────────┤
    │ Market                  │ The Market class contains 2 years of daily data for all tickers        │
    │                         │ traded. Market data comes from Polygon which limits API calls to five  │
    │                         │ a minute. Two years of data takes over an hour to download. The Market │
    │                         │ class has a special update() method that updates the data when called. │
    │                         │ When data is less than five days out of date, the class automatically  │
    │                         │ fetches the new data. However, when the data is more than five days    │
    │                         │ out of date you need to manually invoke the update method.             │
    ├─────────────────────────┼────────────────────────────────────────────────────────────────────────┤
    │ Day                     │ The Day class contains 20 years of daily data for a specific ticker.   │
    ├─────────────────────────┼────────────────────────────────────────────────────────────────────────┤
    │ IntraDay                │ The IntraDay class returns intraday data for a specific ticker. The    │
    │                         │ data includes pre and post market trades. You can pass a period        │
    │                         │ argument to the IntraDay constructor to specify either 1, 5, or 30     │
    │                         │ minute data. The number of days of data depends on the period. For     │
    │                         │ example, 30 days of 1 minute data are available (90 days of 5 minute   │
    │                         │ data and one year of 30 minute data).                                  │
    ╘═════════════════════════╧════════════════════════════════════════════════════════════════════════╛



```python
info('functions')
```

    ╒═════════════════════════╤═══════════════════════════════════════════════════════════════════════╕
    │ Function                │ Description                                                           │
    ╞═════════════════════════╪═══════════════════════════════════════════════════════════════════════╡
    │ intraday(symbol)        │ Returns current intraday one-minute data for the specified ticker.    │
    ├─────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ tickers(update = False) │ Returns table of all tickers. Set update to True when calling for the │
    │                         │ first time or to download the latest data.                            │
    ├─────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ ticker_details(symbol)  │ Returns info about a ticker like market cap, institutional ownership  │
    │                         │ ratio, etc...                                                         │
    ├─────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ ticker_news(symbol)     │ Returns list of news items about the specified ticker.                │
    ├─────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ quote(symbol)           │ Returns current quote for ticker.                                     │
    ╘═════════════════════════╧═══════════════════════════════════════════════════════════════════════╛


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
      <th>4531971</th>
      <td>HOLD</td>
      <td>175</td>
      <td>98.7631</td>
      <td>98.7450</td>
      <td>98.7450</td>
      <td>98.7450</td>
      <td>98.7450</td>
      <td>2021-05-10</td>
      <td>HOLD</td>
    </tr>
    <tr>
      <th>4531972</th>
      <td>HLGE</td>
      <td>13</td>
      <td>26.3054</td>
      <td>25.9974</td>
      <td>25.9974</td>
      <td>25.9974</td>
      <td>25.9974</td>
      <td>2021-05-10</td>
      <td>HLGE</td>
    </tr>
    <tr>
      <th>4531973</th>
      <td>HEWC</td>
      <td>4</td>
      <td>30.8423</td>
      <td>30.6740</td>
      <td>30.6740</td>
      <td>30.6740</td>
      <td>30.6740</td>
      <td>2021-05-10</td>
      <td>HEWC</td>
    </tr>
    <tr>
      <th>4531974</th>
      <td>IBCE</td>
      <td>125</td>
      <td>24.8644</td>
      <td>24.8450</td>
      <td>24.8450</td>
      <td>24.8450</td>
      <td>24.8450</td>
      <td>2021-05-10</td>
      <td>IBCE</td>
    </tr>
    <tr>
      <th>4531975</th>
      <td>JHCS</td>
      <td>40</td>
      <td>38.5053</td>
      <td>38.2801</td>
      <td>38.2801</td>
      <td>38.2801</td>
      <td>38.2801</td>
      <td>2021-05-10</td>
      <td>JHCS</td>
    </tr>
  </tbody>
</table>
<p>4531976 rows × 9 columns</p>
</div>




```python
from underdog import ticker_details
# Get useful information about a ticker
ticker_details('TSLA')
```




    {'market_cap': 647710000000,
     'shares_float': 770380000,
     'shares_outstanding': 963330000,
     'insider_ownership': 0.0,
     'institutional_ownership': 0.46,
     'retail_ownership': 0.54,
     'short_float': 0.07,
     'employees': 70757,
     'has_options': True,
     'is_shortable': True}




```python
from underdog import IntraDay
# Last five days of TSLA intraday five minute data
df = IntraDay('TSLA', period = 5)[-5:]
# Filter for only regular hours trading (1 = pre-market, 2 = regular hours, 3 = extended hours)
df[df['trading_segment'] == 2]
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
      <th>timestamp</th>
      <th>trading_segment</th>
      <th>timeslot</th>
      <th>twap</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>49</th>
      <td>678.8000</td>
      <td>683.4464</td>
      <td>675.8701</td>
      <td>676.9100</td>
      <td>830269</td>
      <td>2021-05-04 09:30:00-04:00</td>
      <td>2</td>
      <td>66</td>
      <td>679.686748</td>
    </tr>
    <tr>
      <th>50</th>
      <td>676.7600</td>
      <td>677.8800</td>
      <td>674.1300</td>
      <td>676.3150</td>
      <td>356577</td>
      <td>2021-05-04 09:35:00-04:00</td>
      <td>2</td>
      <td>67</td>
      <td>676.003119</td>
    </tr>
    <tr>
      <th>51</th>
      <td>676.3850</td>
      <td>678.8000</td>
      <td>674.2981</td>
      <td>676.8550</td>
      <td>433493</td>
      <td>2021-05-04 09:40:00-04:00</td>
      <td>2</td>
      <td>68</td>
      <td>676.548856</td>
    </tr>
    <tr>
      <th>52</th>
      <td>676.9050</td>
      <td>676.9999</td>
      <td>667.8985</td>
      <td>669.8200</td>
      <td>503220</td>
      <td>2021-05-04 09:45:00-04:00</td>
      <td>2</td>
      <td>69</td>
      <td>672.286134</td>
    </tr>
    <tr>
      <th>53</th>
      <td>669.8200</td>
      <td>671.9000</td>
      <td>668.1200</td>
      <td>670.8808</td>
      <td>331188</td>
      <td>2021-05-04 09:50:00-04:00</td>
      <td>2</td>
      <td>70</td>
      <td>670.003163</td>
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
      <th>832</th>
      <td>632.2902</td>
      <td>633.1300</td>
      <td>630.3750</td>
      <td>630.4200</td>
      <td>208316</td>
      <td>2021-05-10 15:35:00-04:00</td>
      <td>2</td>
      <td>139</td>
      <td>631.804244</td>
    </tr>
    <tr>
      <th>833</th>
      <td>630.4000</td>
      <td>630.6800</td>
      <td>628.3800</td>
      <td>629.2400</td>
      <td>388961</td>
      <td>2021-05-10 15:40:00-04:00</td>
      <td>2</td>
      <td>140</td>
      <td>629.510306</td>
    </tr>
    <tr>
      <th>834</th>
      <td>629.3100</td>
      <td>630.8900</td>
      <td>628.5000</td>
      <td>629.3700</td>
      <td>337088</td>
      <td>2021-05-10 15:45:00-04:00</td>
      <td>2</td>
      <td>141</td>
      <td>629.695056</td>
    </tr>
    <tr>
      <th>835</th>
      <td>629.4600</td>
      <td>629.8700</td>
      <td>627.6101</td>
      <td>628.4810</td>
      <td>365889</td>
      <td>2021-05-10 15:50:00-04:00</td>
      <td>2</td>
      <td>142</td>
      <td>628.728706</td>
    </tr>
    <tr>
      <th>836</th>
      <td>628.6200</td>
      <td>630.7850</td>
      <td>628.4326</td>
      <td>629.0400</td>
      <td>452539</td>
      <td>2021-05-10 15:55:00-04:00</td>
      <td>2</td>
      <td>143</td>
      <td>629.615056</td>
    </tr>
  </tbody>
</table>
<p>390 rows × 9 columns</p>
</div>




```python

```
