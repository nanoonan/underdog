# import logging

# from typing import (
#     Any, Optional
# )

# import pandas as pd

# from underdog.tdaclient import tda

# logger = logging.getLogger(__name__)

# def option_chain(symbol: str) -> Optional[pd.DataFrame]:

#     result = tda.api.get_option_chain(
#         symbol,
#         contract_type = tda.api.Options.ContractType.ALL
#     )
#     assert result.status_code == 200, result.raise_for_status()

#     rows = []

#     def convert(data: Any):
#         if isinstance(data, str):
#             return 0.0
#         return float(data)

#     def parse(key: str):
#         rows = []
#         for date, strikes in result.json()[key + 'ExpDateMap'].items():
#             date, daystoexp = date.split(':')
#             for strike, contract in strikes.items():
#                 symbol = contract[0]['symbol'].strip()
#                 row = dict(
#                     symbol = symbol,
#                     type = key,
#                     strike = float(strike),
#                     expiration = pd.Timestamp(
#                         int(contract[0]['expirationDate']),
#                         tz = 'US/Eastern', unit = 'ms'
#                     ),
#                     bid = contract[0]['bid'],
#                     ask = contract[0]['ask'],
#                     days_to_expiration = int(daystoexp),
#                     sortkey = symbol[0:symbol.rindex('P') + 1] \
#                     if key == 'put' else symbol[0:symbol.rindex('C') + 1],
#                     volume = convert(contract[0]['totalVolume']),
#                     delta = convert(contract[0]['delta']) \
#                     if convert(contract[0]['delta']) != 0.0 else float('nan'),
#                     gamma = convert(contract[0]['gamma']),
#                     theta = convert(contract[0]['theta']),
#                     rho = convert(contract[0]['rho']),
#                     vega = convert(contract[0]['vega']),
#                     close = convert(contract[0]['closePrice']),
#                     volatility = convert(contract[0]['volatility']),
#                     implied_volatility = convert(contract[0]['theoreticalVolatility']),
#                     open_interest = convert(contract[0]['openInterest']),
#                 )
#                 rows.append(row)
#         return rows

#     rows.extend(parse('call'))
#     rows.extend(parse('put'))

#     return pd.DataFrame(rows)
