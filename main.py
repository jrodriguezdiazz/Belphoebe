import os
import telebot
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, ForceReply

USER_DATA = {}
load_dotenv()
BOT_KEY = os.getenv('BOT_KEY')
EMAIL_ADDERS = os.getenv('EMAIL_ADDERS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
bot = telebot.TeleBot(BOT_KEY)


@bot.message_handler(["help", "start"])
def send_message(message):
    bot.reply_to(message, "Hello, How are you? 🙋🏻‍♀️")


@bot.message_handler(commands=["ask"])
def start_ask(message):
    markup = ReplyKeyboardMarkup()
    msg = bot.reply_to(message, "What is your name?", reply_markup=markup)
    bot.register_next_step_handler(msg, ask_phone_number)


def ask_phone_number(message):
    USER_DATA[message.chat.id] = {}
    USER_DATA[message.chat.id]["name"] = message.text
    markup = ForceReply()
    msg = bot.send_message(message.chat.id, "¿Cuál es tu número telefónico?", reply_markup=markup)
    bot.register_next_step_handler(msg, ask_sex)


def ask_sex(message):
    if not message.text.isdigit():
        markup = ForceReply()
        msg = bot.send_message(message.chat.id, "¿Cuál es tu número telefónico?", reply_markup=markup)
        bot.register_next_step_handler(msg, ask_sex)
    else:
        USER_DATA[message.chat.id]["phone"] = int(message.text)
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, input_field_placeholder="Pulsa el botón para enviar")
        markup.add("Hombre", "Mujer")
        msg = bot.send_message(message.chat.id, "¿Eres hombre o mujer?", reply_markup=markup)
        bot.register_next_step_handler(msg, save_user_data)


def save_user_data(message):
    USER_DATA[message.chat.id]["sex"] = message.text
    text = "Datos Introducidos: \n"
    text += f'<code>Nombre: {USER_DATA[message.chat.id]["name"]}</code>\n'
    text += f'<code>Número telefónico: {USER_DATA[message.chat.id]["phone"]}</code>\n'
    text += f'<code>Sexo: {USER_DATA[message.chat.id]["sex"]}</code>\n'
    bot.send_message(message.chat.id, text, parse_mode="html")


if __name__ == '__main__':
    print("Welcome to the bot")
    bot.set_my_commands([
        telebot.types.BotCommand(command="/start", description="Iniciar el bot"),
        telebot.types.BotCommand(command="/ask", description="Empezar a preguntar"),
    ])
    bot.infinity_polling()
    print("Goodbye")
