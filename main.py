import random
import os
import random
import string
import smtplib
import uuid
import threading
import nltk
import pandas as pd
import pyodbc
import requests
import telebot
import pickle
from datetime import datetime
from email.message import EmailMessage
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup

N_RES_PAGE = 5
MAXIMUM_WIDTH_OF_BUTTONS = 8
USER_DATA = {}
SEARCH_HISTORY_FOLDER = "./search_history/"

if not os.path.exists(SEARCH_HISTORY_FOLDER):
    os.makedirs(SEARCH_HISTORY_FOLDER)

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

total_price = 0
movies_rented = []


def reset_global_variables():
    global total_price
    global movies_rented
    total_price = 0
    movies_rented = []


def send_email(chat_id):
    user = get_user_data(chat_id)
    global total_price
    email_smtp = "smtp.gmail.com"
    email_port = 587
    message['Subject'] = "Confirmación de renta de películas"
    message['From'] = EMAIL_ADDERS
    message['To'] = user["email"]
    message.set_content(
        f"Gracias por confiar en nosotros, su renta ha sido realizada con éxito.\n\n Total a pagar: ${total_price}\nLuego de 5 minutos esta acción será irreversible.\n.")

    server = smtplib.SMTP(email_smtp, email_port)
    server.starttls()
    server.login(EMAIL_ADDERS, EMAIL_PASSWORD)
    server.send_message(message)
    server.quit()
    del message['To']


def get_user_data(chat_id):
    query = f"SELECT * FROM users WHERE chat_id = {chat_id};"
    user = pd.read_sql_query(query, conn)
    user = user.iloc[0]
    return user


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
    bot.send_chat_action(message.chat.id, "typing")
    greeting = '¡Hola! Soy Belphoebe , tu asistente virtual. \n¿Cómo te puedo ayudar en el día de hoy?  🙋🏻‍♀️'
    bot.reply_to(message, greeting)


@bot.message_handler(commands=["get_info"])
def start_ask(message):
    reset_global_variables()
    if check_if_user_is_registered(message.chat.id):
        bot.send_chat_action(message.chat.id, "typing")
        text = f"Buenos días {message.from_user.first_name}, te recomendaré algunas películas para ti en base a las " \
               f"películas que ya haz alquilado previamente  🙋🏻‍♀️\n "
        bot.send_chat_action(message.chat.id, "typing")
        bot.send_message(message.chat.id, text)

        get_movies(message)
    else:
        markup = ForceReply()
        text = "Para realizar rentas de películas en nuestro sistema debe de proporcionarnos algunos datos " \
               "personales.\n\n¿Cuál es tu número telefónico?"
        bot.send_chat_action(message.chat.id, "typing")
        msg = bot.reply_to(message, text, reply_markup=markup)
        bot.register_next_step_handler(msg, ask_phone_number)


@bot.message_handler(commands=["buy"])
def buy_movie(message):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Tarjeta de crédito", "Efectivo")
    bot.send_chat_action(message.chat.id, "typing")
    msg = bot.reply_to(message, "¿Cómo deseas pagar?", reply_markup=markup)
    bot.register_next_step_handler(msg, ask_payment_method)


def get_movie_price(movie_id):
    query = f"SELECT price FROM movies WHERE id = {movie_id};"
    price = pd.read_sql_query(query, conn)
    price = price.iloc[0]["price"]
    return price


def get_total_invoice_price(invoice_id):
    query = f"SELECT price_total FROM rent WHERE id = '{invoice_id}';"
    price = pd.read_sql_query(query, conn)
    price = price.iloc[0]["price_total"]
    return price


def check_if_user_has_movies_rented(invoice_id):
    query = f"SELECT * FROM rent_details WHERE invoice_id = '{invoice_id}';"
    movies = pd.read_sql_query(query, conn)
    if movies.empty:
        return False
    else:
        return True


def update_invoice_price(invoice_id, movie_price):
    user_has_movies_rented = check_if_user_has_movies_rented(invoice_id)
    if user_has_movies_rented:
        price_total = get_total_invoice_price(invoice_id)
        price_total -= movie_price
        query = f"UPDATE rent SET price_total = {price_total} WHERE id = '{invoice_id}';"
    else:
        query = f"DELETE FROM rent WHERE id = '{invoice_id}';"
    conn.execute(query)
    conn.commit()


def send_alert_message(chat_id, text):
    bot.send_chat_action(chat_id, "typing")
    bot.send_message(chat_id, text)


def remove_movie_from_my_rentals(data, chat_id):
    function_name, invoice_id, movie_id = data.split(",")
    movie_price = get_movie_price(movie_id)
    query = f"DELETE FROM rent_details WHERE invoice_id = '{invoice_id}' AND movie_id = {movie_id};"
    conn.execute(query)
    conn.commit()
    update_invoice_price(invoice_id, movie_price)
    send_alert_message(chat_id, f"Has devuelto la película {movie_id}")


def get_time_left(invoice_id):
    query = f"SELECT date FROM rent WHERE id = '{invoice_id}';"
    date = pd.read_sql_query(query, conn)
    date = date.iloc[0]["date"]
    time_left = 5 - ((datetime.now() - date).total_seconds() / 60.0)
    return "{:.2f}".format(time_left)


def show_my_rented_movies(message, pending_movies_rented):
    bot.send_chat_action(message.chat.id, "typing")
    for index, movie in pending_movies_rented.iterrows():
        movie_title = movie["title"]
        movie_id = movie["movie_id"]
        invoice_id = movie["id"]
        time_left = get_time_left(invoice_id)
        text = f"<b>Tiempo restante para devolver la película:</b> {time_left} minutos\n"
        text += create_message_movie_info(movie)
        cancel_rent_button = InlineKeyboardButton(
            text=f'¿Deseas eliminar la película {movie_title} de tus rentas pendientes?',
            callback_data=f'remove_movie,{invoice_id},{movie_id}')
        reply_markup = InlineKeyboardMarkup(
            [[cancel_rent_button]]
        )
        bot.send_chat_action(message.chat.id, "typing")
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=reply_markup)


def create_message_movie_info(movie, index=None, with_overview=True):
    if index is None:
        text = f'{movie["title"]}: \n'
    else:
        text = f'{index} - {movie["title"]}: \n'
    if with_overview:
        text += f'{movie["overview"][0:300]}...\n'
    text += f'<b>Título original: {movie["original_title"]}</b>\n'
    text += f'<b>Precio: ${movie["price"]}</b>\n'
    text += f'<b>Fecha de estreno:</b> {movie["release_date"]}\n'
    text += f'<b>Puntuación IMDB:</b> {round(movie["vote_average"], 1)}\n'
    if movie["homepage"] is not None:
        text += f'<b>Página Web:</b> <a href="{movie["homepage"]}">{movie["homepage"]}</a>'
    return text + "\n\n"


@bot.message_handler(commands=["check_my_rented_movies"])
def check_my_rented_movies(message):
    query = f"SELECT * FROM view_pending_rented_movies({message.chat.id});"
    movies = pd.read_sql_query(query, conn)
    bot.send_chat_action(message.chat.id, "typing")
    if movies.empty:
        bot.send_message(message.chat.id, "No tienes películas alquiladas por el momento.\nDeseas que te recomiende "
                                          "algunas películas en base a tu historial?")
    else:
        bot.send_message(message.chat.id, "Estas son las películas que tienes alquiladas")
        show_my_rented_movies(message, movies)


def save_rent_movies_details(rent_id):
    global movies_rented
    values = ""
    for movie in movies_rented:
        values += f"('{rent_id}', {movie['id']}, '{movie['price']}'),"
    query = f"INSERT INTO rent_details (invoice_id, movie_id, price) VALUES {values[:-1]};"
    conn.execute(query)
    conn.commit()


def update_invoice_status(invoice_id):
    query = f"UPDATE rent SET status = 0 WHERE id = '{invoice_id}';"
    conn.execute(query)
    conn.commit()


def save_rent_movies(chat_id):
    global total_price
    rent_id = str(uuid.uuid4())[:20]
    query = f"INSERT INTO rent (id, chat_id, price_total) VALUES ('{rent_id}', {chat_id}, {int(total_price)});"
    cursor.execute(query)
    conn.commit()
    time = 60 * 5
    text = f"Has alquilado {len(movies_rented)} películas por un total de ${total_price}.\nLuego de 5 minutos esta " \
           f"acción será irreversible.\nPara poder deshacer la renta, por favor, utilize el siguiente comando " \
           f"/check_my_rented_movies "
    send_alert_message(chat_id, text)
    start_time = threading.Timer(time, update_invoice_status, [rent_id])
    start_time.start()
    save_rent_movies_details(rent_id)


def confirm_rent_movies(message, payment_method):
    global total_price
    if message.text == "✅ Si":
        if payment_method == "Efectivo":
            total_price = total_price - (total_price * 0.1)

        save_rent_movies(message.chat.id)
        bot.send_message(message.chat.id, "Gracias por elegirnos, esperamos que disfrutes tu película 🙆🏻‍♀️")
        send_email(message.chat.id)
    else:
        bot.send_message(message.chat.id, "De nada, le estaré esperando 🙍🏻‍♀️")


def rent_confirmation(message):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("✅ Si", "❌ No")
    bot.send_chat_action(message.chat.id, "typing")
    msg = bot.reply_to(message, "¿Deseas confirmar tu compra?", reply_markup=markup)
    bot.register_next_step_handler(msg, confirm_rent_movies, message.text)


def ask_payment_method(message):
    if message.text != "Tarjeta de crédito" and message.text != "Efectivo":
        bot.send_chat_action(message.chat.id, "typing")
        msg = bot.reply_to(message, "Por favor, ingresa una opción válida.")
        bot.register_next_step_handler(msg, ask_payment_method)
    else:
        rent_confirmation(message)


def ask_phone_number(message):
    USER_DATA[message.chat.id] = {}
    USER_DATA[message.chat.id]["phone"] = message.text
    markup = ForceReply()
    bot.send_chat_action(message.chat.id, "typing")
    msg = bot.send_message(message.chat.id, "¿Cuál es tu correo electrónico?", reply_markup=markup)
    bot.register_next_step_handler(msg, ask_email)


def ask_email(message):
    USER_DATA[message.chat.id]["email"] = message.text
    markup = ReplyKeyboardMarkup()
    text = f'Muchas Gracias {message.from_user.first_name} {message.from_user.last_name}\n A continuación te ' \
           f'mostraremos nuestro catálogo de películas'
    bot.send_chat_action(message.chat.id, "typing")
    msg = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    save_user_data(message.chat.id)
    get_movies(msg)


def save_user_data(chat_id):
    phone = USER_DATA[chat_id]["phone"]
    email = USER_DATA[chat_id]["email"]
    query = f"INSERT INTO users (chat_id, phone, email) VALUES ({chat_id}, '{phone}', '{email}');"
    if check_if_user_is_registered(chat_id) is False:
        cursor.execute(query)
        conn.commit()
    else:
        update_user_data(chat_id, phone, email)


def update_user_data(chat_id, phone, email):
    query = f"UPDATE users SET phone = '{phone}', email = '{email}' WHERE chat_id = {chat_id};"
    cursor.execute(query)
    conn.commit()


def check_if_user_is_registered(chat_id):
    query = f"SELECT * FROM users WHERE chat_id = {chat_id};"
    cursor.execute(query)
    if cursor.fetchone() is None:
        return False
    else:
        return True


def get_movie_photo(title):
    url = "https://imdb-api.com/en/API/SearchMovie/{IMDB_API_KEY}/{title}".format(IMDB_API_KEY=IMDB_API_KEY,
                                                                                  title=title)
    response = requests.get(url)
    data = response.json()
    image = data["results"][0]["image"]
    return image


def get_movies(message):
    query = f"SELECT TOP 100 * FROM movies ORDER BY release_date DESC;"
    movies = pd.read_sql_query(query, conn)
    show_movies(message.chat.id, movies)


def get_movie_info(chat_id, movie_id, show_recommend_button=True):
    query = f"SELECT * FROM movies WHERE id = {movie_id};"
    movie = pd.read_sql_query(query, conn)
    movie = movie.iloc[0]
    text = create_message_movie_info(movie)
    movie_id = movie["id"]
    rent_movie_button = InlineKeyboardButton(text=f'🛒 Rentar película ', callback_data=f'rent_movie,{movie_id}')
    recommend_movie_button = InlineKeyboardButton(text=f'🔍 Recomendar película',
                                                  callback_data=f'recommend_movie,{movie_id}')
    if show_recommend_button:
        reply_markup = InlineKeyboardMarkup(
            [[rent_movie_button, recommend_movie_button]]
        )
    else:
        reply_markup = InlineKeyboardMarkup(
            [[rent_movie_button]]
        )
    bot.send_chat_action(chat_id, "typing")
    # image = get_movie_photo(movie["title"])
    # bot.send_photo(chat_id, image, caption=text, parse_mode="HTML", reply_markup=reply_markup)
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=reply_markup)


def rent_movie(chat_id, movie):
    global total_price
    global movies_rented
    movie_id = movie["id"].values[0]
    title = movie["title"].values[0]
    price = movie["price"].values[0]
    release_date = movie["release_date"].values[0]
    year = int(release_date.split("-")[0])
    release_date = datetime.strptime(release_date, "%Y-%m-%d")
    is_between_2016_and_2017 = 2016 <= year <= 2017
    is_fifty_year_old = (datetime.now() - release_date).days >= 365 * 50
    bot.send_chat_action(chat_id, "typing")
    if is_between_2016_and_2017:
        bot.send_message(chat_id,
                         f"Nota: La película {title} es considerada un estreno por lo que se cobrará 200 pesos "
                         f"a su compra 🙆🏻‍♀️")
        total_price += 200
    if is_fifty_year_old:
        bot.send_message(chat_id, "Lo sentimos, no se puede rentar una película de hace más de 50 años 🙍🏻‍♀️")
        return

    total_price += int(price)
    movies_rented.append({'id': movie_id, 'price': price})
    text = f'Haz agregado la película {title}\nEl precio es de ${price}.\nEl precio total es de ${total_price}.00' \
           f'\nPara finalizar el proceso utiliza el comando /buy'
    bot.send_chat_action(chat_id, "typing")
    bot.send_message(chat_id, text, parse_mode="html")


def get_movie(data):
    movie_id, chat_id = data.split(",")
    query = "SELECT * FROM movies WHERE id = {id};".format(id=movie_id)
    movie = pd.read_sql_query(query, conn)
    rent_movie(chat_id, movie)


def recommend_movie(data, chat_id):
    _, movie_id = data.split(",")
    query = "SELECT TOP 4 id FROM movies ORDER BY popularity DESC;"
    movies = pd.read_sql_query(query, conn)
    for index, row in movies.iterrows():
        get_movie_info(chat_id, row["id"], show_recommend_button=False)


def show_movies(chat_id, movies, page=0, message_id=None):
    markup = InlineKeyboardMarkup(row_width=MAXIMUM_WIDTH_OF_BUTTONS)
    previous_button = InlineKeyboardButton(text="⬅️", callback_data=f"previous_button,{page}")
    next_button = InlineKeyboardButton(text="➡️", callback_data=f"next_button,{page}")
    close_button = InlineKeyboardButton(text="❌", callback_data=f"close_button,{page}")

    start = page * N_RES_PAGE
    end = start + N_RES_PAGE
    text = f"<i><b>Página {start + 1} - {end} de {len(movies)}</b></i>\n\n"
    buttons = []
    for index, movie in movies[start:end].iterrows():
        buttons.append(InlineKeyboardButton(text=str(index + 1), callback_data=f"get_movie_info,{movie['id']}"))
        text += create_message_movie_info(movie, index + 1, with_overview=False)
    markup.add(*buttons)
    markup.row(previous_button, close_button, next_button)
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup,
                              disable_web_page_preview=True)
    else:
        response = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup,
                                    disable_web_page_preview=True)
        message_id = response.message_id
        data = {"page": 0, "movies": movies}
        pickle.dump(data, open(f"{SEARCH_HISTORY_FOLDER}{chat_id}_{message_id}.text", "wb"))


@bot.callback_query_handler(lambda call: call.data.startswith("get_movie_info"))
def handler_get_movie_info(call):
    chat_id = call.from_user.id
    movie_id = call.data.split(",")[1]
    get_movie_info(chat_id, movie_id)


@bot.callback_query_handler(lambda call: call.data.startswith("rent_movie"))
def handler_rent_movie(call):
    chat_id = call.from_user.id
    movie_id = call.data.split(",")[1]
    query = f"SELECT * FROM movies WHERE id = {movie_id};"
    movie = pd.read_sql_query(query, conn)
    rent_movie(chat_id, movie)


@bot.callback_query_handler(lambda call: call.data.startswith("previous_button"))
def handler_previous_button(call):
    chat_id = call.from_user.id
    message_id = call.message.message_id
    data = pickle.load(open(f"{SEARCH_HISTORY_FOLDER}{chat_id}_{message_id}.text", "rb"))
    is_first_page = data["page"] == 0
    if is_first_page:
        bot.answer_callback_query(call.id, "No puedes retroceder más")
    else:
        data["page"] -= 1
        movies = data["movies"]
        pickle.dump(data, open(f"{SEARCH_HISTORY_FOLDER}{chat_id}_{message_id}.text", "wb"))
        show_movies(chat_id, movies, data["page"], message_id)
    return


@bot.callback_query_handler(lambda call: call.data.startswith("next_button"))
def handler_next_button(call):
    chat_id = call.from_user.id
    message_id = call.message.message_id
    data = pickle.load(open(f"{SEARCH_HISTORY_FOLDER}{chat_id}_{message_id}.text", "rb"))
    is_last_page = data["page"] * N_RES_PAGE + N_RES_PAGE >= len(data["movies"])
    if is_last_page:
        bot.answer_callback_query(call.id, "No puedes avanzar más")
    else:
        data["page"] += 1
        movies = data["movies"]
        pickle.dump(data, open(f"{SEARCH_HISTORY_FOLDER}{chat_id}_{message_id}.text", "wb"))
        show_movies(chat_id, movies, data["page"], message_id)
    return


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.from_user.id
    message_id = call.message.id
    if call.data.startswith("remove_movie"):
        remove_movie_from_my_rentals(call.data, chat_id)
    elif call.data.startswith("recommend_movie"):
        recommend_movie(call.data, chat_id)
    elif call.data.startswith("get_movie_info"):
        get_movie_info(chat_id, call.data.split(",")[1])
    elif call.data.startswith("close"):
        bot.delete_message(chat_id, message_id)
        return
    elif call.data.startswith("stop"):
        bot.stop_polling()


print("Welcome to the bot")
bot.set_my_commands([
    telebot.types.BotCommand(command="/start", description="Iniciar el bot"),
    telebot.types.BotCommand(command="/get_info", description="Pedir la informaciones de contacto del usuario"),
    telebot.types.BotCommand(command="/check_my_rented_movies", description="Ver las películas que has rentado"),
])
bot.infinity_polling()

print("Goodbye")
