import os
import telebot
from dotenv import load_dotenv

load_dotenv()
BOT_KEY = os.getenv('BOT_KEY')

bot = telebot.TeleBot(BOT_KEY)

commands = ["help", "start"]


@bot.message_handler(commands)
def send_message(message):
    bot.reply_to(message, "Hello, How are you? 🙋🏻‍♀️")


bot.polling()
