## Overview
Status | Value
---|---
**Quality** | Pre-Alpha
**Tested** | Windows only
**Requires** | Python 3.8+

The *underdog* package provides Python classes and functions to easily access free equity-related data via Numpy arrays or Pandas DataFrames. Data is automatically downloaded, kept up to date, and cached on disk for convenience and to improve performance and limit API requests to the data providers (which often rate limit the APIs). Currently, data is pulled from [Polygon](https://polygon.io), [finviz](https://finviz.com), and [TD Ameritrade](https://www.tdameritrade.com/home.html).

Real-time streams of time and sales, level one quotes, and one minute candle data are also supported. The data streams are written to a persistent log and the data can be accessed from multiple processes.

## Installation

1. Install [parkit](https://github.com/nanoonan/parkit), which provides the storage layer.

2. Install _underdog_ by opening a command prompt, navigating to the top-level directory of the git installation, and running the following command.

```
python -m pip install .
```

3. You'll need a free account with [Polygon](https://polygon.io) and a developer account with TD Ameritrade. The documentation for [tda-api](https://tda-api.readthedocs.io/en/latest/index.html) has more information on setting up a TDA developer account.

4. Finally, set up the environment variables used to access data from your accounts. The next cell describes these variables.

Environment Variable | Description
---|---
POLYGON_API_KEY | The API key from your Polygon account
TDA_TOKEN_PATH | Path to file where TDA auth token is stored
TDA_API_KEY | The API key from your TDA developer account
TDA_REDIRECT_URI | In most cases this will be https://localhost
TDA_ACCOUNT_ID | Account id for your TDA trading account

## Example Usage
```
enable_tasks()

# Create a cache of historic data for the defined symbols and update daily right after midnight
symbols = ['TSLA', 'AAL', 'MSFT']
schedule(update_cache, frequency = Frequency.DAY, period = 1, start = 'tomorrow 12:05 am', symbols = symbols)

# Get Numpy array for TSLA 1 minute data
arr = File('cache/intraday/1/TSLA').get_content()

# Get Pandas DataFrame for TSLA 1 minute data
df = as_pandas(File('cache/intraday/1/TSLA').get_content())
```
