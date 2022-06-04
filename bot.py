import os
from city import find_path, build_city_graph, plot_path, get_time_path
from city import load_osmnx_graph, Path, CityGraph
from metro import get_metro_graph
from restaurants import find_restaurants, read_restaurants, Restaurant
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from easyinput import read  # type: ignore


# ------------------ VARIABLES GLOBALS ------------------- #
metro_graph = get_metro_graph()
street_graph = load_osmnx_graph('barcelona.grf')
city_graph = build_city_graph(street_graph, metro_graph, False)
city_graph_accessible = build_city_graph(street_graph, metro_graph, True)
# -------------------------------------------------------- #

# --------------------------------- #
# FUNCIONS PER LES COMANDES DEL BOT #
# --------------------------------- #


def initialize(update, context):
    """ Inicialitza les dades per poder comprovar si s'han efectuat comandes
    o no de qualsevol tipus
    """
    context.user_data['travel_time'] = -1
    context.user_data['desired_restaurants'] = []
    context.user_data['accessibility'] = False
    # Inicialment suposem que l'usuari no té preferencia pels accessos.


def accessibility(update, context):
    """ En el cas de que l'usuari ho indiqui, actualitza les preferències
    d'aquest en vers l'accessibilitat
    """
    try:
        indication: str = context.args[0]
        # Assegurem que l'entrada de l'usuari és correcte
        assert indication == "SI" or indication == "NO"
        if indication == "SI":
            context.user_data['accessibility'] = True
        else:
            context.user_data['accessibility'] = False

        msg = "Accessibilitat desitjada actualitzada correctament✅ \n"
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=msg)
    except AssertionError:
        info = ("El text inserit al camp <SI/NO>, no és correcte. Per "
                "actualitzar l'accessibilitat , introdueix SI o NO\n")
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)
    except IndexError:
        info = ("No has inserit cap paraula al camp <SI/NO> \n")
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)


def start(update, context):
    """ Envia missatge de benvinguda a l'usuari i inicialitza el context
    """
    initialize(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hola " +
                             str(update.effective_chat.first_name) + "!👋🏼 \n"
                             + "Soc el bot que et porta a menjar en metro, on"
                             " vols menjar avui?")


def help(update, context):
    """ Envia un missatge d'ajuda amb totes les comandes disponibles """
    info = ("Introdueix alguna de les següents comandes: \n"
            "- ✅ /start inicia la conversa \n"
            "- ✏️ /author mostra els autors del projecte \n"
            "- 🔎 /find <query> busca quins restaurants satisfan la cerca "
            "feta al camp query. En el cas de fer servir cerca multiple amb "
            "n paraules, cal fer servir la següent notació:\n"
            "/find <query(1)>;<query(2)>; ... <query(n-1)>;<query(n)>\n"
            "- 📝 /info <number> mostra la informació del restaurant "
            "especificat pel seu nombre a la llista de restaurants impresa "
            "amb la comanda find \n"
            "- 👣 /guide <number> mostra el camí més curt des d'on et trobes "
            "fins al restaurant especificat pel seu nombre  a la llista de "
            "restaurants impresa amb la comanda find. Rebràs tant una guia "
            "visual com una guia verbal per facilitar-te la ruta \n"
            "- ⏳ /travel_time mostra el temps de ruta de l'última ruta que "
            "s'ha efectuat amb la comanda /guide <number> \n"
            "- /accessibility <SI/NO> indica al bot si l'usuari vol que la "
            "ruta inclogui accessos no accessibles o no. Per exemple: "
            "/accessibility YES indica al bot que l'usuari vol que la ruta "
            "només inclogui accessos accessibles")
    context.bot.send_message(chat_id=update.effective_chat.id, text=info)


def author(update, context):
    """ Envia un missatge informant de qui són els creadors del projecte """
    info = "Els meus creadors són la Carlota Gozalbo i el Marc Camps"
    context.bot.send_message(chat_id=update.effective_chat.id, text=info)


def find(update, context):
    """ Donada una cerca, envia un missatge de tipus enumeració amb els
    primers restaurants que la satisfan (ordenats de més coincidencia a menys)
    Post: la llista pot ser com a màxim de llargada 12.
    """
    try:

        # Obtenim la query a partir del que ha rebut el bot després de /find
        query: str = context.args[0]
        restaurants: Restaurants = read_restaurants()
        desired_restaurants: Restaurants = find_restaurants(query,
                                                            restaurants)
        context.user_data['desired_restaurants'] = desired_restaurants
        # Comprovem que s'hagi trobat algun restaurant
        assert len(desired_restaurants) > 0

        info = "Aquests són els restaurants que he trobat: \n"
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)

        # Notifiquem per pantalla tots els restaurants trobats.
        list: str = ""
        qty_rest: int = min(12, len(desired_restaurants))
        for i in range(0, qty_rest):
            list += str(i+1)+" - "+str(desired_restaurants[i].name)+"\n"
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=list)
        mess = ("\n Recorda que per a fer servir la comanda /guide <number> "
                "primer has d'haver compartit la teva ubicació \n")
        context.bot.send_message(chat_id=update.effective_chat.id, text=mess)

    except IndexError:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="No has inserit cap nom de restaurant "
                                 "al camp <number> de la comanda /find 😭 \n")
    except AssertionError:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="No he trobat cap restaurant que "
                                 "s'ajusti a la teva cerca 😭 \n")


def info(update, context):
    """ Pre: la comanda ha de ser de la forma: /info <int>, on l'enter és un
    nombre entre 1 i len(desired_restaurants) ambdós inclosos

    Imprimeix per pantalla tot un seguit d'atributs del restaurant que
    s'indiqui
    """
    try:
        desired_restaurants: Restaurants = (
            context.user_data['desired_restaurants'])
        # posició del restaurant que volem trobar els atributs
        position: int = int(context.args[0])
        # Comprovem que la llista de restaurants no sigui buida
        assert len(desired_restaurants) > 0
        # Si el restaurant que rebem no compleix la precondició, advertim
        if 1 > position or position > len(desired_restaurants):
            info = ("Aquest nombre no pertany a cap dels restaurants de la "
                    "llista! 😭 \n")
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info)
        else:
            # Altrament, obtenir i imprimir els atributs del restaurant
            # Ordenem la info del restaurant per fer el missatge més clar
            desired_restaurant: Restaurant = desired_restaurants[position-1]
            name: str = desired_restaurant.name
            direction = (str(desired_restaurant.street_name) + " " +
                         str(int(desired_restaurant.street_number)))
            district: str = desired_restaurant.district
            phone: str = desired_restaurant.phone
            neighbourhood: str = desired_restaurant.neighbourhood
            # Si el camp telèfon al csv està buit o no conté telèfon
            if phone == '-' or not isinstance(phone, str):
                phone = "No té telèfon😭"

            # Disenyem el missatge que volem que s'efectui per pantalla
            info = ("Aquests són els atributs del restaurant que m'has "
                    "demanat\n")
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info + "Nom : " + str(name) + "\n"
                                     + "Direcció : " + str(direction) + "\n"
                                     + "Barri : " + str(neighbourhood) + "\n"
                                     + "Districte : " + str(district) + "\n"
                                     + "Telèfon : " + str(phone) + "\n")
    except IndexError:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="No has inserit cap nombre enter "
                                 "després de la comanda /info i per tant no "
                                 "sé quin restaurant vols tafanejar 😭 \n")
    except AssertionError:
        info = ("La llista de resultats encara és buida, primer busca "
                "restaurants que t'interessin i després ja em consultaràs la "
                "seva informació! 😭 \n")
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)


def guide(update, context):
    """ Pre: l'usuari s'ha de trobar a Barcelona i ha d'haver enviat la seva
    localització.
    Imprimeix el camí des del punt on es troba l'usuari al restaurant al
    que vol anar
    """
    # Nota: Si l'usuari no està a Barcelona, la ruta no serà realista
    try:
        desired_restaurants: Restaurants = (
            context.user_data['desired_restaurants'])
        position: int = int(context.args[0])

        # Obtenim les coordenades d'on es troba el restaurant en qüestió
        # i les coordenades d'on es troba l'usuari
        orig_coords: Coord = context.user_data['orig_coords']
        desired_restaurant: Restaurant = desired_restaurants[position-1]
        dst_coords: Coord = [desired_restaurant.y_coord,
                             desired_restaurant.x_coord]

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Calculant la millor ruta ⏰ ...\n")

        filename = (update.effective_chat.first_name +
                    update.effective_chat.last_name + ".png")

        # En funció de l'accessibilitat, ruta des d'on es troba l'usuari
        # fins al restaurant desitjat
        if context.user_data['accessibility']:
            path: Path = find_path(street_graph, city_graph_accessible,
                                   orig_coords, dst_coords)
            plot_path(city_graph_accessible, path, filename, orig_coords,
                      dst_coords)
            context.user_data['travel_time'] = get_time_path(
                path, city_graph_accessible)
            indicate_path(path, city_graph_accessible, update, context)
        else:
            path: Path = find_path(street_graph, city_graph, dst_coords,
                                   orig_coords)
            plot_path(city_graph, path, filename, orig_coords, dst_coords)
            context.user_data['travel_time'] = get_time_path(path, city_graph)
            indicate_path(path, city_graph, update, context)
        # El filename de l'imatge serà el nom i cognom de l'usuari
        # per tal d'evitar colisions entre usuaris
        # Enviem la imatge de la ruta al bot per a que la mostri per pantalla
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open(filename, 'rb'))
        os.remove(filename)

    except KeyError:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Encara no m'has enviat la ubicació "
                                 "😭 \n")
    except IndexError:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="O bé no has escrit res al camp "
                                 "<number> o bé el nombre que hi has escrit "
                                 "no pertany a la llista de "
                                 "restaurants 😭 \n")


def indicate_path(path: Path, g: CityGraph, update, context) -> None:
    """ Donat un camí, notifica l'usuari dels accessos, estacions de sortida,
    i transbords que ha de fer
    """
    len_path: int = len(path)

    info = "1 - Camina pel carrer i espera a la següent indicació \n"
    count: int = 2
    for i in range(1, len_path):

        if g.nodes[path[i]]["type"] == "Street":
            continue
        # Condició per entrar accessos.
        if (g.nodes[path[i]]["type"] == "Access" and
                g.nodes[path[i-1]]["type"] == "Street"):
            info += (str(count) + " - Entra per l'accés: %s \n" %
                     (g.nodes[path[i]]["name"]))
            info += (str(count+1) + " - Agafa el metro a l'estació: %s \n" %
                     (g.nodes[path[i]]["name"]))
            count += 2

        # Condició per a sortir per un access.
        elif (g.nodes[path[i]]["type"] == "Access" and
                g.nodes[path[i-1]]["type"] == "Station"):
            info += (str(count)+" - Ves fins l'estació: %s \n" %
                     (g.nodes[path[i-1]]["name"]))
            info += (str(count+1)+" - Surt per l'accés: %s \n" %
                     (g.nodes[path[i]]["name"]))
            count += 2

        # Condició per a fer transbords
        elif (g.edges[path[i-1], path[i]]["attr"].type == "Link"):
            info += (str(count) + " - Fes un transbord a l'estació: %s \n" %
                     (g.nodes[path[i]]["name"] + " ; " +
                      g.nodes[path[i]]["nameline"]))
            count += 1

    # Com que no tenim el nom del tots els carrers al graf d'Osmnx, només
    # podem indicar que l'usuari ha de caminar fins al restaurant.
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=info+str(count)+" - Camina pel carrer fins "
                             "al restaurant")


def where(update, context):
    """ Quan l'usuari envia la seva ubicació, l'emmagatzema
    """
    lat, lon = (update.message.location.latitude,
                update.message.location.longitude)
    context.user_data['orig_coords'] = [lon, lat]


def time(update, context):
    """ Retorna la durada de la ruta demanada, en cas que no s'hagi demanat cap
    ruta s'envia un missatge avisant del problema
    """
    try:
        assert context.user_data['travel_time'] > 0

        travel_time = context.user_data['travel_time']
        info = ("El temps de ruta aproximat és de " +
                str(round(travel_time/60)) + " min(s)\n")
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)
    except AssertionError:
        info = ("Encara no s'ha calculat cap ruta com per calcular el temps "
                "de ruta! 😭 \n")
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)


# ---------------------- #
# INICIALITZACIÓ DEL BOT #
# ---------------------- #

# Guardem a un fitxer '.txt' el token per poder modificar i configurar el bot
TOKEN = open('token.txt').read().strip()

# Inicialitzem l'updater i el dispatcher.
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher


# Vinculem les comandes amb les funcions que han d'invocar cada una d'elles
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('author', author))
dispatcher.add_handler(CommandHandler('find', find))
dispatcher.add_handler(CommandHandler('info', info))
dispatcher.add_handler(MessageHandler(Filters.location, where))
dispatcher.add_handler(CommandHandler('guide', guide))
dispatcher.add_handler(CommandHandler('travel_time', time))
dispatcher.add_handler(CommandHandler('accessibility', accessibility))

# Engegem el bot
updater.start_polling()
updater.idle()
