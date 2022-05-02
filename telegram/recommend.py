import pandas as pd
import json
import warnings

warnings.filterwarnings('ignore')
from scipy import spatial
import operator

# Dependencias utilizadas para los graficos vv
# import base64
# import io
# from matplotlib.pyplot import imread
# import codecs
# from IPython.display import HTML
# from wordcloud import WordCloud, STOPWORDS
# import nltk
# from nltk.corpus import stopwords
# import matplotlib.pyplot as plt
# plt.style.use('fivethirtyeight')
# import seaborn as sns
# import numpy as np
# nltk.download('stopwords')
# nltk.download('punkt')


movies = pd.read_csv('tmdb_5000_movies.csv')
credits = pd.read_csv('tmdb_5000_credits.csv')
print('+---------------------------------------+')


# F U N C I O N E S
# P R I N C I P A L E S
def cambiar_json_a_string(df, columna):
    df[columna] = df[columna].apply(json.loads)
    for index, i in zip(df.index, df[columna]):
        list1 = []
        for j in range(len(i)):
            list1.append((i[j]['name']))  # la llave 'name' contiene el nombre de la columna
        df.loc[index, columna] = str(list1)
    return df[columna]


def encontrar_repetidos(original_list, unique_attr_list):
    binaryList = []
    for item in unique_attr_list:
        if item in original_list:
            binaryList.append(1)
        else:
            binaryList.append(0)
    return binaryList


def reemplazar_string_vacio(s):
    if s is None:
        return ''
    return str(s)


def similarity(movieId1, movieId2):
    a = movies.iloc[movieId1]
    b = movies.iloc[movieId2]

    genresA = a['genres_bin']
    genresB = b['genres_bin']

    genreDistance = spatial.distance.cosine(genresA, genresB)

    scoreA = a['cast_bin']
    scoreB = b['cast_bin']
    scoreDistance = spatial.distance.cosine(scoreA, scoreB)

    directA = a['director_bin']
    directB = b['director_bin']
    directDistance = spatial.distance.cosine(directA, directB)

    wordsA = a['words_bin']
    wordsB = b['words_bin']
    wordsDistance = spatial.distance.cosine(directA, directB)
    return genreDistance + directDistance + scoreDistance + wordsDistance


def predict_movie(name):
    new_movie = movies[movies['original_title'].str.contains(name)].iloc[0].to_frame().T
    print('Selected Movie: ', new_movie.original_title.values[0])

    def getNeighbors(baseMovie, K):
        distances = []

        for index, movie in movies.iterrows():
            if movie['new_id'] != baseMovie['new_id'].values[0]:
                dist = similarity(baseMovie['new_id'].values[0], movie['new_id'])
                distances.append((movie['new_id'], dist))

        distances.sort(key=operator.itemgetter(1))
        neighbors = []

        for x in range(K):
            neighbors.append(distances[x])
        return neighbors

    K = 10
    avgRating = 0
    neighbors = getNeighbors(new_movie, K)
    result = []
    for neighbor in neighbors:
        movie = movies.iloc[neighbor[0]][0].replace("'", "''")
        result.append(movie)
    return result
    # print('\n')
    # avgRating = avgRating / K
    # print('Puntaje predecido %s es: %f' % (new_movie['original_title'].values[0], avgRating))
    # print('Puntaje real %s es %f' % (new_movie['original_title'].values[0], new_movie['vote_average']))


# -------------------------------------------------------- #
# Despues de analizar el dataset usando las funciones .head() y .describe(), pudimos observar 
# que los datos de generos, palabras claves, compania y los equipos que trabajaron en las 
# peliculas estan en formato JSON, para facilitar nuestra manipulacion de datos, vamos a 
# transformarlos a strings y mas adelante se transformaran en una lista
movies['genres'] = cambiar_json_a_string(movies, 'genres')
movies['keywords'] = cambiar_json_a_string(movies, 'keywords')
movies['production_companies'] = cambiar_json_a_string(movies, 'production_companies')

credits['cast'] = cambiar_json_a_string(credits, 'cast')
# Este cambio se hace para obtener el nombre del 
# director de la pelicula, y se reemplaza la columna "crew" por una 
# columna "director"
credits['crew'] = credits['crew'].apply(json.loads)


def director(x):
    for i in x:
        if i['job'] == 'Director':
            return i['name']


credits['crew'] = credits['crew'].apply(director)
credits.rename(columns={'crew': 'director'}, inplace=True)

# mezclaremos ambos csv/datagrames con las columnas requeridas
movies = movies.merge(credits, left_on='id', right_on='movie_id', how='left')
movies = movies[['id', 'original_title', 'genres', 'cast', 'vote_average', 'director', 'keywords']]

# MANIPULAR LA COLUMNA "GENEROS"
print('Manipulando la lista de generos...')
movies['genres'] = movies['genres'].str.strip('[]').str.replace(' ', '').str.replace("'", '')
movies['genres'] = movies['genres'].str.split(',')

for i, j in zip(movies['genres'], movies.index):
    list2 = []
    list2 = i
    list2.sort()
    movies.loc[j, 'genres'] = str(list2)

movies['genres'] = movies['genres'].str.strip('[]').str.replace(' ', '').str.replace("'", '')
movies['genres'] = movies['genres'].str.split(',')

# filtrar los generos que no se repiten
genreList = []
for index, row in movies.iterrows():
    genres = row["genres"]

    for genre in genres:
        if genre not in genreList:
            genreList.append(genre)
# Agregar una lista de los unicos en cada pelicula
movies['genres_bin'] = movies['genres'].apply(lambda x: encontrar_repetidos(x, genreList))

# --------------------------------------------
# MANIPULAR LA COLUMNA "CAST"
print('Manipulando los datos del elenco de las peliculas...')
movies['cast'] = movies['cast'].str.strip('[]').str.replace('', '').str.replace("'", '').str.replace('"', '')
movies['cast'] = movies['cast'].str.split(',')

for i, j in zip(movies['cast'], movies.index):
    list2 = []
    list2 = i[:4]
    movies.loc[j, 'cast'] = str(list2)
movies['cast'] = movies['cast'].str.strip('[]').str.replace(' ', '').str.replace("'", '')
movies['cast'] = movies['cast'].str.split(',')
for i, j in zip(movies['cast'], movies.index):
    list2 = []
    list2 = i
    list2.sort()
    movies.loc[j, 'cast'] = str(list2)
movies['cast'] = movies['cast'].str.strip('[]').str.replace(' ', '').str.replace("'", '')

castList = []
for index, row in movies.iterrows():
    cast = row["cast"]

    for i in cast:
        if i not in castList:
            castList.append(i)

movies['cast_bin'] = movies['cast'].apply(lambda x: encontrar_repetidos(x, castList))

# --------------------------------------------
# MANIPULAR LA COLUMNA "DIRECTOR"
print('Manipulando los directores de las peliculas...')
movies['director'] = movies['director'].apply(reemplazar_string_vacio)

directorList = []
for i in movies['director']:
    if i not in directorList:
        directorList.append(i)

movies['director_bin'] = movies['director'].apply(lambda x: encontrar_repetidos(x, directorList))

# --------------------------------------------
# MANIPULAR LA COLUMNA "DIRECTOR"
print('Manipulando las palabras claves...')
movies['keywords'] = movies['keywords'].str.strip('[]').str.replace('', '').str.replace("'", '').str.replace('"', '')
movies['keywords'] = movies['keywords'].str.split(',')
for i, j in zip(movies['keywords'], movies.index):
    list2 = []
    list2 = i
    movies.loc[j, 'keywords'] = str(list2)

movies['keywords'] = movies['keywords'].str.strip('[]').str.replace('', '').str.replace("'", '')
movies['keywords'] = movies['keywords'].str.split(',')
for i, j in zip(movies['keywords'], movies.index):
    list2 = []
    list2 = i
    list2.sort()
    movies.loc[j, 'keywords'] = str(list2)

movies['keywords'] = movies['keywords'].str.strip('[]').str.replace('', '').str.replace("'", '')
movies['keywords'] = movies['keywords'].str.split(',')

words_list = []
for index, row in movies.iterrows():
    keywords = row["keywords"]
    for keyword in keywords:
        if keyword not in words_list:
            words_list.append(keyword)


def binary(words):
    binaryList = []
    for word in words_list:
        if word in words:
            binaryList.append(1)
        else:
            binaryList.append(0)
    return binaryList


# Por alguna razon, utilizar la funcion "encontrar_repetidos" dura demasiado tiempo
# corriendo y hacer una funcion propia para los "keywords" nos ha funcionado
movies['words_bin'] = movies['keywords'].apply(lambda x: binary(x))
movies = movies[(movies['vote_average'] != 0)]  # Remover las peliculas con un puntaje de cero
movies = movies[movies['director'] != '']  # remover las peliculas que no tengan director

new_id = list(range(0, movies.shape[0]))
movies['new_id'] = new_id
movies = movies[
    ['original_title', 'genres', 'vote_average', 'genres_bin', 'cast_bin', 'new_id', 'director', 'director_bin',
     'words_bin']]
print(movies.head()['new_id'])

# G R A F I C A S
# MUESTRA UNA GRAFICA DE LOS GENEROS MAS FAMOSOS
# +---------------------------+
# plt.subplots(figsize=(12,10))
# list1 = []
# for i in movies['genres']:
#     list1.extend(i)
# ax = pd.Series(list1).value_counts()[:10].sort_values(ascending=True).plot.barh(width=0.9,color=sns.color_palette('hls',10))
# for i, v in enumerate(pd.Series(list1).value_counts()[:10].sort_values(ascending=True).values): 
#     ax.text(.8, i, v,fontsize=12,color='white',weight='bold')
# plt.title('Generos mas famosos')
# plt.show()
# +---------------------------+

# GRAFICO DE ACTORES QUE MAS APARECEN EN PELICULAS
# +---------------------------+
# plt.subplots(figsize=(12,10))
# list1=[]
# for i in movies['cast']:
#     list1.extend(i)
# ax=pd.Series(list1).value_counts()[:15].sort_values(ascending=True).plot.barh(width=0.9,color=sns.color_palette('muted',40))
# for i, v in enumerate(pd.Series(list1).value_counts()[:15].sort_values(ascending=True).values): 
#     ax.text(.8, i, v,fontsize=10,color='white',weight='bold')
# plt.title('Actores con mayor cantidad de peliculas actuadas')
# plt.show()
# +---------------------------+

# DIRECTORES CON MAS PELICULAS
# +---------------------------+
# plt.subplots(figsize=(12,10))
# ax = movies[movies['director']!=''].director.value_counts()[:10].sort_values(ascending=True).plot.barh(width=0.9,color=sns.color_palette('muted',40))
# for i, v in enumerate(movies[movies['director']!=''].director.value_counts()[:10].sort_values(ascending=True).values): 
#     ax.text(.5, i, v,fontsize=12,color='white',weight='bold')
# plt.title('Directores con mas peliculas')
# plt.show()
# +---------------------------+

# NUBE DE PALABRAS MAS UTILIZADAS PARA DESCRIBIR LAS PELICULAs
# +---------------------------+
# plt.subplots(figsize=(12,12))
# stop_words = set(stopwords.words('english'))
# stop_words.update(',',';','!','?','.','(',')','$','#','+',':','...',' ','')

# words=movies['keywords'].dropna().apply(nltk.word_tokenize)
# word=[]
# for i in words:
#     word.extend(i)
# word=pd.Series(word)
# word=([i for i in word.str.lower() if i not in stop_words])
# wc = WordCloud(background_color="black", max_words=2000, stopwords=STOPWORDS, max_font_size= 60,width=1000,height=1000)
# wc.generate(" ".join(word))
# plt.imshow(wc)
# plt.axis('off')
# fig=plt.gcf()
# fig.set_size_inches(10,10)
# plt.show()
# +---------------------------+
