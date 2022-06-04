from dataclasses import dataclass
from typing import Optional, TextIO, TypeAlias, List, Tuple, Dict
import pandas as pd  # type: ignore
import networkx as nx  # type: ignore
import haversine as hs  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from staticmap import StaticMap, CircleMarker, Line  # type: ignore


Point = Tuple[float, float]  # Punt sobre el pla de coordenades de Barcelona
MetroGraph: TypeAlias = nx.Graph  # Definim un MetroGraph com graf de Networx


@dataclass
class Station:
    id: str          # Codi de l'estació (en funció de la línia) - únic
    stationid: str   # Codi de l'estació
    name: str        # Nom de l'estació (no únic)
    nameline: str    # Nom de la línia de l'estació
    linecolor: str   # Color de la línia en format RGB
    location: Point  # Localització de l'estació


@dataclass
class Access:
    id: str              # Identificador del accés
    name: str            # Nom del accés
    location: Point      # Posició de tipus punt del accés en qüestió
    stationid: str       # Identificador de l'estació associada al accés
    accessibility: bool  # Indicador d'accessibilitat d'un accés


@dataclass
class Edge:
    type: str            # Possibilitats: Street, Access, Link
    distance: float      # Distancia entre edge[0] i edge[1]
    color_id: str        # RGB


Stations: TypeAlias = List[Station]

Accesses: TypeAlias = List[Access]

# ------------------- #
# FUNCIONS DE LECTURA #
# ------------------- #


def read_stations() -> Stations:
    """A partir de la informació que conté el fitxer csv amb la base de dades
    de les estacions, retorna un llistat de totes les estacions
    """

    # Fitxer on es troba tota l'informació referent a les Stations
    f = open('estacions.csv', 'r')

    # Assignem a cada atribut el nom de la columna que té en el fitxer
    id: str = 'CODI_ESTACIO_LINIA'
    stationid: str = 'CODI_ESTACIO'
    name: str = 'NOM_ESTACIO'
    nameline: str = 'NOM_LINIA'
    linecolor: str = 'COLOR_LINIA'
    location: str = 'GEOMETRY'

    # DataFrame que conté la informació de les columnes que ens interesen
    df = pd.read_csv(f, usecols=[id, stationid, name, nameline, linecolor,
                     location])

    stations: Stations = []

    for row in df.itertuples():
        point: Point = get_coordinates(row.GEOMETRY)
        current_station = Station(row.CODI_ESTACIO_LINIA, row.CODI_ESTACIO,
                                  row.NOM_ESTACIO, row.NOM_LINIA,
                                  '#'+row.COLOR_LINIA, point)
        # sumem '#' al color de línia per passar-ho a format RGB
        stations.append(current_station)

    return stations


def read_accesses() -> Accesses:
    """ A partir de la informació que conté el fitxer csv amb la base de dades
    dels accessos, retorna un llistat de tots els accessos
    """

    # Fitxer on es troba tota l'informació referent als Accesssos
    f = open('accessos.csv', 'r')

    # Assignem a cada atribut el nom de la columna que li pertoca en el fitxer
    id: str = 'ID_ACCES'
    name: str = 'NOM_ACCES'
    location: str = 'GEOMETRY'
    stationid: str = 'ID_ESTACIO'
    accessibility: str = 'NOM_TIPUS_ACCESSIBILITAT'

    # DataFrame que conté tota la informació de les columnes que ens interesen
    df = pd.read_csv(f, usecols=[id, name, location, stationid,
                     accessibility])

    accesses: Accesses = []

    for row in df.itertuples():
        coords: Point = get_coordinates(row.GEOMETRY)
        current_access = Access(str(row.ID_ACCES), row.NOM_ACCES,
                                coords, row.ID_ESTACIO,
                                get_accessibility(
                                    row.NOM_TIPUS_ACCESSIBILITAT))
        accesses.append(current_access)

    return accesses


# ------------------------------------------------- #
# FUNCIONS  I ACCIONS PER A LA PRESENTACIÓ DEL GRAF #
# ------------------------------------------------- #

def show(metro_graph: MetroGraph) -> None:
    """ Imprimeix el graf metro_graph amb els nodes de color blau, i les
    arestes en negre
    """
    coords: Dict[int, Point] = nx.get_node_attributes(metro_graph,
                                                      'coordinates')
    nx.draw(metro_graph, coords, node_size=10)
    plt.show()


def plot(g: MetroGraph) -> None:
    """ Desa el graf com una imatge amb el mapa de la ciutat de fons """
    m = StaticMap(2500, 3000, 80)
    add_nodes(m, g)
    add_lines(m, g)
    image = m.render()
    image.save('bcn.png')


def add_lines(m: StaticMap, g: MetroGraph) -> None:
    """ Donat un StaticMap i un graf, afegeix les arestes del graf a
    l'StaticMap
    """
    for edge in g.edges:
        edge_attributes: Dict = g.get_edge_data(*edge)
        # Escollim el color de la línia a pintar
        if edge_attributes["attributes"].type == "Railway":
            color: str = edge_attributes["attributes"].color_id

        else:
            color = "#BABAB6"

        # Pintem les arestes del color que se'ls ha assignat en el mapa
        line = Line(edge_attributes["coordinates"], color, 5)
        m.add_line(line)


def add_nodes(m: StaticMap, g: MetroGraph) -> None:
    """ Donat un StaticMap i un graf, afegeix els nodes del graf a
    l'StaticMap
    """
    for node in g.nodes():
        coords: Dict[int, Point] = nx.get_node_attributes(g, "coordinates")

        # Pintem els nodes del color que se'ls ha assignat en el mapa
        if g.nodes[node]["type"] == "Access":
            marker = CircleMarker(coords[node], "#BABAB6", 4)
            m.add_marker(marker)
        else:
            marker = CircleMarker(coords[node], "#2B2B2B", 10)
            m.add_marker(marker)


# ------------------------------- #
# FUNCIONS DE POSICIÓ I DISTÀNCIA #
# ------------------------------- #


def get_accessibility(info: str) -> bool:
    """ Donat un string de la forma Accessible o No accessible
    retorna el boolea que li correspon
    """
    """ Pre: l'entrada ha de ser: o bé 'Accessible' o bé 'No accessible' """
    indicator: str = info.split()[0]
    return not indicator == "No"


def get_coordinates(info: str) -> Point:
    """ Pre: l'entrada a de correspondre a una expressió de la forma
    Point(x_coord, y_coord)
    """
    """ Donada una expressio de la forma Point(x_coord, y_coord) retorna un
    punt amb x_coord i y_coord"""

    expression: List[str] = info[7:-1].split()
    coordinates: Point = (float(expression[0]), float(expression[1]))
    return coordinates


def getdistance(point1: Point, point2: Point) -> float:
    """ A partir de les coordenades de dos punts, retorna la distancia entre
    aquests
    """
    return hs.haversine(point1, point2, unit='m')


# -------------------------------- #
# ACCIONS D'AFEGIR NODES I ARESTES #
# -------------------------------- #


def add_nodes_and_edges_stations(station1: Station, station2: Station,
                                 metro_graph: MetroGraph) -> None:
    """ Pre: les estacions han d'estar ordenades per línia al .csv """
    """ A partir de la llista d'estacions, afegeix els nodes referents a
    aquestes estacions al metro_graph i si es necesari, les arestes entre si
    """
    # Afegim els dos nodes per poder afegir les arestes correctament
    metro_graph.add_node(station1.id, type="Station",
                         name=station1.name, nameline=station1.nameline,
                         coordinates=station1.location)
    metro_graph.add_node(station2.id, type="Station", name=station2.name,
                         nameline=station2.nameline,
                         coordinates=station2.location)

    # Si els dos nodes que hem afegit son de la mateixa línia, els unim amb
    # una aresta de tipus Railway
    if station1.nameline == station2.nameline:
        type: str = "Railway"
        distance: float = getdistance(station1.location, station2.location)
        color_id: str = station1.linecolor

        edge = Edge(type, distance, color_id)
        metro_graph.add_edge(
            station1.id, station2.id, attributes=edge,
            coordinates=[station1.location, station2.location])


def add_edges_accesses(
        qty_stations: int, all_stations: Stations, all_accesses: Accesses,
        metro_graph: MetroGraph) -> None:
    """ Pre: els accessos han d'estar ordenats per estacions (primer tots els
    accessos d'una estacio, després els d'una altra etc...)
    """
    """ Afegeix totes les arestes que connecten els accessos amb les seves
    respectives estacions
    """
    for station in all_stations:
        first_matching_access: bool = False  # No hem trobat cap access
        for access in all_accesses:
            # Assegurar-nos que l'acces i la estació comparteixen id d'estació
            if station.stationid == access.stationid:
                first_matching_access = True
                type: str = "Access"
                distance: float = getdistance(station.location,
                                              access.location)
                color_id: str = "BABAB6"
                edge = Edge(type, distance, color_id)

                # Afegim una aresta de tipus Access
                metro_graph.add_edge(
                    station.id, access.id, attributes=edge,
                    coordinates=[station.location, access.location])
            # Condició per passar a la següent estació
            elif first_matching_access:
                break


def add_nodes_accesses(all_accesses: Accesses,
                       metro_graph: MetroGraph) -> None:
    """ Donats tots els accessos, els afegeix com a nodes al graf """
    for access in all_accesses:
        # Afegim node de tipus Access
        metro_graph.add_node(access.id, type="Access", name=access.name,
                             coordinates=access.location,
                             accessibilitat=access.accessibility)


def add_link_edges(all_stations: Stations,
                   metro_graph: MetroGraph) -> None:
    """ Realitza un recorregut sobre les estacions per veure quines haurien
    de tenir transbord(link) entre si
    """
    for station1 in all_stations:
        for station2 in all_stations:
            # Comprovem que una estació amb el mateix nom difereix en línia
            if station1.nameline != station2.nameline:
                if station1.name == station2.name:
                    # Afegim aresta de tipus Link al graf
                    type: str = "Link"
                    distance: float = getdistance(station1.location,
                                                  station2.location)
                    color_id: str = station1.linecolor

                    edge = Edge(type, distance, color_id)

                    metro_graph.add_edge(
                        station1.id, station2.id, attributes=edge,
                        coordinates=[station1.location, station2.location])

# ----------------------------------------- #
# FUNCIÓ PER A LA CREACIÓ DEL GRAF DE METRO #
# ----------------------------------------- #


def get_metro_graph() -> MetroGraph:
    """ Retorna un graf del metro de Barcelona amb la informació dels arxius
    accessos.csv i estacions.csv
    """
    # Graf buit que contindra la info de metro de Barcelona
    metro_graph: MetroGraph = nx.Graph()

    # Obtenim la informacio dels accessos i estacions del metro de Barcelona
    all_accesses: Accesses = read_accesses()
    all_stations: Stations = read_stations()

    qty_stations: int = len(all_stations)
    # Iterem totes les estacions dos a dos repetint sempre una estació
    for i in range(1, qty_stations):
        station1: Station = all_stations[i-1]
        station2: Station = all_stations[i]
        # Afegim nodes de la iteració, si cal els unim amb una aresta Railway
        add_nodes_and_edges_stations(station1, station2, metro_graph)

    # Afegim tots els nodes accessos
    add_nodes_accesses(all_accesses, metro_graph)
    # Afegim totes les arestes de tipus access entre access i station
    add_edges_accesses(qty_stations, all_stations, all_accesses, metro_graph)
    # Afegim totes les arestes de link entre estació i estació
    add_link_edges(all_stations, metro_graph)

    return metro_graph
