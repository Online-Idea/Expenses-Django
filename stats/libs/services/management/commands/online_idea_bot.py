from django.core.management.base import BaseCommand
from stats.settings import env
from telebot import TeleBot


# Общий бот
online_idea_bot = TeleBot(env('ONLINE_IDEA_BOT_TOKEN'), threaded=False)


class Command(BaseCommand):
    help = 'Телеграм боты'

    def handle(self, *args, **kwargs):
        print('Бот Онлайн Идея запущен')
        online_idea_bot.enable_save_next_step_handlers(delay=2)
        online_idea_bot.load_next_step_handlers()
        online_idea_bot.infinity_polling()


@online_idea_bot.message_handler(commands=['test'])
def send_message_to_users(message):
    user_id = message.chat.id  # user id to who you want to send the message
    print(f'LOOK HERE {user_id=}')
    text_message = 'This is a test message'  # Message you want to send
    online_idea_bot.send_message(user_id, text_message)


@online_idea_bot.message_handler(commands=['chatid'])
def send_chat_id(message):
    online_idea_bot.reply_to(message, message.chat.id)

