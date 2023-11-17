from django.core.management.base import BaseCommand
from telebot import TeleBot

from applications.autoconverter.models import ConverterLogsBotData
from stats.settings import env

# Объявление переменной бота для конвертера
bot = TeleBot(env('CONVERTER_LOGS_TOKEN'), threaded=False)


class Command(BaseCommand):
    help = 'Телеграм бот для Автоконвертера'

    def handle(self, *args, **kwargs):
        print('Бот Конвертера запущен')
        bot.enable_save_next_step_handlers(delay=2)  # Сохранение обработчиков
        bot.load_next_step_handlers()  # Загрузка обработчиков
        bot.infinity_polling()  # Бесконечный цикл бота


@bot.message_handler(commands=['help'])
def help_message(message):
    msg = 'Этот бот для логов конвертера.\nПосле того как ты подпишешься на него через /start или /subscribe бот ' \
          'начнёт присылать тебе логи и прайс.\n\nЛоги есть в текстовом варианте - чтобы ты мог их посмотреть не ' \
          'открывая файл.\nИ в файле - с него удобно добавлять нерасшифрованные коды.\n\nПрайс уже в csv - можешь ' \
          'сразу грузить в базу.\n\nЧтобы отписаться: /unsubscribe'
    bot.send_message(message.chat.id, msg)


# Начало, добавление chat id в базу для последующей рассылки всем подписавшимся
@bot.message_handler(commands=['start', 'subscribe'])
def send_welcome(message):
    chat_id = message.chat.id
    record_exists_check = ConverterLogsBotData.objects.filter(chat_id=chat_id)
    if record_exists_check.count() == 0:
        new_chat = ConverterLogsBotData(chat_id=chat_id)
        new_chat.save()
        bot.send_message(chat_id, 'Начинаем, следующие логи конвертера будут приходить сюда.')
    else:
        bot.send_message(chat_id, 'Ты уже в базе, следующие логи конвертера будут приходить сюда')


@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    chat_id = message.chat.id
    record_exists_check = ConverterLogsBotData.objects.filter(chat_id=chat_id)
    if record_exists_check.count() > 0:
        record_exists_check[0].delete()
        bot.send_message(chat_id, 'Ты отписался, чтобы подписаться снова: /subscribe')
    else:
        bot.send_message(chat_id, 'Ты не в базе, чтобы подписаться: /subscribe')


# # Handle all other messages with content_type 'text' (content_types defaults to ['text'])
# @bot.message_handler(func=lambda message: True)
# def echo_message(message):
#     print(message.chat.id)
#     bot.reply_to(message, message.text)
