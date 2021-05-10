```python
from underdog import help
```

## Overview
**Status**: Development

**Tested**: Windows only

**Requires**: Python 3.8+

The *underdog* package provides Python classes and functions to easily access free equity-related data through Panda dataframes. Data is cached on disk to improve performance and limit API requests to the data providers (which often rate limit the APIs). Currently, data is pulled from [Polygon](www.polygon.io), [finViz](https://finviz.com), and TD Ameritrade. 

Feel free to send questions, comments or feedback to: nanoonan at marvinsmind dot com.


## Installation

1. Install [parkit](https://github.com/nanoonan/parkit), which provides the storage layer. Make sure the _parkit_ directory is included in your PYTHONPATH.

2. Install _underdog_ by opening a command prompt, navigating to the top-level directory of the git installation, and running the following command.

```
python -m pip install .
```

3. You'll need a free account with [Polygon](https://polygon.io) and a developer account with TD Ameritrade. The documentation for [tda-api](https://tda-api.readthedocs.io/en/latest/index.html) has more information on setting up a TDA developer account.

4. Finally, set up the environment variables used to access data from your accounts. The next cell describes these variables.


```python
help('environment')
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
help()
```

    help(topic: str) -> useful information
    Valid help topics: introduction, installation, classes, functions
    


```python
help('classes')
```

    ╒═════════════════════════╤═══════════════════════════════════════════════════════════════════════╕
    │ Type                    │ Description                                                           │
    ╞═════════════════════════╪═══════════════════════════════════════════════════════════════════════╡
    │ [Market, Day, IntraDay] │ The historic data classes implement a Dict-like interface to access   │
    │                         │ historic stock data. Valid keys are dates, integers, or strings       │
    │                         │ containing dates in 'YYYY-MM-DD' format. Slices are also supported.   │
    │                         │ Assuming x is an instance, here are some examples: x['2020-01-01'],   │
    │                         │ x['2020-01-01':'2021-01-01'], x[-252:] (returns last 252 trading days │
    │                         │ of data). Data is returned in a Panda table.                          │
    ├─────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ Market                  │ The Market class contains 2 years of daily data for all tickers       │
    │                         │ traded.                                                               │
    ├─────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ Day                     │ The Day class contains 20 years of daily data for a specific ticker.  │
    ├─────────────────────────┼───────────────────────────────────────────────────────────────────────┤
    │ IntraDay                │ The IntraDay class contains about two months of one-minute intraday   │
    │                         │ data for a specific tickers. Includes pre and post market trades. The │
    │                         │ IntraDay class contains about two months of one-minute intraday data  │
    │                         │ for a specific tickers. Includes pre and post market trades.          │
    ╘═════════════════════════╧═══════════════════════════════════════════════════════════════════════╛
    


```python
help('functions')
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
    ╘═════════════════════════╧═══════════════════════════════════════════════════════════════════════╛
    

## Examples


```python
from underdog import Market
df = Market()[:]
df
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
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
      <td>76.868060</td>
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
      <th>4521651</th>
      <td>ARCM</td>
      <td>200</td>
      <td>100.0298</td>
      <td>100.0300</td>
      <td>100.0300</td>
      <td>100.0300</td>
      <td>100.0300</td>
      <td>2021-05-07</td>
      <td>100.030000</td>
    </tr>
    <tr>
      <th>4521652</th>
      <td>ESGN</td>
      <td>728</td>
      <td>28.6764</td>
      <td>28.6150</td>
      <td>28.6150</td>
      <td>28.6150</td>
      <td>28.6150</td>
      <td>2021-05-07</td>
      <td>28.615000</td>
    </tr>
    <tr>
      <th>4521653</th>
      <td>EAOK</td>
      <td>363</td>
      <td>27.5315</td>
      <td>27.5347</td>
      <td>27.5347</td>
      <td>27.5347</td>
      <td>27.5347</td>
      <td>2021-05-07</td>
      <td>27.534700</td>
    </tr>
    <tr>
      <th>4521654</th>
      <td>EAOM</td>
      <td>100</td>
      <td>28.5166</td>
      <td>28.6215</td>
      <td>28.6215</td>
      <td>28.6215</td>
      <td>28.6215</td>
      <td>2021-05-07</td>
      <td>28.621500</td>
    </tr>
    <tr>
      <th>4521655</th>
      <td>DYHG</td>
      <td>18</td>
      <td>56.9200</td>
      <td>57.0110</td>
      <td>57.0110</td>
      <td>57.0110</td>
      <td>57.0110</td>
      <td>2021-05-07</td>
      <td>57.011000</td>
    </tr>
  </tbody>
</table>
<p>4521656 rows × 9 columns</p>
</div>




```python
from underdog import ticker_details
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
# Last five days of TSLA intraday (one-minute) data
df = IntraDay('TSLA')[-5:]
# Filter for only regular hours trading (1 = pre-market, 2 = regular hours, 3 = extended hours)
df[df['trading_segment'] == 2]
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
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
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>195</th>
      <td>703.8000</td>
      <td>706.0000</td>
      <td>702.8900</td>
      <td>703.5200</td>
      <td>213505</td>
      <td>2021-05-03 09:30:00-04:00</td>
      <td>2</td>
    </tr>
    <tr>
      <th>196</th>
      <td>703.9800</td>
      <td>703.9899</td>
      <td>699.2788</td>
      <td>699.3318</td>
      <td>149198</td>
      <td>2021-05-03 09:31:00-04:00</td>
      <td>2</td>
    </tr>
    <tr>
      <th>197</th>
      <td>699.5800</td>
      <td>701.5500</td>
      <td>698.5341</td>
      <td>698.7457</td>
      <td>97179</td>
      <td>2021-05-03 09:32:00-04:00</td>
      <td>2</td>
    </tr>
    <tr>
      <th>198</th>
      <td>698.5001</td>
      <td>701.6700</td>
      <td>698.5001</td>
      <td>699.1600</td>
      <td>107517</td>
      <td>2021-05-03 09:33:00-04:00</td>
      <td>2</td>
    </tr>
    <tr>
      <th>199</th>
      <td>699.0000</td>
      <td>701.4600</td>
      <td>699.0000</td>
      <td>699.6600</td>
      <td>89382</td>
      <td>2021-05-03 09:34:00-04:00</td>
      <td>2</td>
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
      <th>3414</th>
      <td>671.8700</td>
      <td>673.0000</td>
      <td>671.8000</td>
      <td>672.5700</td>
      <td>93098</td>
      <td>2021-05-07 15:55:00-04:00</td>
      <td>2</td>
    </tr>
    <tr>
      <th>3415</th>
      <td>672.5600</td>
      <td>672.7500</td>
      <td>672.3400</td>
      <td>672.6000</td>
      <td>55404</td>
      <td>2021-05-07 15:56:00-04:00</td>
      <td>2</td>
    </tr>
    <tr>
      <th>3416</th>
      <td>672.5671</td>
      <td>672.9500</td>
      <td>672.4200</td>
      <td>672.9500</td>
      <td>69338</td>
      <td>2021-05-07 15:57:00-04:00</td>
      <td>2</td>
    </tr>
    <tr>
      <th>3417</th>
      <td>672.9700</td>
      <td>673.0000</td>
      <td>672.6100</td>
      <td>672.9000</td>
      <td>95969</td>
      <td>2021-05-07 15:58:00-04:00</td>
      <td>2</td>
    </tr>
    <tr>
      <th>3418</th>
      <td>672.9000</td>
      <td>672.9400</td>
      <td>671.9000</td>
      <td>672.3600</td>
      <td>148692</td>
      <td>2021-05-07 15:59:00-04:00</td>
      <td>2</td>
    </tr>
  </tbody>
</table>
<p>1950 rows × 7 columns</p>
</div>




```python
from underdog import intraday
intraday('TSLA')
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
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
      <th>twap</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>667.000</td>
      <td>668.16</td>
      <td>665.49</td>
      <td>667.29</td>
      <td>19844</td>
      <td>2021-05-10 07:00:00-04:00</td>
      <td>1</td>
      <td>666.824053</td>
    </tr>
    <tr>
      <th>1</th>
      <td>667.450</td>
      <td>667.94</td>
      <td>667.20</td>
      <td>667.73</td>
      <td>2285</td>
      <td>2021-05-10 07:01:00-04:00</td>
      <td>1</td>
      <td>667.569258</td>
    </tr>
    <tr>
      <th>2</th>
      <td>667.800</td>
      <td>669.99</td>
      <td>667.52</td>
      <td>669.34</td>
      <td>3380</td>
      <td>2021-05-10 07:02:00-04:00</td>
      <td>1</td>
      <td>668.774914</td>
    </tr>
    <tr>
      <th>3</th>
      <td>669.380</td>
      <td>669.38</td>
      <td>668.30</td>
      <td>668.59</td>
      <td>1317</td>
      <td>2021-05-10 07:03:00-04:00</td>
      <td>1</td>
      <td>668.817609</td>
    </tr>
    <tr>
      <th>4</th>
      <td>668.500</td>
      <td>669.02</td>
      <td>668.40</td>
      <td>668.99</td>
      <td>253</td>
      <td>2021-05-10 07:04:00-04:00</td>
      <td>1</td>
      <td>668.703523</td>
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
    </tr>
    <tr>
      <th>645</th>
      <td>624.575</td>
      <td>624.80</td>
      <td>624.00</td>
      <td>624.18</td>
      <td>932</td>
      <td>2021-05-10 17:45:00-04:00</td>
      <td>3</td>
      <td>624.401460</td>
    </tr>
    <tr>
      <th>646</th>
      <td>624.350</td>
      <td>624.50</td>
      <td>624.00</td>
      <td>624.25</td>
      <td>1280</td>
      <td>2021-05-10 17:46:00-04:00</td>
      <td>3</td>
      <td>624.249495</td>
    </tr>
    <tr>
      <th>647</th>
      <td>624.250</td>
      <td>624.50</td>
      <td>624.00</td>
      <td>624.00</td>
      <td>899</td>
      <td>2021-05-10 17:47:00-04:00</td>
      <td>3</td>
      <td>624.258333</td>
    </tr>
    <tr>
      <th>648</th>
      <td>624.000</td>
      <td>624.44</td>
      <td>623.50</td>
      <td>624.00</td>
      <td>2040</td>
      <td>2021-05-10 17:48:00-04:00</td>
      <td>3</td>
      <td>623.970000</td>
    </tr>
    <tr>
      <th>649</th>
      <td>623.750</td>
      <td>624.44</td>
      <td>623.75</td>
      <td>624.05</td>
      <td>616</td>
      <td>2021-05-10 17:49:00-04:00</td>
      <td>3</td>
      <td>624.104673</td>
    </tr>
  </tbody>
</table>
<p>650 rows × 8 columns</p>
</div>




```python

```
