import logging
from typing import List, Dict

from libs.autoru.services.base_api_manager import BaseAutoruApi


class AutoruFeedsManager(BaseAutoruApi):
    """
    Класс для работы с API авто.ру для загрузки и управления прайс-листами (фидами).
    """

    def __init__(self, api_key: str = None, login: str = None, password: str = None):
        """
        Инициализация класса AutoruFeedsManager с вызовом конструктора базового класса.
        :param api_key: API ключ авто.ру.
        :param login: Логин для авторизации.
        :param password: Пароль для авторизации.
        """
        super().__init__(api_key, login, password)

    def get_feeds_history(self, autoru_id: str) -> List[Dict]:
        """
        Получает историю загрузок прайс-листов через API авто.ру.
        :param autoru_id: Идентификатор клиента (x-dealer-id).
        :return: Список с информацией о загрузках прайс-листов.
        """
        logging.info(f"Fetching feeds history for autoru_id: {autoru_id}")
        url = '/feeds/history'
        response = self._request_api(url, 'GET', autoru_id=autoru_id)

        # Если запрос выполнен успешно, возвращаем список фидов
        if response.status_code == 200:
            try:
                feeds_data = response.json().get('feeds', [])
                logging.info(f"Fetched {len(feeds_data)} feed records.")
                return feeds_data
            except ValueError as e:
                logging.error(f"Error parsing JSON response: {e}")
                return []
        else:
            # Логируем ошибку, обработка делегируется обработчику ошибок
            logging.error(f"Failed to fetch feeds history. Status code: {response.status_code}")
            return []

    def process_feeds_data(self, feeds_data: List[Dict]):
        """
        Обрабатывает полученные данные о загрузках прайс-листов.
        :param feeds_data: Список с информацией о фидах.
        """
        for feed in feeds_data:
            task = feed.get('task', {})
            settings = feed.get('settings', {})

            print(f"ID задачи фида: {task.get('id')}")
            print(f"Статус фида: {task.get('status')}")
            print(f"Статус фида: {task.get('type')}")
            print(f"Дата создания фида: {task.get('created_at')}")
            print(f"Количество объявлений в фиде: {task.get('count_offers', 0)}")
            print()

            # Дополнительная обработка данных по необходимости
            # Например: сохранение информации в базе данных или логирование детальной информации


logging.basicConfig(level=logging.INFO)
