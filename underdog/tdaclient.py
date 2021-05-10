# pylint: disable = too-few-public-methods
import logging
import threading

from parkit import getenv
from selenium import webdriver
from tda import auth

import underdog.constants as constants

logger = logging.getLogger(__name__)

class TDA(threading.local):

    def __init__(self):
        super().__init__()
        self._client = None
        self._token_path = getenv(constants.TDA_TOKEN_PATH_ENVNAME)
        self._api_key = getenv(constants.TDA_API_KEY_ENVNAME)
        self._redirect_uri = getenv(constants.TDA_REDIRECT_URI_ENVNAME)

    @property
    def api(self):
        if self._client is None:
            try:
                self._client = auth.client_from_token_file(self._token_path, self._api_key)
            except FileNotFoundError:
                with webdriver.Chrome() as driver:
                    self._client = auth.client_from_login_flow(
                        driver, self._api_key, self._redirect_uri, self._token_path
                    )
        return self._client

tda = TDA()
