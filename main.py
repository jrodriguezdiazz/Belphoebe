import os
import telebot
import smtplib
from telebot import types
from dotenv import load_dotenv

load_dotenv()
BOT_KEY = os.getenv('BOT_KEY')
EMAIL_ADDERS = os.getenv('EMAIL_ADDERS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
bot = telebot.TeleBot(BOT_KEY)

commands = ["help", "start"]


@bot.message_handler(commands)
def send_message(message):
    bot.reply_to(message, "Hello, How are you? 🙋🏻‍♀️")


def get_product_information():
    return "SELECT * FROM products"


def get_order_information():
    return "SELECT * FROM products"


def get_recommendations():
    return []


def send_email(to_adders):
    order = 'A111'
    message = 'Subject: Prueba \n\n Orden #{order} registrada. (Estará disponible en un lapso no mayor a 7 días.)'.format(
        order=order)
    connection = smtplib.SMTP('smtp.gmail.com', 587)
    connection.ehlo()
    connection.starttls()
    connection.login(EMAIL_ADDERS, EMAIL_ADDERS)
    connection.sendmail(EMAIL_ADDERS, to_adders, message)


def reserve_product():
    query = ""


def delete_order():
    query = ""


def show_menu(message):
    chat_id = message.chat.id
    first_name = message.chat.first_name
    message = "Elija la opción deseada {first_name}?".format(first_name=first_name)
    prod_btn = types.ReplyKeyboardMarkup(row_width=1)
    new_order = types.KeyboardButton("ORDENAR")
    consult_order = types.KeyboardButton("CONSULTAR ORDEN")
    cancel_order = types.KeyboardButton("CANCELAR ORDEN")
    prod_btn.row(new_order, consult_order)
    prod_btn.row(cancel_order)
    bot.send_message(chat_id, message, reply_markup=prod_btn)


bot.polling()
