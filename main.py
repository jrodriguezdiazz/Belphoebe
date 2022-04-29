import json
import os
import random
import string
import smtplib
from email.message import EmailMessage
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
CHAT_ID = os.getenv('CHAT_ID')

bot = telebot.TeleBot(BOT_KEY)
message = EmailMessage()
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


def send_email(chat_id):
    global total_price
    email_smtp = "smtp.gmail.com"
    email_port = 587
    message['Subject'] = "Confirmación de compra de películas"
    message['From'] = EMAIL_ADDERS
    message['To'] = USER_DATA[chat_id]["email"]
    message.set_content(
        f"Gracias por confiar en nosotros, su compra ha sido realizada con éxito.\n\n Total a pagar: ${total_price}\n\n ")

    server = smtplib.SMTP(email_smtp, email_port)
    server.starttls()
    server.login(EMAIL_ADDERS, EMAIL_PASSWORD)
    server.send_message(message)
    server.quit()
    del message['To']


def get_lemer_tokens():
    file = open(r'store.txt', 'r', errors='ignore')
    raw = file.read()
    raw = raw.lower()
    sent_tokens = nltk.sent_tokenize(raw)
    word_tokens = nltk.word_tokenize(raw)
    lemmer = nltk.stem.WordNetLemmatizer()
    return lemmer


def lem_tokens(tokens):
    lemmer = get_lemer_tokens()
    return [lemmer.lemmatize(token) for token in tokens]


def lem_normalize(text):
    remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)
    return lem_tokens(nltk.word_tokenize(text.lower().translate(remove_punct_dict)))


def saludos(sentence):
    for word in sentence.split():
        if word.lower() in SALUDOS_INPUTS:
            return random.choice(SALUDOS_OUTPUTS)


@bot.message_handler(["help", "start"])
def send_message(message):
    greeting = '¡Hola! Soy Belphoebe , tu asistente virtual. \n¿Cómo te puedo ayudar en el día de hoy?  🙋🏻‍♀️'
    bot.reply_to(message, greeting)


@bot.message_handler(commands=["get_info"])
def start_ask(message):
    markup = ForceReply()
    text = "Para realizar compras en nuestro sistema debe de proporcionarnos algunos datos personales.\n\n¿Cuál es tu " \
           "número telefónico?"
    msg = bot.reply_to(message, text, reply_markup=markup)
    bot.register_next_step_handler(msg, ask_phone_number)


@bot.message_handler(commands=["buy"])
def buy_movie(message):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Tarjeta de crédito", "Efectivo")
    msg = bot.reply_to(message, "¿Cómo deseas pagar?", reply_markup=markup)
    bot.register_next_step_handler(msg, ask_payment_method)


def ask_payment_method(message):
    global total_price
    if message.text != "Tarjeta de crédito" and message.text != "Efectivo":
        msg = bot.reply_to(message, "Por favor, ingresa una opción válida.")
        bot.register_next_step_handler(msg, ask_payment_method)
    else:
        if message.text == "Efectivo":
            total_price = total_price - (total_price * 0.1)
        send_email(message.chat.id)
        bot.reply_to(message,
                     f"Gracias por confiar en nosotros, su compra ha sido realizada con éxito.\n\n Total a pagar: ${total_price}\n\n ")


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


def get_movie_photo(title):
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
        text += f'<b>Precio: ${row["price"]}</b>\n'
        button = InlineKeyboardButton(text=f'🎥 Ver detalles de {row["title"]} ',
                                      callback_data=f'get_movie_info,{message.chat.id},{row["id"]}')
        reply_markup = InlineKeyboardMarkup(
            [[button]]
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=reply_markup)


def get_movie_info(chat_id, movie_id):
    query = f"SELECT * FROM movies WHERE id = {movie_id};"
    movie = pd.read_sql_query(query, conn)
    movie = movie.iloc[0]
    text = f'Información sobre {movie["title"]}: \n'
    text += f'<b>Título original: {movie["original_title"]}</b>\n'
    text += f'<b>Precio: ${movie["price"]}</b>\n'
    text += f'<b>Fecha de estreno:</b> {movie["release_date"]}\n'
    text += f'<b>Puntuación IMDB:</b> {movie["vote_average"]}%\n'
    text += f'<b>Sinopsis:</b>\n'
    text += f'{movie["overview"][0:100]}...\n'
    if movie["homepage"] is not None:
        text += f'<b>Página Web:</b> <a href="{movie["homepage"]}">Ver página web</a>'

    # image = get_movie_photo(movie["title"])
    # bot.send_photo(chat_id, image, caption=text, parse_mode="HTML")

    shop_movie_button = InlineKeyboardButton(text=f'🎥 Comprar película ',
                                             callback_data=f'shop_movie,{chat_id},{movie["title"]},{movie["price"]}')
    recommend_movie_button = InlineKeyboardButton(text=f'🎥 Recomendar película ',
                                                  callback_data=f'recommend_movie,{movie["id"]}')
    reply_markup = InlineKeyboardMarkup(
        [[shop_movie_button, recommend_movie_button]]
    )
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=reply_markup)


def shop_movie(chat_id, title, price):
    global total_price
    total_price += int(price)
    text = f'Haz agregado la película {title}\nEl precio es de ${price}.\nEl precio total es de ${total_price}.00' \
           f'\nPara finalizar la compra utiliza el comando /buy '
    bot.send_message(chat_id, text, parse_mode="html")


def get_movie(data):
    movie_id, chat_id = data.split(",")
    query = "SELECT * FROM movies WHERE id = {id};".format(id=movie_id)
    movie = pd.read_sql_query(query, conn)
    title = movie["title"].values[0]
    price = movie["price"].values[0]
    shop_movie(chat_id, title, price)


def recommend_movie(data):
    pass


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith("get_movie_info"):
        get_movie_info(call.data.split(",")[1], call.data.split(",")[2])
    elif call.data.startswith("shop_movie"):
        shop_movie(call.data.split(",")[1], call.data.split(",")[2], call.data.split(",")[3])
    elif call.data.startswith("recommend_movie"):
        recommend_movie(call.data)


print("Welcome to the bot")
bot.set_my_commands([
    telebot.types.BotCommand(command="/start", description="Iniciar el bot"),
    telebot.types.BotCommand(command="/get_info", description="Pedir la informaciones de contacto del usuario"),
])
bot.infinity_polling()

print("Goodbye")
