from easyinput import read
import os
from city import find_path, load_city_graph, plot_path, get_time_path
from restaurants import find_restaurants, read_restaurants
from staticmap import StaticMap, CircleMarker
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Obtenim el graf de la ciutat de Barcelona (Metro i carrers).
# En cas de tenir-lo ja en un fitxer guardat, l'accedeix. En cas contrari el descarrega.
City_Graph = load_city_graph('city_graf.dat')

# Inicialitzem el temps a -1
def initialize(update,context):
    """ Inicialitza les dades per poder comprovar si s'han efectuat comandes o no de qualsevol tipus """
    context.user_data['travel_time'] = -1
    context.user_data['desired_restaurants'] = -1

def start(update, context):
    """ Envia un missatge de benvinguda a l'usuari i inicialitza el context"""
    initialize(update,context)
    context.bot.send_message(chat_id = update.effective_chat.id, text = "Hola!👋🏼 \n "
    "Soc el bot que et porta a menjar en metro, on vols menjar avui ?")

def help(update, context):
    """ Envia un missatge d'ajuda amb totes les comandes disponibles """
    context.bot.send_message(chat_id = update.effective_chat.id, text = "Introdueix alguna de les següents comandes: \n"
    "- ✅ /start inicia la conversa \n"
    "- ✏️ /author mostra els autors del projecte \n"
    "- 🔎 /find <query> busca quins restaurants satisfan la cerca feta al camp query \n"
    "- 📝 /info <number> mostra la informació del restaurant especificat pel seu numero a la llista de restaurants impresa amb la comanda find \n"
    "- 👣 /guide <number> mostra el camí més curt des d'on et trobes fins al restaurant especificat pel seu nombre  a la llista de restaurants impresa amb la comanda find\n"
    "- ⏳ /travel_time mostra el temps de ruta de l'ultima ruta que s'ha efectuat amb la comanda /guide <number> \n")

def author(update, context):
    """ Envia un missatge informant de qui són els creadors del projecte en qüestió """
    context.bot.send_message(chat_id = update.effective_chat.id, text = "Els meus creadors són la Carlota Gozalbo i el Marc Camps")

    """ Pre: només sortiràn els 12 primers restaurants que s'afegeixin a la llista """
def find(update, context):
    """ Donada una cerca , envia un missatge de tipus enumeració amb tots els restaurants que la satisfan """
    # Obtenim la query a partir del que ha rebut el bot després de la comanda /find
    query: str = context.args[0]
    # Notifiquem a l'usuari amb tots els restaurants que s'han trobat.
    restaurants: Restaurants = read_restaurants()
    desired_restaurants : Restaurants = find_restaurants(query, restaurants)
    context.user_data['desired_restaurants'] = desired_restaurants
    if len(desired_restaurants) == 0:
        context.bot.send_message(chat_id = update.effective_chat.id, text = "No he trobat cap restaurant amb aquest nom! 😭 \n")
    else:
        context.bot.send_message(chat_id = update.effective_chat.id, text = "Aquests són els restaurants que he trobat: \n")
        qty_rest = len(desired_restaurants)
        # Notifiquem per pantalla tots els restaurants trobats.
        for i in range(0, qty_rest):
            context.bot.send_message(chat_id = update.effective_chat.id, text = str(i+1)+ "-" +str(desired_restaurants[i].name) + "\n")

        context.bot.send_message(chat_id = update.effective_chat.id,
        text = "\n Recorda que per a fer servir la comanda /guide <number> primer has d'haver compartit la teva ubicació \n")


""" Pre: la comanda ha de ser de la forma: /info <int>, on l'enter és un nombre entre len(desired_restaurants) i 1 ambdós inclosos. """
def info(update, context):
    """ Imprimeix per pantalla tot un seguit d'atributs del restaurant que s'indiqui """

    desired_restaurants = context.user_data['desired_restaurants']
    position: int = int(context.args[0]) # posició del restaurant que volem trobar els atributs.
    # Si la llista de restaurants encara és buida
    if desired_restaurants == -1:
        context.bot.send_message(chat_id = update.effective_chat.id, text = "La llista de resultats encara és buida,"
        "primer busca restaurants que t'interessin i després ja em consultaràs la seva informació! 😭 \n")
    # Si el restaurant que rebem de l'usuari no compleix la precondició, l'advertim.
    elif 1 > position or position > len(desired_restaurants):
        context.bot.send_message(chat_id = update.effective_chat.id, text = "Aquest nombre no pertany a cap dels restaurants de la llista! 😭 \n")
    else:
        # Altrament, procedim a obtenir i imprimir els atributs del restaurant.
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

""" Pre: l'usuari s'ha de trobar a Barcelona. """
# Nota: Si l'usuari no està a Barcelona, la primera aresta des del punt d'origen no tindrà sentit.
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

    # Obtenim la ruta des d'on es troba l'usuari fins al restaurant desitjat.
    path = find_path(City_Graph,dst_coords ,orig_coords)
    plot_path(City_Graph, path) #Obtenim una imatge "path.png" de la ruta a seguir.
    context.user_data['travel_time'] = get_time_path(path, City_Graph)
    # Enviem aquesta imatge "path.png" al bot per a que la mostri per pantalla.
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=open("path.png", 'rb'))

def where(update, context):
    """ Quan l'usuari envia la seva ubicació, l'emmagatzema """
    lat, lon = update.message.location.latitude, update.message.location.longitude
    context.user_data['dst_coords'] = [lon,lat]

def time(update, context):
    if context.user_data['travel_time'] == -1 :
        context.bot.send_message(chat_id = update.effective_chat.id, text = "Encara no s'ha calculat cap ruta com per calcular el temps de ruta! 😭 \n")
    else:
        travel_time = context.user_data['travel_time']
        context.bot.send_message(chat_id = update.effective_chat.id, text = "El temps de ruta aproximat és de " +str(round(travel_time/60))+" min(s)\n")


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
dispatcher.add_handler(CommandHandler('travel_time', time))

# Engegem el bot.
updater.start_polling()
updater.idle()
