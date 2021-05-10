import logging

from typing import (
    Any, Dict
)

from underdog.tdaclient import tda

logger = logging.getLogger(__name__)

def quote(symbol: str) -> Dict[str, Any]:
    result = tda.api.get_quote(symbol)
    assert result.status_code == 200, result.raise_for_status()
    return result.json()[symbol]
