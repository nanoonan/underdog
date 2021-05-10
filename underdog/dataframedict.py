# pylint: disable = no-self-use
import io
import logging
import mmap

import pandas as pd

from parkit import Dict

logger = logging.getLogger(__name__)

class DataFrameDict(Dict):

    def encitemkey(self, key):
        return key.encode('utf-8')

    def decitemkey(self, data):
        if isinstance(data, memoryview):
            return bytes(data).decode('utf-8')
        return data.decode('utf-8')

    def encitemval(self, df):
        buf = mmap.mmap(-1, 1073741824)
        df.to_feather(buf)
        return memoryview(buf[0:buf.tell()])

    def decitemval(self, data):
        buf = io.BytesIO(data)
        df = pd.read_feather(buf)
        buf.close()
        return df
