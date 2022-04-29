import json
import os
import random
import string

import nltk
import pandas as pd
import pyodbc
import requests
import telebot
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup

USER_DATA = {}
load_dotenv()
BOT_KEY = os.getenv('BOT_KEY')
IMDB_API_KEY = os.getenv('IMDB_API_KEY')
EMAIL_ADDERS = os.getenv('EMAIL_ADDERS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

bot = telebot.TeleBot(BOT_KEY)
conn = pyodbc.connect('Driver={SQL Server};'
                      'Server=JRODRIGUEZDIAZZ\SQLEXPRESS;'
                      'Database=store;'
                      'Trusted_Connection=yes;')
cursor = conn.cursor()

SALUDOS_INPUTS = (
    "hola", "buenas", "saludos", "qué tal", "hey", "buenos dias", "klk", "buenas tardes", "buenas noches", "dime a ver")

SALUDOS_OUTPUTS = ["ROBOT: Hola", "ROBOT: Hola, ¿Qué tal?", "ROBOT Hola, ¿Cómo te puedo ayudar?",
                   "ROBOT: Hola, encantado de hablar contigo", "ROBOT: Buenas, ¿Cómo le puedo servir?", "ROBOT: klk",
                   "ROBOT: Dime a ver", "ROBOT: ¿En qué te puedo ayudar?"]

DESPEDIDA_OUTPUTS = ["ROBOT: No hay de qué", "ROBOT: Con mucho gusto", "ROBOT: De nada", "ROBOT: Le estaré esperando",
                     "ROBOT: Vuelva pronto"]

total_price = 0;


def getLemerTokens():
    file = open(r'store.txt', 'r', errors='ignore')
    raw = file.read()
    raw = raw.lower()
    sent_tokens = nltk.sent_tokenize(raw)
    word_tokens = nltk.word_tokenize(raw)
    lemmer = nltk.stem.WordNetLemmatizer()
    return lemmer


def LemTokens(tokens):
    lemmer = getLemerTokens()
    return [lemmer.lemmatize(token) for token in tokens]


def LemNormalize(text):
    remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)
    return LemTokens(nltk.word_tokenize(text.lower().translate(remove_punct_dict)))


def saludos(sentence):
    for word in sentence.split():
        if word.lower() in SALUDOS_INPUTS:
            return random.choice(SALUDOS_OUTPUTS)


@bot.message_handler(["help", "start"])
def send_message(message):
    greeting = 'ROBOT: Si necesitas ayuda puedes consultarla con nuestros creadores Randy, Robert, Frambel usando el siguiente numero de telefono:\n\n 849-858-2406'
    bot.reply_to(message, "Hello, How are you? 🙋🏻‍♀️")


@bot.message_handler(commands=["get_info"])
def start_ask(message):
    markup = ForceReply()
    text = "Para realizar compras en nuestro sistema debe de proporcionarnos algunos datos personales.\n\nCúal es tu número telefónico."
    msg = bot.reply_to(message, text, reply_markup=markup)
    bot.register_next_step_handler(msg, ask_phone_number)


def ask_phone_number(message):
    USER_DATA[message.chat.id] = {}
    USER_DATA[message.chat.id]["phone"] = message.text
    markup = ForceReply()
    msg = bot.send_message(message.chat.id, "¿Cuál es tu correo electrónico?", reply_markup=markup)
    bot.register_next_step_handler(msg, ask_email)


def ask_email(message):
    USER_DATA[message.chat.id]["email"] = message.text
    markup = ReplyKeyboardMarkup()
    text = f'Muchas Gracias {message.from_user.first_name} {message.from_user.last_name}\n A continuación te ' \
           f'mostraremos nuestro catálogo de películas'
    msg = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    bot.register_next_step_handler(msg, get_movies)


def save_user_data(message):
    USER_DATA[message.chat.id]["sex"] = message.text
    text = "Datos Introducidos: \n"
    text += f'<code>Nombre: {USER_DATA[message.chat.id]["name"]}</code>\n'
    text += f'<code>Número telefónico: {USER_DATA[message.chat.id]["phone"]}</code>\n'
    text += f'<code>Sexo: {USER_DATA[message.chat.id]["sex"]}</code>\n'
    bot.send_message(message.chat.id, text, parse_mode="html")


def get_photo(title):
    url = "https://imdb-api.com/en/API/SearchMovie/{IMDB_API_KEY}/{title}".format(IMDB_API_KEY=IMDB_API_KEY,
                                                                                  title=title)
    response = requests.get(url)
    data = response.json()
    image = data["results"][0]["image"]
    return image


def get_movies(message):
    query = "SELECT TOP 2 * FROM movies ORDER BY id;"
    movies = pd.read_sql_query(query, conn)
    for index, row in movies.iterrows():
        text = f'Información sobre {row["title"]}: \n'
        text += f'<b>Fecha de estreno: {row["release_date"]}</b>\n'
        text += f'<b>Precio: ${row["price"]}</b>\n'
        text += f'<b>Descripción: {row["overview"]}</b>\n'
        button = InlineKeyboardButton(text=f'🛒 Agregar película {row["title"]} carrito',
                                      callback_data=f'{row["id"]},{message.chat.id}')
        reply_markup = InlineKeyboardMarkup(
            [[button]]
        )
        bot.reply_to(message, text, parse_mode="HTML", reply_markup=reply_markup)


def shop_movie(chat_id, title, price):
    global total_price
    total_price += price
    text = f'Haz agregado la película {title}\nEl precio es de ${price}.00\nEl precio total es de ${total_price}.00'
    bot.send_message(chat_id, text, parse_mode="html")


def get_movie(data):
    movie_id, chat_id = data.split(",")
    query = "SELECT * FROM movies WHERE id = {id};".format(id=movie_id)
    movie = pd.read_sql_query(query, conn)
    title = movie["title"].values[0]
    price = movie["price"].values[0]
    shop_movie(chat_id, title, price)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    get_movie(call.data)


print("Welcome to the bot")
bot.set_my_commands([
    telebot.types.BotCommand(command="/start", description="Iniciar el bot"),
    telebot.types.BotCommand(command="/get_info", description="Pedir la informaciones de contacto del usuario"),
])
bot.infinity_polling()
# get_movie("11,1")
print("Goodbye")
