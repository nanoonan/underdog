# pylint: disable = broad-except, too-many-return-statements
import datetime

from typing import (
   Any, Dict, List, Optional, Union
)

from functools import lru_cache

import aiohttp
from lxml import html

from underdog.asyncthread import AsyncThread

_stock_url = 'https://finviz.com/quote.ashx'

_news_url = 'https://finviz.com/news.ashx'

_headers = {
    'User-Agent':
    """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)
    AppleWebKit/537.36 (KHTML, like Gecko)
    Chrome/39.0.2171.95 Safari/537.36"""
}

def _parse_stock_data_field(
    data: Dict[str, str],
    valuetype: Any,
    key: str
) -> Optional[Union[float, int, bool]]:
    if valuetype is bool:
        try:
            value = data[key]
            if value == "Yes":
                return True
            if value == "No":
                return False
            return False
        except Exception:
            return False
    if valuetype is float or valuetype is int:
        multiplier = 1.0
        if data[key].endswith("M"):
            multiplier = 1000000.0
            data[key] = data[key][0:-1]
        elif data[key].endswith("B"):
            multiplier = 1000000000.0
            data[key] = data[key][0:-1]
        elif data[key].endswith("%") and valuetype is float:
            multiplier = 0.01
            data[key] = data[key][0:-1]
        try:
            return valuetype(float(data[key]) * multiplier)
        except Exception:
            return None
    return None

def safe_round(value: Optional[float], places: int = 0) -> Optional[float]:
    if value is None:
        return value
    return round(value, places)

async def _to_dict(data: Dict[str, str]) -> Dict[str, Optional[Union[float, bool, int]]]:
    insider_ownership = safe_round(_parse_stock_data_field(data, float, 'Insider Own'), 2)
    institutional_ownership = safe_round(_parse_stock_data_field(data, float, 'Inst Own'), 2)
    if insider_ownership is None or institutional_ownership is None:
        retail_ownership = None
        insider_ownership = None
        institutional_ownership = None
    else:
        retail_ownership = safe_round(abs(1.0 - institutional_ownership - insider_ownership), 2)
    return dict(
        market_cap = _parse_stock_data_field(data, int, 'Market Cap'),
        shares_float = _parse_stock_data_field(data, int, 'Shs Float'),
        shares_outstanding = _parse_stock_data_field(data, int, 'Shs Outstand'),
        insider_ownership = insider_ownership,
        institutional_ownership = institutional_ownership,
        retail_ownership = retail_ownership,
        short_float = safe_round(_parse_stock_data_field(data, float, 'Short Float'), 2),
        employees = _parse_stock_data_field(data, int, 'Employees'),
        has_options = _parse_stock_data_field(data, bool, 'Optionable'),
        is_shortable = _parse_stock_data_field(data, bool, 'Shortable')
    )

@lru_cache
def fetch_ticker_details(symbol: str) -> Dict[str, Optional[Union[float, bool, int]]]:
    try:
        thread = AsyncThread()
        thread.start()
        return thread.run_task(async_fetch_ticker_details(symbol))
    finally:
        thread.stop()

async def async_fetch_ticker_details(
    symbol: str
) -> Optional[Dict[str, Optional[Union[float, bool, int]]]]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            _stock_url, headers = _headers, params = {'t': symbol}
        ) as response:
            if response.status == 200:
                page = html.fromstring(await response.text())
                data = {}
                all_rows = [
                    row.xpath('td//text()')
                    for row in page.cssselect('tr[class="table-dark-row"]')
                ]
                for row in all_rows:
                    for column in range(0, 11):
                        if column % 2 == 0:
                            data[row[column]] = row[column + 1]
                return await _to_dict(data)
            if response.status == 404:
                return None
            raise RuntimeError('Server response code {0}'.format(response.status))

def fetch_ticker_news(symbol: str) -> List[Dict[str, Any]]:
    try:
        thread = AsyncThread()
        thread.start()
        return thread.run_task(async_fetch_ticker_news(symbol))
    finally:
        thread.stop()

async def async_fetch_ticker_news(symbol: str) -> List[Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        async with session.get(_stock_url, headers = _headers, params = {'t': symbol}) as response:
            if response.status == 200:
                page = html.fromstring(await response.text())
                news = page.cssselect('a[class="tab-link-news"]')
                dates = []
                for i, _ in enumerate(news):
                    tr = news[i].getparent().getparent().getparent().getparent()
                    date_str = tr[0].text.strip()
                    if ' ' not in date_str:
                        tbody = tr.getparent()
                        previous_date_str = ''
                        j = 1
                        while ' ' not in previous_date_str:
                            try:
                                previous_date_str = tbody[i-j][0].text.strip()
                            except IndexError:
                                break
                            j += 1
                        date_str = ' '.join([previous_date_str.split(' ')[0], date_str])
                    news_date = datetime.datetime.strptime(date_str, "%b-%d-%y %I:%M%p")
                    dates.append(news_date)
                headlines = [row.xpath('text()')[0] for row in news]
                urls = [row.get('href') for row in news]
                items = []
                for date, headline, url in list(zip(dates, headlines, urls)):
                    items.append(dict(
                        date = str(date),
                        headline = headline,
                        url = url
                    ))
                return items
            raise RuntimeError('Server response code {0}'.format(response.status))
