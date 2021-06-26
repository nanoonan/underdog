import logging
import time
import uuid

from typing import (
    Any, Iterator, List, Optional
)

import parkit.constants

from parkit import (
    Array,
    create_string_digest,
    Dict,
    get_site_uuid,
    getenv,
    import_site,
    transaction
)

logger = logging.getLogger(__name__)

import_site(
    getenv(parkit.constants.GLOBAL_SITE_STORAGE_PATH_ENVNAME, str),
    create = True
)

class RateLimiter():

    def __init__(
        self,
        name: str,
        interval: float,
        maxsize: int
    ):
        self._name = name
        paths = {}
        for obj_type in ['entry', 'exit']:
            paths[obj_type] = '/'.join([
                'memory/underdog',
                '-'.join([
                    'rate-limiter',
                    create_string_digest(
                        ''.join([
                            name,
                            str(interval),
                            str(maxsize),
                            obj_type
                        ])
                    )
                ])
            ])
        self._entry = Array(
            paths['entry'],
            maxsize = maxsize,
            create = True, bind = True,
            site_uuid = get_site_uuid(
                getenv(parkit.constants.GLOBAL_SITE_STORAGE_PATH_ENVNAME, str)
            )
        )
        self._exit = Dict(
            paths['exit'],
            create = True, bind = True,
            site_uuid = get_site_uuid(
                getenv(parkit.constants.GLOBAL_SITE_STORAGE_PATH_ENVNAME, str)
            )
        )
        self._maxsize = maxsize
        self._interval_ns = interval * 1e9
        self._entry_id = None
        self._errors: List[Any] = []
        self._failed = False
        self._attempts = 0

    @property
    def attempts(self) -> int:
        return self._attempts

    @property
    def name(self) -> str:
        return self._name

    @property
    def maxsize(self) -> int:
        return self._maxsize

    @property
    def interval(self) -> float:
        return self._interval_ns / 1e9

    @property
    def errors(self) -> List[Any]:
        return self._errors

    @property
    def failed(self) -> bool:
        return self._failed

    def try_request(
        self,
        max_attempts: int = 1
    ) -> Iterator[Any]:
        if self._entry_id is not None:
            raise RecursionError()
        self._errors = []
        self._failed = False
        self._attempts = 0
        for i in range(max_attempts):
            if i > 0:
                time.sleep(i * i)
            self._attempts += 1
            yield self
        self._failed = True

    def __enter__(self):
        while True:
            with transaction(self._entry):
                if len(self._entry) < self._maxsize:
                    entry_id = str(uuid.uuid4())
                    self._entry.append((time.time_ns(), entry_id))
                    self._entry_id = entry_id
                    return
                entry_ns, entry_id = self._entry[0]
                if entry_id in self._exit:
                    oldest_ns = self._exit.pop(entry_id)
                else:
                    oldest_ns = entry_ns
                now_ns = time.time_ns()
                if now_ns - oldest_ns > self._interval_ns:
                    entry_id = str(uuid.uuid4())
                    self._entry.append((time.time_ns(), entry_id))
                    self._entry_id = entry_id
                    return
            time.sleep((oldest_ns + self._interval_ns - now_ns) / 1e9)

    def __exit__(self, error_type: type, error: Optional[Any], traceback: Any):
        try:
            assert self._entry_id is not None
            self._exit[self._entry_id] = time.time_ns()
            return True
        finally:
            self._entry_id = None
            if error is not None:
                self._errors.append(error)
