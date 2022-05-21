import os
from city import find_path, build_city_graph, plot_path, get_time_path, load_osmnx_graph, Path
from metro import get_metro_graph
from restaurants import find_restaurants, read_restaurants
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


#------------------ VARIABLES GLOBALS -------------------#
Metro_Graph = get_metro_graph()
Street_Graph = load_osmnx_graph('barcelona.grf')
City_Graph = build_city_graph(Street_Graph, Metro_Graph)
#--------------------------------------------------------#

# --------------------------------- #
# FUNCIONS PER LES COMANDES DEL BOT #
# --------------------------------- #

def initialize(update, context):
    """ Inicialitza les dades per poder comprovar si s'han efectuat comandes
    o no de qualsevol tipus
    """
    context.user_data['travel_time'] = -1
    context.user_data['desired_restaurants'] = []


def start(update, context):
    """ Envia missatge de benvinguda a l'usuari i inicialitza el context """
    initialize(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hola "+str(update.effective_chat.first_name)+"!👋🏼 \n"+"Soc el bot que et porta a "
                             "menjar en metro, on vols menjar avui?")


def help(update, context):
    """ Envia un missatge d'ajuda amb totes les comandes disponibles """
    info = ("Introdueix alguna de les següents comandes: \n"
            "- ✅ /start inicia la conversa \n"
            "- ✏️ /author mostra els autors del projecte \n"
            "- 🔎 /find <query> busca quins restaurants satisfan la cerca "
            "feta al camp query. En el cas de fer servir cerca multiple amb n paraules,"
            "cal fer servir la següent notació:\n"
            "/find <query(1)>;<query(2)>; ... <query(n-1)>;<query(n)>\n"
            "- 📝 /info <number> mostra la informació del restaurant "
            "especificat pel seu numero a la llista de restaurants impresa "
            "amb la comanda find \n"
            "- 👣 /guide <number> mostra el camí més curt des d'on et trobes "
            "fins al restaurant especificat pel seu nombre  a la llista de "
            "restaurants impresa amb la comanda find. Rebràs tant una guia visual"
            " com una guia verbal per facilitar-te la ruta \n"
            "- ⏳ /travel_time mostra el temps de ruta de l'ultima ruta que "
            "s'ha efectuat amb la comanda /guide <number> \n")
    context.bot.send_message(chat_id=update.effective_chat.id, text=info)


def author(update, context):
    """ Envia un missatge informant de qui són els creadors del projecte """
    info = "Els meus creadors són la Carlota Gozalbo i el Marc Camps"
    context.bot.send_message(chat_id=update.effective_chat.id, text=info)


def find(update, context):
    """ Pre: surten els 12 primers restaurants que s'afegeixin a la llista """
    """ Donada una cerca, envia un missatge de tipus enumeració amb tots els
    restaurants que la satisfan
    """
    try:

        # Obtenim la query a partir del que ha rebut el bot després de /find

        query: str = context.args[0]
        # Notifiquem a l'usuari amb tots els restaurants que s'han trobat
        restaurants: Restaurants = read_restaurants()
        desired_restaurants: Restaurants = find_restaurants(query, restaurants)
        context.user_data['desired_restaurants'] = desired_restaurants

        assert len(desired_restaurants)>0

        info = "Aquests són els restaurants que he trobat: \n"
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)
        qty_rest = len(desired_restaurants)
        # Notifiquem per pantalla tots els restaurants trobats.
        info1 =""
        for i in range(0, qty_rest):
            info1 += str(i+1)+" - "+str(desired_restaurants[i].name)+"\n"
        context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info1)
        mess = ("\n Recorda que per a fer servir la comanda /guide <number> "
                "primer has d'haver compartit la teva ubicació \n")
        context.bot.send_message(chat_id=update.effective_chat.id, text=mess)

    except IndexError:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No has inserit cap nom de restaurant al camp <number> de la comanda /find 😭 \n")
    except AssertionError:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No he trobat cap restaurant que s'ajusti a la teva cerca 😭 \n")


def info(update, context):
    """ Pre: la comanda ha de ser de la forma: /info <int>, on l'enter és un
    nombre entre len(desired_restaurants) i 1 ambdós inclosos
    """
    """ Imprimeix per pantalla tot un seguit d'atributs del restaurant que
    s'indiqui
    """
    try:
        desired_restaurants: Restaurants = (
            context.user_data['desired_restaurants'])
        # posició del restaurant que volem trobar els atributs
        position: int = int(context.args[0])
        # Si la llista de restaurants encara és buida
        assert len(desired_restaurants)>0
        # Si el restaurant que rebem no compleix la precondició, l'advertim
        if 1 > position or position > len(desired_restaurants):
            info = ("Aquest nombre no pertany a cap dels restaurants de la "
                    "llista! 😭 \n")
            context.bot.send_message(chat_id=update.effective_chat.id, text=info)
        else:
            # Altrament, procedim a obtenir i imprimir els atributs del restaurant
            # Ordenem la informació del restaurant per fer el missatge més clar
            desired_restaurant = desired_restaurants[position-1]
            name = desired_restaurant.name
            direction = (str(desired_restaurant.street_name) + " " +
                         str(int(desired_restaurant.street_number)))
            district = desired_restaurant.district
            phone = desired_restaurant.phone
            neighbourhood = desired_restaurant.neighbourhood

            # Disenyem el missatge que volem que s'efectui per pantalla
            info = "Aquests són els atributs del restaurant que m'has demanat\n"
            context.bot.send_message(chat_id=update.effective_chat.id, text=info
                                     + "Nom : " + str(name) + "\n"
                                     + "Direcció : " +str(direction) + "\n"
                                     + "Barri : "+str(neighbourhood)+"\n"
                                     + "Districte : " +str(district) + "\n"
                                     + "Telèfon : " + str(phone) + "\n")
    except IndexError:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No has inserit cap nombre enter després de la comanda /info i per tant no sé quin restaurant vols tafanejar 😭 \n")
    except AssertionError:
        info = ("La llista de resultats encara és buida, primer busca "
                "restaurants que t'interessin i després ja em consultaràs la "
                "seva informació! 😭 \n")
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)

def guide(update, context):
    """ Pre: l'usuari s'ha de trobar a Barcelona i ha d'haver enviat la seva localització. """
    # Nota: Si l'usuari no està a Barcelona, la primera aresta des de
    # l'origen no tindrà sentit
    """ Imprimeix el camí des del punt on es troba l'usuari al restaurant al
    que vol anar
    """
    try:
        desired_restaurants: Restaurants = (
        context.user_data['desired_restaurants'])
        position: int = int(context.args[0])

        # Obtenim les coordenades d'on es troba el restaurant en qüestió
        dst_coords: Coord = context.user_data['dst_coords']
        desired_restaurant: Restaurant = desired_restaurants[position-1]
        orig_coords: Coord = [desired_restaurant.y_coord, desired_restaurant.x_coord]

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Calculant la millor ruta ⏰ ...\n")
                                 
        # Ruta des d'on es troba l'usuari fins al restaurant desitjat
        path: Path = find_path(Street_Graph, City_Graph, dst_coords, orig_coords)
        filename = (update.effective_chat.first_name +
                    update.effective_chat.last_name + ".png")
        # Obtenim una imatge "path.png" de la ruta a seguir
        plot_path(City_Graph, path, filename)
        context.user_data['travel_time'] = get_time_path(path, City_Graph)
        # Enviem la imatge "path.png" al bot per a que la mostri per pantalla
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open(filename, 'rb'))
        indicate_path(path, update, context)
        os.remove(filename)
    except KeyError:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Encara no m'has enviat la ubicació 😭 \n")
    except IndexError:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="O bé no has escrit res al camp <number> o bé el nombre que hi has escrit no pertany a la llista de restaurants 😭 \n")


def indicate_path(path: Path, update, context)-> None:
    """ Donat un camí, notifica a l'usuari del accessos, estacions de sortida, i transbords que ha de fer """
    len_path: int = len(path)

    info = "1 - Camina pel carrer i espera a la següent indicació \n"
    count: int = 2
    for i in range(1, len_path):

        if City_Graph.nodes[path[i]]["type"] == "Street" :
            continue
        # Condició per entrar accessos.
        if City_Graph.nodes[path[i]]["type"] == "Acces" and City_Graph.nodes[path[i-1]]["type"] == "Street":
            info += str(count)+" - Entra per l'accés: %s \n" % (City_Graph.nodes[path[i]]["name"])
            info += str(count+1)+" - Agafa el metro a l'estació: %s \n" % (City_Graph.nodes[path[i]]["name"])
            count+=2

        # Condició per a sortir per acces.
        elif City_Graph.nodes[path[i]]["type"] == "Acces" and City_Graph.nodes[path[i-1]]["type"] == "Station":
            info += str(count)+" - Ves fins l'estació: %s \n" % (City_Graph.nodes[path[i-1]]["name"])
            info += str(count+1)+" - Surt per l'accés: %s \n" % (City_Graph.nodes[path[i]]["name"])
            count+=2

        # Condició per a fer transbords
        elif City_Graph.edges[path[i-1], path[i]]["attr"].type == "Enllaç":
            info += str(count)+" - Fes un transbord a l'estació: %s \n" % (City_Graph.nodes[path[i]]["name"]+ " ; " + City_Graph.nodes[path[i]]["nameline"])
            count+=1

    # Com que no tenim el nom del tots els carrers al graf d'Osmnx, només podem indicar que l'usuari ha de caminar fins al restaurant.
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=info+str(count)+" - Camina pel carrer fins al restaurant")


def where(update, context):
    """ Quan l'usuari envia la seva ubicació, l'emmagatzema """
    lat, lon = (update.message.location.latitude,
                update.message.location.longitude)
    context.user_data['dst_coords'] = [lon, lat]


def time(update, context):
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

# Guardem a un fitxer de tipus txt el token per a tal de poder modificar i
# configurar el bot.
TOKEN = open('token.txt').read().strip()

# Inicialitzem l'updater i el dispatcher.
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher


# Vinculem les comandes amb les funcions que han d'invocar cada una de les
# comandes
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
