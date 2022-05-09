from easyinput import read
import os
from city import find_path, load_city_graph, plot_path
from restaurants import find_restaurants, read_restaurants
from staticmap import StaticMap, CircleMarker
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


def start(update, context):
    """ Envia un missatge de benvinguda a l'usuari """
    context.bot.send_message(chat_id = update.effective_chat.id, text = "Hola!👋🏼 Soc el bot que et porta a menjar en metro, on vols menjar avui ?")


def help(update, context):
    """ Envia un missatge d'ajuda amb totes les comandes disponibles """
    context.bot.send_message(chat_id = update.effective_chat.id, text = "Introdueix alguna de les següents comandes: \n"
    "- /start inicia la conversa \n"
    "- /author mostra els autors del projecte \n"
    "- /find <query> busca quins restaurants satisfan la cerca feta \n"
    "- /info <numero> mostra la informació del restaurant especificat pel seu numero \n"
    "- /guide <numero> mostra el camí més curt \n")

def author(update, context):
    """ Envia un missatge informant de qui són els creadors del projecte en qüestió """
    context.bot.send_message(chat_id = update.effective_chat.id, text = "Els meus creadors són la Carlota Gozalbo i el Marc Camps")

    """ Pre: només sortiràn els 12 primers restaurants que s'afegeixin a la llista """
def find(update, context):
    """ Donada una cerca , envia un missatge de tipus enumeració amb tots els restaurants que la satisfan """
    # Obtenim la query a partir del que ha rebut el bot després de la comanda /find
    query: str = context.args[0]
    # Notifiquem a l'usuari amb tots els restaurants que s'han trobat.
    context.bot.send_message(chat_id = update.effective_chat.id, text = "Aquests són els restaurants que he trobat: \n")
    restaurants: Restaurants = read_restaurants()
    desired_restaurants : Restaurants = find_restaurants(query, restaurants)
    context.user_data['desired_restaurants'] = desired_restaurants
    qty_rest = len(desired_restaurants)
    # Notifiquem per pantalla tots els restaurants trobats.
    for i in range(0, qty_rest):
        context.bot.send_message(chat_id = update.effective_chat.id, text = str(i+1)+ "-" +str(desired_restaurants[i].name) + "\n")

""" Pre: la comanda ha de ser de la forma: /info <int>, on l'enter és un nombre entre len(desired_restaurants) i 1 ambdós inclosos. """
def info(update, context):
    """ Imprimeix per pantalla tot un seguit d'atributs del restaurant que s'indiqui """
    desired_restaurants = context.user_data['desired_restaurants']
    position: int = int(context.args[0]) # posició del restaurant que volem trobar els atributs.

    # Ordenem l'informació del restaurant en qüestió per fer l'impressió del missatge més nítida.
    desired_restaurant = desired_restaurants[position-1]
    name = desired_restaurant.name
    direction = str(desired_restaurant.street_name) + " " + str(int(desired_restaurant.street_number))
    neighbourhood = desired_restaurant.neighbourhood
    district = desired_restaurant.district

    # Disenyem el missatge que volem que s'efectui per pantalla
    context.bot.send_message(chat_id = update.effective_chat.id, text = "Aquests són els atributs del restaurant que m'has demanat\n"
    + "Nom : "+ str(name)+ "\n"
    + "Direcció : "+ str(direction)+ "\n"
    + "Veïnat : "+ str(neighbourhood)+ "\n"
    + "Districte : "+ str(district)+ "\n"
    )

def guide(update, context):
    """ Imprimeix la guia des del punt on es troba l'usuari al restaurant al que vol anar """
    desired_restaurants = context.user_data['desired_restaurants']
    position : int = int(context.args[0])

    # Obtenim les coordenades d'on es troba el restaurant en qüestió
    desired_restaurant = desired_restaurants[position-1]
    x_coord = desired_restaurant.x_coord
    y_coord = desired_restaurant.y_coord
    orig_coords = [y_coord, x_coord]       # Conveni dels altres moduls.
    dst_coords = context.user_data['dst_coords']


    # Obtenim el City_Graph i la ruta des d'on es troba l'usuari fins al restaurant desitjat.
    City_Graph = load_city_graph('city_graf.dat')
    path = find_path(City_Graph,dst_coords ,orig_coords)
    plot_path(City_Graph, path) # Obtenim una imatge "path.png" de la ruta a seguir.

    # Enviem aquesta imatge "path.png" al bot per a que la mostri per pantalla.
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=open("path.png", 'rb'))

def where(update, context):
    """ Quan l'usuari envia la seva ubicació, l'emmagatzema """
    lat, lon = update.message.location.latitude, update.message.location.longitude
    context.user_data['dst_coords'] = [lon,lat]


# Guardem a un fitxer de tipus txt el token per a tal de poder modificar i configurar el bot.
TOKEN = open('token.txt').read().strip()

# Inicialitzem l'updater i el dispatcher.
updater = Updater(token = TOKEN, use_context = True)
dispatcher = updater.dispatcher

# Vinculem les comandes amb les funcions que han d'invocar cada una de les comandes
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('author', author))
dispatcher.add_handler(CommandHandler('find', find))
dispatcher.add_handler(CommandHandler('info', info))
dispatcher.add_handler(MessageHandler(Filters.location, where))
dispatcher.add_handler(CommandHandler('guide', guide))

# Engegem el bot. 
updater.start_polling()
updater.idle()
