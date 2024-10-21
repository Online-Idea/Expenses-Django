from pprint import pprint

from django.core.management.base import BaseCommand

from libs.autoru.services.base_api_manager import BaseAutoruApi
from libs.autoru.services.feeds_manager import AutoruFeedsManager  # Импортируем класс из соответствующего модуля
import logging

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,  # Устанавливаем минимальный уровень логов для отображения
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат вывода сообщений
    handlers=[logging.StreamHandler()]  # Обработчик: вывод в консоль
)

class Command(BaseCommand):
    help = 'Тестирование работы класса AutoruFeedsManager для загрузки прайс-листов'

    def handle(self, *args, **kwargs):
        autoru_id = '51128'

        # Логгирование
        logging.info('Создаем экземпляр AutoruFeedsManager')
        # Создаем экземпляр класса
        feeds_manager = AutoruFeedsManager()

        # Получаем историю загрузки прайс-листов
        logging.info(f'Получаем историю фидов для autoru_id: {autoru_id}')
        feeds_history = feeds_manager.get_feeds_history(autoru_id)
        pprint(feeds_history)
        # Обрабатываем полученные данные
        logging.info('Обрабатываем полученные данные')
        feeds_manager.process_feeds_data(feeds_history)

        logging.info('Команда завершена успешно')
