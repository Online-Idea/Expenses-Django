import threading

import requests
import logging
import time
from urllib.parse import urljoin
from abc import ABC, abstractmethod
from requests.exceptions import RequestException

from libs.autoru.services.error_handler import ApiErrorHandler
from stats.settings import env


class BaseAutoruApi(ABC):
    endpoint = 'https://apiauto.ru/'
    api_version = '1.0'
    max_retries = 5  # Максимальное количество попыток при ошибках
    retry_delay = 2

    # _instance = None
    # _lock = threading.Lock()
    #
    # def __new__(cls):
    #     if cls._instance is None:
    #         with cls._lock:
    #             if cls._instance is None:  # для безопасности
    #                 cls._instance = super(BaseAutoruApi, cls).__new__(cls)
    #     return cls._instance

    def __init__(self, api_key: str = None, login: str = None, password: str = None):
        """
        Инициализация класса с передачей API ключа, логина и пароля.
        Если не переданы, значения логина и пароля берутся из переменных окружения.
        """
        # if not hasattr(self, '_initialized'):
        self.__api_key = api_key or env('AUTORU_API_KEY')
        self.__login = login or env('AUTORU_LOGIN')
        self.__password = password or env('AUTORU_PASSWORD')

        self._session_id = None
        self._session = requests.Session()
        self.__setup_session_headers()

        self._error_handler = ApiErrorHandler(self.max_retries, self.retry_delay)
        self._initialized = True
        self._authenticating = False

    def __setup_session_headers(self):
        """
        Настройка заголовков для сессии. Устанавливаем API ключ и формат данных.
        """
        self._session.headers.update({
            'x-authorization': self.__api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def __lazy_authenticate(self):
        """
        Ленивая аутентификация — выполняется только при необходимости.
        """
        if not self._session_id:
            self.authenticate()

    def _send_auth_request(self) -> requests.Response:
        """
        Отправляет запрос на аутентификацию без проверки session_id.
        """
        url = '/auth/login'
        auth_data = {'login': self.__login, 'password': self.__password}
        full_url = urljoin(self.endpoint, f'{self.api_version}{url}')

        response = self._session.post(full_url, json=auth_data)
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.json()}")
        return response

    def authenticate(self) -> str:
        """
        Выполняет аутентификацию и устанавливает session_id.
        """
        if self._authenticating:
            # Если уже выполняется аутентификация, не запускаем её повторно.
            logging.warning("Authentication is already in progress.")
            return

        self._authenticating = True  # Устанавливаем флаг
        logging.info("Authenticating user...")

        try:
            response = self._send_auth_request()
            self._session_id = response.json().get('session', {}).get('id')
            logging.info(f"Authenticated successfully. Session ID: {self._session_id}")
        finally:
            self._authenticating = False  # Сбрасываем флаг
        return self._session_id

    def _prepare_headers(self, autoru_id: str = None) -> dict:
        """
        Подготовка заголовков для запроса.
        Добавляются session_id и autoru_id (если есть).
        """
        headers = self._session.headers.copy()
        if self._session_id:
            headers['x-session-id'] = self._session_id
        if autoru_id:
            headers['x-dealer-id'] = autoru_id
        return headers

    def _request_api(self, url: str, request_type: str, autoru_id: str = None,
                     params: dict = None, json: dict = None) -> requests.Response:
        """
        Выполнение запроса к API.
        Поддержка GET и POST запросов. В случае ошибки вызывается обработчик ошибок.
        """
        self.__lazy_authenticate()  # Аутентификация по требованию

        full_url = urljoin(self.endpoint, f'{self.api_version}{url}')

        print(f'{str(autoru_id):6} | {request_type:4} | {url}')

        headers = self._prepare_headers(autoru_id)

        try:
            response = self.__make_request(full_url, request_type, headers, params, json)
            response_data = response.json()
            status_code = response.status_code
            if self._error_handler.handle_error(response_data, status_code):
                return self._request_api(url, request_type, autoru_id, params, json)
            return response
        except RequestException as e:
            logging.error(f"Request to {full_url} failed: {e}")
            raise e

    def __make_request(self, full_url, request_type, headers, params, json):
        """
        Универсальный метод для выполнения GET и POST запросов.
        """
        if request_type == 'GET':
            return self._session.get(full_url, headers=headers, params=params)
        elif request_type == 'POST':
            return self._session.post(full_url, headers=headers, json=json)
        else:
            raise ValueError("Invalid request type. Expected 'GET' or 'POST'.")
