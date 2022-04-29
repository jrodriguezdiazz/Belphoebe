import os
import requests
import numpy as np
import pandas as pd
import pyodbc
import telebot
import nltk
import string
import random
from nltk.corpus import stopwords
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, ForceReply
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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


def get_photo(title):
    url = "https://imdb-api.com/en/API/SearchMovie/{IMDB_API_KEY}/{title}".format(IMDB_API_KEY=IMDB_API_KEY,
                                                                                  title=title)
    response = requests.get(url)
    data = response.json()
    image = data["results"][0]["image"]
    return image


@bot.message_handler(commands=["get_movies"])
def get_movies(message):
    query = "SELECT TOP 2 * FROM movies ORDER BY id;"
    movies = pd.read_sql_query(query, conn)
    for index, row in movies.iterrows():
        text = f'Información sobre {row["title"]}: \n'
        text += f'<b>Fecha de estreno: {row["release_date"]}</b>\n'
        text += f'<b>Precio: ${row["price"]}</b>\n'

        bot.send_message(message.chat.id, text, parse_mode="html")


if __name__ == '__main__':
    print("Welcome to the bot")
    bot.set_my_commands([
        telebot.types.BotCommand(command="/start", description="Iniciar el bot"),
        telebot.types.BotCommand(command="/get_movies", description="Obtener la lista de películas")
    ])
    bot.infinity_polling()
    print("Goodbye")
