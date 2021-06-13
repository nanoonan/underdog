import logging

from typing import Any

import parkit

from parkit import (
    Array,
    self
)

class LogHandler(logging.StreamHandler):

    def __init__(self, log: Array):
        super().__init__()
        self._log = log

    def emit(self, record: Any):
        self._log.append(self.format(record))

def add_logger(logger, name: str):
    self = parkit.self()
    if 'log' not in self.attributes():
        self.log = Array('log/{0}'.format(name))
    handler = LogHandler(self.log)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s@%(name)s : %(message)s'))
    logger.addHandler(handler)
    self.log.clear()
