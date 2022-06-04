import osmnx as ox  # type: ignore
from typing import Union  # type: ignore
import networkx as nx  # type: ignore
import pickle
from metro import*
import os as os


CityGraph: TypeAlias = nx.Graph
OsmnxGraph: TypeAlias = nx.MultiDiGraph
Coord: TypeAlias = Tuple[float, float]
NodeID: TypeAlias = Union[int, str]
Path: TypeAlias = List[NodeID]


# ------------------------------------------------ #
# FUNCIONS PER LA CREACIÓ I MOSTRA DEL OSMNX GRAPH #
# ------------------------------------------------ #


def get_osmnx_graph() -> OsmnxGraph:
    """ Retorna un graf dels carrers de Barcelona """
    g: OsmnxGraph = ox.graph_from_place('Barcelona, Catalonia, Spain',
                                        simplify=True, network_type='walk')
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


def add_metro_graph(city_graph: CityGraph, metro_graph: MetroGraph) -> None:
    """ Aquesta acció afegeix les arestes i els nodes del graf del metro de
    Barcelona al graf de la ciutat
    """
    # Afegim els nodes del metro de Barcelona al graf city_graph
    for node in metro_graph.nodes:
        # Distingim entre tipus de nodes doncs volem que tinguin atributs
        # diferents
        if metro_graph.nodes[node]["type"] == "Access":
            city_graph.add_node(
                node, type=metro_graph.nodes[node]["type"],
                name=metro_graph.nodes[node]["name"],
                coordinates=metro_graph.nodes[node]["coordinates"])
        else:
            city_graph.add_node(
                node, type=metro_graph.nodes[node]["type"],
                name=metro_graph.nodes[node]["name"],
                nameline=metro_graph.nodes[node]["nameline"],
                coordinates=metro_graph.nodes[node]["coordinates"])

    # Afegim les arestes del metro de Barcelona al graf city_graph
    for edge in metro_graph.edges:

        type: str = metro_graph.edges[edge]["attributes"].type
        distance: float = metro_graph.edges[edge]["attributes"].distance

        # Decidim quin color té l'aresta que estem tractant en aquest instant
        if type == "Access":
            color_id: str = "#000000"
        elif type == "Railway":
            color_id = (metro_graph.edges[edge[0],
                        edge[1]]["attributes"].color_id)
        else:
            color_id = "#FF0000"

        # Afegim la informació referent a l'aresta dins info (classe Edge)
        info = Edge(type, distance, color_id)

        city_graph.add_edge(edge[0], edge[1],
                            time=get_travel_time(type, distance), attr=info)


def add_Street_Graph(city_graph: CityGraph, street_graph: OsmnxGraph) -> None:
    """ Afegeix les arestes i els nodes del graf dels carrers de
    Barcelona al graf de la ciutat
    """
    y: Dict[int, float] = nx.get_node_attributes(street_graph, "y")
    x: Dict[int, float] = nx.get_node_attributes(street_graph, "x")

    for node in list(street_graph.nodes):
        # Afegir un atribut 'coordinates' a cada node.
        nx.set_node_attributes(street_graph, {node: [x[node], y[node]]},
                               'coordinates')

        city_graph.add_node(
            node, type="Street",
            coordinates=street_graph.nodes[node]["coordinates"])

    # Afegim les arestes dels carrers de Barcelona al city_graph
    for u, nbrsdict in street_graph.adjacency():

        for v, edgesdict in nbrsdict.items():
            # son MultiDiGrafs, només considerem la primera aresta
            dist: float = edgesdict[0]["length"]
            info = Edge("Street", dist, "#F0F619")
            city_graph.add_edge(u, v, time=get_travel_time("Street", dist),
                                attr=info)


def get_access_coords(metro_graph: MetroGraph, y: List, x: List,
                      access_nodes: List) -> None:
    """ Modifica les llistes x, y, i access_nodes de tal forma que a la
    posició ièssima dels vectors tenim: x[i] = coord x, y[i] = coord y,
    access_nodes[i] = accés amb coordenades [x[i],y[i]]
    """
    for node in metro_graph.nodes:
        if metro_graph.nodes[node]["type"] == "Access":
            access_nodes.append(node)
            coordinates: Coord = metro_graph.nodes[node]['coordinates']
            x.append(coordinates[0])
            y.append(coordinates[1])


def link_Street_with_Access(city_graph: CityGraph, street_graph: OsmnxGraph,
                            metro_graph: MetroGraph) -> None:
    """ Donats el city_graph, street_graph i metro_graph actualitza el
    city_graph de tal forma que tot node Access tingui una aresta amb el node
    Street més proper a ell mateix
    """

    access_nodes: List[str] = []
    x_coordinates: List[float] = []
    y_coordinates: List[float] = []
    get_access_coords(metro_graph, y_coordinates, x_coordinates, access_nodes)

    # Trobem el node proper a cada accés
    nearest_nodes, dist = ox.distance.nearest_nodes(
        street_graph, x_coordinates, y_coordinates, return_dist=True)

    # Afegim una aresta entre cada accés i el seu node Street més proper
    for i in range(0, len(access_nodes)):
        info = Edge("Street", dist[i], "#BABAB6")
        city_graph.add_edge(access_nodes[i], nearest_nodes[i], attr=info,
                            time=get_travel_time("Street", dist[i]))


# ---------------------------- #
# FUNCIÓ PER CREAR CITY GRAPH  #
# ---------------------------- #


def build_city_graph(street_graph: OsmnxGraph, metro_graph: MetroGraph,
                     accessibility: bool) -> CityGraph:
    """ Retorna un graf fusió del metro_graph i street_graph, formant el
    CityGraph
    """
    city_graph: CityGraph = nx.Graph()

    # Afegim nodes i arestes del Graf dels carrers de Barcelona al city_graph
    add_Street_Graph(city_graph, street_graph)

    # Afegim nodes i arestes del Graf del Metro de Barcelona al city_graph
    add_metro_graph(city_graph, metro_graph)

    # Creem aresta des de cada un dels nodes de tipus Access al node de
    # tipus Street més proper
    link_Street_with_Access(city_graph, street_graph, metro_graph)

    # Eliminem els cicles que ens donava el graf extret d'OSMNX
    city_graph.remove_edges_from(nx.selfloop_edges(city_graph))

    # Comprovem l'accessibilitat en funció del que l'usuari hagi demanat
    if accessibility:
        delete_unaccessible_accesses(city_graph, metro_graph)

    return city_graph


# ---------------------------------- #
# ACCIÓ PER TRACTAR L'ACCESSIBILITAT #
# ---------------------------------- #


def delete_unaccessible_accesses(city_graph: CityGraph,
                                 metro_graph: MetroGraph) -> None:
    """ Elimina els accessos no accessibles del graf de la ciutat """
    for node in metro_graph.nodes:
        if (metro_graph.nodes[node]["type"] == "Access" and
                not metro_graph.nodes[node]["accessibilitat"]):
            city_graph.remove_node(node)


# ---------------------------------- #
# ACCIONS PER MOSTRAR EL CITY GRAPH  #
# ---------------------------------- #


def show_city(city_graph: CityGraph) -> None:
    """ Pre: els nodes del graf d'entrada han de tenir un atribut
    coordinates (on es troba ubicat)
    """
    """ Donat un Graf el dibuixa per pantalla """
    coords: Coord = nx.get_node_attributes(city_graph, "coordinates")
    nx.draw(city_graph, coords, node_size=10)
    plt.show()


def plot_city(g: CityGraph, filename: str) -> None:
    """ Desa dins d'un arxiu filename la imatge del CityGraph """
    m = StaticMap(2500, 3000, 80)
    add_city_nodes(m, g)
    add_city_lines(m, g)
    image = m.render()
    image.save(filename)


def add_city_nodes(m: StaticMap, g: CityGraph) -> None:
    """ Donat un StaticMap i un graf, afegeix els nodes del graf a
    l'StaticMap
    """
    coords: Dict = nx.get_node_attributes(g, "coordinates")
    for node in g.nodes:
        if g.nodes[node]["type"] == "Street":
            color: str = "#0F7002"  # Color verd
        elif g.nodes[node]["type"] == "Access":
            color = "#000000"  # Color negre
        else:
            color = "#FF0000"  # Color vermell
        # Pintem els nodes del color que se'ls ha assignat en el mapa
        marker = CircleMarker(coords[node], color, 5)
        m.add_marker(marker)


def add_city_lines(m: StaticMap, g: CityGraph) -> None:
    """ Donat un StaticMap i un graf, afegeix les arestes del graf a
    l'StaticMap
    """
    for edge in g.edges:
        edge_attributes: Dict = g.get_edge_data(*edge)
        # Obtenim el color que li hem assignat prèviament a l'aresta
        color: str = edge_attributes["attr"].color_id

        # Pintem les arestes del color que se'ls ha assignat en el mapa
        line = Line([g.nodes[edge[0]]["coordinates"],
                     g.nodes[edge[1]]["coordinates"]], color, 5)
        m.add_line(line)


# ----------------------------------------------- #
# FUNCIONS PER TROBAR EL PATH I EL TEMPS DE RUTA  #
# ----------------------------------------------- #


def find_path(street_graph: OsmnxGraph, city_graph: CityGraph, src: Coord,
              dst: Coord) -> Path:
    """ Donat un origen src i un desti dst, retorna el camí Path més
    ràpid
    """
    # Trobem els nodes del street_graph més propers al src i dst
    # I busquem el camí més ràpid entre sí
    nearest_node, dist = ox.distance.nearest_nodes(
        street_graph, [src[0], dst[0]], [src[1], dst[1]], return_dist=True)

    # L'algorisme dijkstra calcula el camí mes curt entre source i target
    # El pes de les arestes és el temps que un triga en recórrer-les
    Path_to_dst: Path = nx.dijkstra_path(city_graph, source=nearest_node[0],
                                         target=nearest_node[1], weight="time")
    return Path_to_dst


def get_time_path(path: Path, city_graph: CityGraph) -> float:
    """ Donada una ruta, retorna el temps que es triga a fer-la """
    qty_nodes = len(path)
    time: float = 0
    for i in range(1, qty_nodes):
        time += city_graph.edges[path[i-1], path[i]]["time"]
    return time


def get_travel_time(type: str, distance: float) -> float:
    """ Donat un tipus d'aresta retorna la velocitat a la que aquesta es
    recorre en metres per segon
    """
    if type == "Railway":
        return distance/7.5  # Vel mitjana en m/s del metro de barcelona(7.5)
    elif type == "Link":
        return distance/1.5+120  # Vel mitjana al caminar en m/s (1.5)
        # Sumem 180 segons per retràs al canviar d'estació als transbordaments
    else:
        return distance/1.5


# --------------------------- #
# ACCIONS PER PINTAR EL PATH  #
# --------------------------- #


def plot_path(city_graph: CityGraph, path: Path, filename: str,
              orig_coords: Coord, dst_coords: Coord) -> None:
    """ Dibuixa un path utilitzant el mòdul StaticMap i guarda la imatge en
    un fitxer
    """
    m = StaticMap(600, 600)
    add_path_lines(m, city_graph, path)
    image = m.render()
    image.save(filename)


def add_path_lines(m: StaticMap, g: CityGraph, path: Path) -> None:
    """ Donat un Static map, un camí i un graf, dibuixa les arestes del graf
    que pertanyen al camí en aquest StaticMap
    """
    length_path: int = len(path)
    for i in range(1, length_path):
        # En funció de l'aresta assignem un color a aquesta
        if g.edges[path[i-1], path[i]]["attr"].type == "Railway":
            color: str = g.edges[path[i-1], path[i]]["attr"].color_id
        else:
            color = "#000000"
        # Pintem les arestes del color que se'ls ha assignat en el mapa
        line = Line([g.nodes[path[i-1]]["coordinates"],
                     g.nodes[path[i]]["coordinates"]], color, 2)
        m.add_line(line)
