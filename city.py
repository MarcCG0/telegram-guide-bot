import osmnx as ox  #type: ignore
from typing import Union  #type: ignore
import networkx as nx  #type: ignore
import pickle
from metro import*   #Canviar el nom dels fitxers.
import os as os


CityGraph: TypeAlias = nx.Graph  # CityGraph com graf no dirigit de networkx : afegir atributs.
OsmnxGraph: TypeAlias = nx.MultiDiGraph  # Nota: un MultiDiGraph és un graf
# dirig multiArc (poss arestes repetides entre els mateixos parells de nodes)
Coord: TypeAlias = Tuple[float, float]  # (latitude, longitude)

NodeID: TypeAlias = Union[int, str]
Path: TypeAlias = List[NodeID]

# Observació , les distancies entre nodes del MetroGraph estan definides en
# kms mentre que les descarregades d'OSMNX ho estan en metres.

# ------------------------------------------------ #
# FUNCIONS PER LA CREACIÓ I MOSTRA DEL OSMNX GRAPH #
# ------------------------------------------------ #


def get_osmnx_graph() -> OsmnxGraph:
    """ Retorna un graf dels carrers de Barcelona """
    g: OsmnxGraph = ox.graph_from_place('Barcelona, Catalonia, Spain', simplify=True, network_type='walk')
    save_osmnx_graph(g, 'barcelona.grf')
    return g


def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
    """ Guarda el graf g al fitxer filename """
    f = open(filename, 'wb')
    pickle.dump(g, f)
    f.close()


def load_osmnx_graph(filename: str) -> OsmnxGraph:
    """ Retorna el graf guardat al fitxer filename """
    if os.path.exists(filename):
        pickle_in = open(filename, 'rb')
        g: OsmnxGraph = pickle.load(pickle_in)
        pickle_in.close()
        return g
    else:
        return get_osmnx_graph()

# ------------------------------------------------- #
# ACCIONS PER AFEGIR NODES I ARESTES AL CITY GRAPH  #
# ------------------------------------------------- #


def add_Metro_Graph(City_Graph: CityGraph, Metro_Graph: MetroGraph) -> None:
    """ Aquesta acció afegeix les arestes i els nodes del graf del metro de
    Barcelona al graf de la ciutat
    """

    # Afegim els nodes del metro de Barcelona al graf City_Graph
    for node in Metro_Graph.nodes:
        if Metro_Graph.nodes[node]["type"] == "Acces":
            City_Graph.add_node(
                node, type=Metro_Graph.nodes[node]["type"],name = Metro_Graph.nodes[node]["name"],
                coordinates=Metro_Graph.nodes[node]["coordinates"])
        else:
            City_Graph.add_node(
                node, type=Metro_Graph.nodes[node]["type"],name = Metro_Graph.nodes[node]["name"],nameline = Metro_Graph.nodes[node]["nameline"],
                coordinates=Metro_Graph.nodes[node]["coordinates"])


    # Afegim les arestes del metro de Barcelona al graf City_Graph
    for edge in Metro_Graph.edges:

        type = Metro_Graph.edges[edge]["attributes"].type
        distance = Metro_Graph.edges[edge]["attributes"].distance

        # Decidim quin color té l'aresta que estem tractant en aquest precís
        # instant
        if type == "Acces":
            color_id = "#000000"
        elif type == "Tram":
            color_id = Metro_Graph.edges[edge[0], edge[1]]["attributes"].color_id
        else:
            color_id = "#FF0000"

        info = Edge(type, distance, color_id)

        # Afegim tota la informació referent a l'aresta (tipus, distancia,
        # color) dins info (classe Edge definida al mòdul de metro.py)
        City_Graph.add_edge(edge[0], edge[1], time=get_travel_time(type, distance),
                            attr=info)


def add_Street_Graph(City_Graph: CityGraph, Street_Graph: OsmnxGraph) -> None:
    """ Aquesta acció afegeix les arestes i els nodes del graf dels carrers de
    Barcelona al graf de la ciutat """

    # Afegim els nodes que ens hem descarregat del graf dels carrers de
    # Barcelona amb OSMNx, al graf City_Graph

    y: Dict[int, float] = nx.get_node_attributes(Street_Graph, "y")
    x: Dict[int, float] = nx.get_node_attributes(Street_Graph, "x")

    for node in list(Street_Graph.nodes):
        nx.set_node_attributes(Street_Graph, {node: [x[node], y[node]]},
                               'coordinates')

        City_Graph.add_node(
            node, type="Street",
            coordinates=Street_Graph.nodes[node]["coordinates"])

    # Afegim les arestes dels carrers de Barcelona al City_Graph
    for u, nbrsdict in Street_Graph.adjacency():

        for v, edgesdict in nbrsdict.items():
            # son MultiGrafs, per tant només considerem la primera aresta
            dist: float = edgesdict[0]["length"]
            info = Edge("Street", dist, "#F0F619")
            City_Graph.add_edge(u, v, time=get_travel_time("Street", dist),
                                attr=info)


def get_acces_coords(Metro_Graph: MetroGraph, y : List, x : List, access_nodes: List)-> None:
    """ Modifica les llistes y, x, i access_nodes de tal forma que a la posició ièssima dels vectors tenim:
    x[i] = coord x, y[i] = coord y, access_nodes[i] = accés amb coordenades [x[i],y[i]]"""

    for node in Metro_Graph.nodes:
        if Metro_Graph.nodes[node]["type"] == "Acces":
            access_nodes.append(node)
            coordinates = Metro_Graph.nodes[node]['coordinates']
            x.append(coordinates[0])
            y.append(coordinates[1])

def link_Street_with_Access(City_Graph: CityGraph, Street_Graph : OsmnxGraph,  Metro_Graph: MetroGraph)-> None:
    """ Donats el City_Graph, Street_Graph i Metro_Graph actualitza el City_Graph de tal forma que tot node Access
    té una aresta amb el node Street més proper a ell mateix """
    y = nx.get_node_attributes(Street_Graph, "y")

    access_nodes : List = []
    x_coordinates : List = []
    y_coordinates : List = []
    get_acces_coords(Metro_Graph, x_coordinates, y_coordinates, access_nodes)

    nearest_nodes = ox.distance.nearest_nodes(Street_Graph,y_coordinates, x_coordinates)

    for i in range(0, len(access_nodes)):
        dist = getdistance(Metro_Graph.nodes[access_nodes[i]]["coordinates"], Street_Graph.nodes[nearest_nodes[i]]["coordinates"])
        info = Edge("Street",dist , "#FD940A")
        City_Graph.add_edge(access_nodes[i], nearest_nodes[i], attr = info,time =get_travel_time("Street", dist) )


# ---------------------------- #
# FUNCIÓ PER CREAR CITY GRAPH  #
# ---------------------------- #

def build_city_graph(Street_Graph: OsmnxGraph,
                     Metro_Graph: MetroGraph) -> CityGraph:
    # Obs: el city graph tindrà -> Nodes: Street, Station, Access.
    # Edges -> : Enllaç, Tram, Acces, Carrer
    """ Retorna un graf fusió de g1 i g2, formant el CityGraph """
    City_Graph: CityGraph = nx.Graph()

    # Afegim nodes i arestes del Graf dels carrers de Barcelona al City_Graph
    add_Street_Graph(City_Graph, Street_Graph)

    # Afegim nodes i arestes del Graf del Metro de Barcelona al City_Graph
    add_Metro_Graph(City_Graph, Metro_Graph)

    # Creem una aresta des de cada un dels nodes de tipus Access al node de
    # tipus Street més proper
    link_Street_with_Access(City_Graph, Street_Graph, Metro_Graph)

    # Eliminem els cicles que ens donava el graf extret d'OSMNX
    City_Graph.remove_edges_from(nx.selfloop_edges(City_Graph))

    return City_Graph


# ---------------------------------- #
# ACCIONS PER MOSTRAR EL CITY GRAPH  #
# ---------------------------------- #


def show_city(City_Graph: CityGraph) -> None:
    """Pre: el graf d'entrada ha de tenir els nodes amb un atribut amb
    les coordenades d'on es troba
    Donat un Graf el dibuixa per pantalla """
    coords: Coord = nx.get_node_attributes(City_Graph, "coordinates")
    nx.draw(City_Graph, coords, node_size=10)
    plt.show()


def plot_city(g: CityGraph, filename: str) -> None:
    """ Desa dins d'un arxiu filename la imatge del Citygraph """
    m = StaticMap(2500, 3000, 80)
    add_city_nodes(m, g)
    add_city_lines(m, g)
    image = m.render()
    image.save(filename)


def add_city_nodes(m: StaticMap, g: CityGraph) -> None:
    """ Donat un StaticMap i un graf, afegeix els nodes del graf a
    l'StaticMap
    """
    # Retorna un diccionari de la forma (identificador_del_node:coordinates)
    coords: Coord = nx.get_node_attributes(g, "coordinates")
    for node in g.nodes:
        if g.nodes[node]["type"] == "Street":  # Color verd
            color = "#0F7002"
        elif g.nodes[node]["type"] == "Acces":  # Color negre
            color = "#000000"
        else:
            color = "#FF0000"  # Color vermell
        # (Centre del node, color, radi)
        marker = CircleMarker(coords[node], color, 5)
        m.add_marker(marker)
    return m


def add_city_lines(m: StaticMap, g: CityGraph) -> None:
    """ Donat un StaticMap i un graf, afegeix les arestes del graf a
    l'StaticMap
    """
    for edge in g.edges:
        edge_attributes = g.get_edge_data(*edge)
        # Obtenim el color que li hem assignat prèviament a l'aresta
        color = edge_attributes["attr"].color_id
        # (Tupla de punts, color, gruix)
        line = Line([g.nodes[edge[0]]["coordinates"],
                     g.nodes[edge[1]]["coordinates"]], color, 5)
        m.add_line(line)
    return m

# ----------------------------------------------- #
# FUNCIONS PER TROBAR EL PATH I EL TEMPS DE RUTA  #
# ----------------------------------------------- #


def find_path( Street_Graph: OsmnxGraph, City_Graph: CityGraph, src: Coord, dst: Coord) -> Path:
    """ Donat un origen src i un desti dst, retorna el camí Path més ràpid """
    nearest_nodes,dist = ox.distance.nearest_nodes(Street_Graph, [src[0], dst[0]], [src[1], dst[1]], return_dist = True)

    City_Graph.add_node("src_node", type = "Src" , coordinates = src)
    edge = Edge("Street", dist[0], "#000000")
    City_Graph.add_edge("src_node", nearest_nodes[0], time = get_travel_time("Street", dist[0]), attr = edge)

    City_Graph.add_node("dst_node", type = "Dst",coordinates = dst)
    edge = Edge("Street", dist[1], "#000000")
    City_Graph.add_edge("dst_node", nearest_nodes[1], time = get_travel_time("Street", dist[1]), attr = edge)

    Path_to_dst: Path = nx.dijkstra_path(City_Graph, source="src_node",
                                  target="dst_node", weight="time")
    return Path_to_dst


def get_time_path(Path: Path, City_Graph: CityGraph) -> float:
    """ Donada una ruta, retorna el temps que es triga a fer-la """
    qty_nodes = len(Path)
    time: float = 0
    for i in range(1, qty_nodes):
        time += City_Graph.edges[Path[i-1], Path[i]]["time"]
    return time

def get_travel_time(type: str, distance: float) -> float:
    """Donat un tipus d'aresta en retorna la velocitat a la que aquesta es
    recorre en metres per segon
    """
    if type == "Tram":
        return distance/7.5 # Velocitat mitjana en m/s del metre de barcelona : 7.5
    elif type == "Enllaç":
        return distance/1.5+120  # Velocitat mitjana al caminar d'una persona en m/s : 7.5
        # Sumem 180 segons per retràs al canviar d'estació als transbordaments.
    else:
        return distance/1.3


# --------------------------- #
# ACCIONS PER PINTAR EL PATH  #
# --------------------------- #


def plot_path(City_Graph: CityGraph, path: Path, filename: str) -> None:
    """ Dibuixa un path utilitzant el mòdul StaticMap i guarda la imatge en un fitxer"""
    m = StaticMap(2500, 3000, 80)
    add_path_nodes(m, City_Graph, path)
    add_path_lines(m, City_Graph, path)
    image = m.render()
    image.save(filename)


def add_path_lines(m: StaticMap, g: CityGraph, path: Path) -> None:
    """ Donat un Static map , un camí i un graf , dibuixa les arestes del graf pertanyents al camí en aquest StaticMap """
    length_path : int = len(path)
    for i in range(1, length_path):
        if g.edges[path[i-1], path[i]]["attr"].type == "Tram":
            color = g.edges[path[i-1], path[i]]["attr"].color_id
        else:
            color = "#000000"
        line = Line([g.nodes[path[i-1]]["coordinates"], g.nodes[path[i]]["coordinates"]], color, 5)
        m.add_line(line)


def add_path_nodes(m: StaticMap, g: CityGraph, path: Path) -> None:
    """ Donat un StaticMap i un graf, afegeix els nodes del graf pertanyents al camí, a
    l'StaticMap
    """
    coords: Dict[NodeID, Point] = nx.get_node_attributes(g, "coordinates") # diccionari de la forma (identificador_del_node:coordinates)

    for node in path:
        marker = CircleMarker(coords[node], "#000000", 10)
        m.add_marker(marker)
