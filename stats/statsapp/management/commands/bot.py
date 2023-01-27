from django.core.management.base import BaseCommand
from stats.settings import env
from telebot import TeleBot
from statsapp.models import ConverterLogsBotData

# Объявление переменной бота
bot = TeleBot(env('CONVERTER_LOGS_TOKEN'), threaded=False)


class Command(BaseCommand):
    # Используется как описание команды обычно
    help = 'Implemented to Django application telegram bot setup command'

    def handle(self, *args, **kwargs):
        print('Бот запущен')
        bot.enable_save_next_step_handlers(delay=2)  # Сохранение обработчиков
        bot.load_next_step_handlers()  # Загрузка обработчиков
        bot.infinity_polling()  # Бесконечный цикл бота


# Начало, добавление chat id в базу для последующей рассылки всем подписавшимся
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    record_exists_check = ConverterLogsBotData.objects.filter(chat_id=chat_id)
    if record_exists_check.count() == 0:
        new_chat = ConverterLogsBotData(chat_id=chat_id)
        new_chat.save()
        bot.send_message(chat_id, 'Начинаем, следующие логи конвертера будут приходить сюда.')
    else:
        bot.send_message(chat_id, 'Вы уже в базе, следующие логи конвертера будут приходить сюда')


# # Handle all other messages with content_type 'text' (content_types defaults to ['text'])
# @bot.message_handler(func=lambda message: True)
# def echo_message(message):
#     print(message.chat.id)
#     bot.reply_to(message, message.text)
