import logging
import time


class ApiErrorHandler:
    """
    Кастомный обработчик ошибок для API авто.ру.
    """

    def __init__(self, max_retries: int = 5, retry_delay: int = 2):
        """
        Инициализация обработчика ошибок с параметрами.
        :param max_retries: Максимальное количество попыток при ошибках API.
        :param retry_delay: Задержка между повторными попытками.
        """
        self.__max_retries = max_retries  # максимальное количество попыток
        self.__retry_delay = retry_delay  # базовая задержка перед повторной попыткой

    def handle_error(self, response_data: dict, status_code: int) -> bool:
        """
        Главный метод для обработки ошибок API.
        :param response_data: Ответ от API в виде словаря.
        :param status_code: HTTP статус-код.
        :return: True, если запрос нужно повторить, иначе False.
        """
        if status_code == 200:
            # Успешный запрос
            return False

        if 'error' not in response_data:
            logging.error(f"Неожиданная структура ошибки в ответе: {response_data}")
            return False

        error = response_data.get('error', '')
        detailed_error = response_data.get('detailed_error', '')

        # Логируем детализированную ошибку
        logging.error(f"Произошла ошибка: {error}, Детали: {detailed_error}, Код статуса: {status_code}")

        if status_code >= 500:
            # 5xx ошибки — проблемы на стороне сервера
            return self.__handle_server_error(status_code)

        if status_code >= 400:
            # 4xx ошибки — проблемы на стороне клиента (например, неверные данные)
            return self.__handle_client_error(error, status_code)

        return False

    def __handle_server_error(self, status_code: int) -> bool:
        """
        Приватный метод для обработки ошибок 5xx (ошибки сервера).
        :param status_code: HTTP статус-код.
        :return: True, если стоит повторить запрос, иначе False.
        """
        if status_code == 500:
            logging.error("Внутренняя ошибка сервера (500). Пытаемся повторить запрос...")
        else:
            logging.error(f"Неизвестная ошибка сервера (код {status_code}).")

        # Пытаемся повторить запрос несколько раз
        for attempt in range(self.__max_retries):
            wait_time = self.__retry_delay * (2 ** attempt)  # Экспоненциальная задержка
            logging.warning(f"Повторная попытка через {wait_time} секунд (попытка {attempt + 1})...")
            time.sleep(wait_time)
        return True

    def __handle_client_error(self, error: str, status_code: int) -> bool:
        """
        Приватный метод для обработки ошибок 4xx (ошибки клиента).
        :param error: Текстовый код ошибки.
        :param status_code: HTTP статус-код.
        :return: True, если стоит повторить запрос, иначе False.
        """
        if status_code == 400:
            logging.error(f"Неверный запрос (400). Проверьте синтаксис и данные: {error}")
            return False

        if status_code == 401 and error in ['AUTH_ERROR', 'NO_AUTH']:
            # Ошибки авторизации
            return self.__handle_auth_error()

        if status_code == 402 and error == 'NOT_ENOUGH_FUNDS_ON_ACCOUNT':
            logging.error("Недостаточно средств на аккаунте для выполнения операции.")
            return False

        if status_code == 403:
            return self.__handle_forbidden_error(error)

        if status_code == 404:
            if error == 'OFFER_NOT_FOUND':
                logging.error("Объявление не найдено (404).")
            elif error == 'CLIENT_NOT_FOUND':
                logging.error("Клиент не найден (404).")
            return False

        if status_code == 409 and error == 'NO_PHONE':
            logging.error("Не указан номер телефона продавца (409).")
            return False

        if status_code == 422:
            logging.error(f"Ошибка обработки данных (422): {error}")
            return False

        if status_code == 429:
            # Лимит запросов (Too Many Requests)
            logging.warning("Превышен лимит запросов (429). Повторяем с задержкой.")
            return self.__handle_rate_limit_error()

        logging.error(f"Необработанная ошибка клиента: {error} (код {status_code})")
        return False

    def __handle_rate_limit_error(self) -> bool:
        """
        Приватный метод для обработки ошибки превышения лимита запросов (429).
        """
        for attempt in range(self.__max_retries):
            wait_time = self.__retry_delay * (2 ** attempt)
            logging.warning(f"Превышен лимит запросов. Повторная попытка через {wait_time} секунд...")
            time.sleep(wait_time)
        return True

    def __handle_auth_error(self) -> bool:
        """
        Приватный метод для обработки ошибки авторизации (401).
        Возвращает True для повторной попытки авторизации и запроса.
        """
        logging.error("Ошибка авторизации: неверный логин или пароль, либо истекла сессия. Повторная авторизация...")
        return True

    def __handle_forbidden_error(self, error: str) -> bool:
        """
        Приватный метод для обработки ошибок доступа (403).
        """
        if error in ['CODE_AUTH_REQUIRED', 'PASSWORD_EXPIRED']:
            logging.error("Требуется повторная аутентификация или пароль устарел.")
            return False
        elif error in ['CUSTOMER_ACCESS_FORBIDDEN', 'AGENT_ACCESS_FORBIDDEN']:
            logging.error("Доступ для данного пользователя запрещен (403).")
            return False
        else:
            logging.error(f"Запрещенный доступ: {error}")
            return False

    def __handle_unhandled_error(self, error: str, status_code: int) -> bool:
        """
        Приватный метод для обработки необработанных ошибок.
        :param error: Текст ошибки.
        :param status_code: HTTP статус-код.
        :return: False, поскольку запрос не должен быть повторен.
        """
        logging.error(f"Необработанная ошибка API: {error} (код {status_code})")
        return False
