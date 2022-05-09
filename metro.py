from dataclasses import dataclass
from typing import Optional, TextIO
from typing import List, Tuple, Dict
import pandas as pd
import networkx as nx
import haversine as hs
import matplotlib.pyplot as plt
from staticmap import StaticMap, CircleMarker, Line


Point = Tuple[float, float] # Definim Point com un punt sobre el pla de coordenades de Barcelona
MetroGraph = nx.Graph       # Definim un MetroGraph com un graf de Networx

@dataclass
class Station:
    _id: str             # Identificador de l'estació (únic)
    _name : str          # Nom de l'estació (no únic, Notem: hi ha estacions amb el mateix nom però de diferents línies)
    _compound_name : str # Concatenació del nom de l'estació i la seva línia. Ex: Espanya L3. (únic)
    _nameline: str       # Nom de la línia de l'estació
    _linecolor: str      # Color de la línia en format RGB. Ex : #FFFFFF per al color blanc.
    _location : Point    # Un punt tal i com l'hem definit previament.


@dataclass
class Access:
    _id : str            # Identificador del accés
    _name: str           # Nom del accés
    _station_name : str  # Nom de l'estació associada al accés
    _accessible : str    # String binari : o "Accessible" o "No accessible". Indica accessibilitat
    _location : Point    # Posició de tipus punt del accés en qüestió
    _station_id : str    # Identificador de l'estació associada al accés

@dataclass
class Edge:
    _type : str                         # Possibilitats: Street, Acces, Enllaç
    _distance : float                   # Haversine distancia entre node [0] and node [1]
    _colour_id : str                    # RGB

Stations = List[Station]

Accesses = List[Access]

# ------------------ #
# MÈTODES DE LECTURA #
# ------------------ #

def read_stations() -> Stations:
    """ A partir de la informació que conté el fitxer csv amb la base de dades de les estacions, retorna un llistat de totes les estacions """

    #Fitxer on es troba tota l'informació referent a les Stations

    f = open('estacions.csv' , 'r')

    #Assignem a cada atribut el nom de la columna que li pertoca en el fitxer estacions.csv

    _id: str = 'CODI_ESTACIO'
    _name : str = 'NOM_ESTACIO'
    _nameline: str = 'NOM_LINIA'
    _linecolor: str = 'COLOR_LINIA'
    _location : Point = 'GEOMETRY'

    #Creem un dataFrame que conté tota la informació de les columnes que ens interesen

    df = pd.read_csv(f, usecols = [_id, _name,_nameline ,_linecolor, _location] )

    Stations : List[Station] = []

    for row in df.itertuples():
        point : Point = get_coordinates(row.GEOMETRY)
        Current_Station = Station(row.CODI_ESTACIO, row.NOM_ESTACIO ,row.NOM_ESTACIO+";"+row.NOM_LINIA, row.NOM_LINIA,  #El nom de la estació el deixem com a suma del nom i la linia per evitar cicles d'una estació amb si mateixa.
        '#'+row.COLOR_LINIA, point)       # Nota: sumem '#' al color de línia per a acabar de passar-ho a format RGB
        Stations.append(Current_Station)

    return Stations


def read_accesses() -> Accesses:
    """ A partir de la informació que conté el fitxer csv amb la base de dades dels accessos , retorna un llistat de tots els accessos """

    #Fitxer on es troba tota l'informació referent als Accesssos
    f=open('accessos.csv', 'r')

    #Assignem a cada atribut el nom de la columna que li pertoca en el fitxer accessos.csv
    _id : str = 'ID_ACCES'
    _name: str = 'NOM_ACCES'
    _station_name : str = 'NOM_ESTACIO'
    _accessible : str = 'NOM_TIPUS_ACCESSIBILITAT'
    _location : Point = 'GEOMETRY'
    _station_id : str = 'ID_ESTACIO'

    #Creem un DataFrame que conté tota la informació de les columnes que ens interesen del fitxer accessos.csv

    df = pd.read_csv(f, usecols = [_id, _name,_station_name, _accessible, _location, _station_id])

    Accesses : List[Access] = []

    for row in df.itertuples():
        coords: Point = get_coordinates(row.GEOMETRY)
        Current_Access = Access( str(row.ID_ACCES), row.NOM_ACCES ,row.NOM_ESTACIO,
        row.NOM_TIPUS_ACCESSIBILITAT, coords , row.ID_ESTACIO)
        Accesses.append(Current_Access)

    return Accesses


# ------------------------------- #
# MÈTODES DE PRESENTACIÓ DEL GRAF #
# ------------------------------- #

def show(Metro_Graph: MetroGraph)-> None:
    """ Imprimeix el graf Metro_Graph amb els nodes de color blau, i les arestes en negre """
    coords = nx.get_node_attributes(Metro_Graph, 'coordinates')
    nx.draw(Metro_Graph, coords , node_size = 10)
    plt.show()

def plot(g : MetroGraph) -> None:
    m = StaticMap(2500, 3000, 80)
    m = add_nodes(m, g)
    m = add_lines(m, g)
    image = m.render()
    image.save('bcn.png')

def add_lines(m : StaticMap, g: MetroGraph) -> StaticMap:
    """ Donat un StaticMap i un graf, afegeix les arestes del graf a l'StaticMap """
    for edge in g.edges:
        edge_attributes = g.get_edge_data(*edge)
        if edge_attributes["attributes"]._type== "Tram": # Si l'aresta en la que estem és de tipus Tram, cal pintar-la del color de la línia a la que pertany.
            color = edge_attributes["attributes"]._colour_id
        else:                          # En cas contrari, cal pintar la aresta de color gris, Nota: l'hem pintat de color fuchsia per apreciar millor els camins d'access.
            color = "#FF00FF"          # Gris és : "#BABAB6"
        line = Line(edge_attributes["coordinates"], color, 5)  # (Tupla de punts, color, gruix)
        m.add_line(line)
    return m

def add_nodes(m : StaticMap, g : MetroGraph) -> StaticMap:
    """ Donat un StaticMap i un graf, afegeix els nodes del graf a l'StaticMap """
    for node in g.nodes():
        coords = nx.get_node_attributes(g,"coordinates") # Retorna un diccionari de la forma (identificador_del_node : coordinates)
        if g.nodes[node]["type"] == "Acces":
            marker = CircleMarker(coords[node], "#FF00FF", 4) # (Centre del node, color, radi)
            m.add_marker(marker)
        else:
            marker = CircleMarker(coords[node], "#2B2B2B", 10)
            m.add_marker(marker)
    return m



# ------------------------------ #
# MÈTODES DE POSICIÓ I DISTÀNCIA #
# ------------------------------ #


def get_coordinates(info : str) -> Point:
    """ Donada una expressio de la forma Point(x_coord, y_coord) retorna un punt amb x_coord i y_coord """
    expression : List[str] = info[7:-1].split()
    coordinates : Point = (float(expression[0]), float(expression[1]))
    return coordinates


def get_distance(point1: Point, point2 : Point)-> float:
    """ A partir de les coordenades de dos punts, retorna la distancia entre aquests """
    return hs.haversine(point1, point2)*1000


# -------------------------------- #
# MÈTODES D'AFEGIR NODES I ARESTES #
# -------------------------------- #

def add_nodes_and_edges_stations(station1: Station, station2: Station, metro_graph: MetroGraph)-> None:
    """ Pre: les estacions han d'estar ordenades per línia """
    """ A partir de la llista d'estacions, afegeix els nodes referents a aquestes estacions al MetroGraph
    i si es necesari, les arestes entre si """

    #Afegim els dos nodes. Nota: Sempre hi haurà un que estara ja afegit(tret de la primera crida), però ho fem d'aquesta manera per afegir totes les arestes correctament
    metro_graph.add_node(station1._compound_name, type = "Estacio", nameline = station1._nameline, coordinates = station1._location)
    metro_graph.add_node(station2._compound_name, type = "Estacio", nameline = station2._nameline, coordinates = station2._location)

    #Si els dos nodes que hem afegit son de la mateixa línia, els unim amb una aresta de tipus Tram
    if station1._nameline == station2._nameline:  #Si son de la mateixa línia
        _type = "Tram"
        _distance = get_distance(station1._location, station2._location)
        _colour_id = station1._linecolor

        edge = Edge(_type, _distance, _colour_id)

        metro_graph.add_edge(station1._compound_name, station2._compound_name, attributes = edge, coordinates = [station1._location, station2._location]) #Atributs: (tipus d'aresta, linia, distancia, color línia)



def add_edges_accesses(qty_stations: int, all_stations : Stations, all_accesses : Accesses, metro_graph: MetroGraph)-> None:
    """Pre: els accessos han d'estar ordenats per estacions (primer tots els accessos d'una estacio, després els d'una altra etc...) """
    """ Afegeix totes les arestes que connecten els accessos amb les seves respectives estacions """
    for station in all_stations:
        first_matching_access = False # No hem trobat encara cap access de l'estació d'aquesta iteració del bucle
        for access in all_accesses:
            if station._id == access._station_id : # Assegurar-nos que l'acces i la estació comparteixen identificador d'estació.
                first_matching_access = True

                _type = "Acces"
                _distance = get_distance(station._location, access._location)
                _colour_id = "BABAB6"
                edge = Edge ( _type, _distance, _colour_id)

                # Afegim una Aresta de tipus Acces
                metro_graph.add_edge(station._compound_name, access._id+"Access", attributes = edge, coordinates = [station._location, access._location]) # Atributs: (tipus d'aresta, distancia, color línia)
            elif first_matching_access: # Si ja hem trobat previament un access per a aquella estacio i l'access d'aquesta iteració ja no ho és, significa que ja no n'hi ha més (doncs estan ordenats)
                break

def add_nodes_accesses(all_accesses: Accesses, metro_graph : MetroGraph)-> None:
    """ Donats tots els accessos, els afegeix com a nodes al graf """
    for access in all_accesses:
        metro_graph.add_node(access._id+"Access", type = "Acces", accessibility = access._accessible, coordinates = access._location) # Afegim node de tipus Acces.

def add_transbording_edges(all_stations: Stations, metro_graph: MetroGraph)-> None:
    """ Realitza un recorregut sobre les estacions per veure quines tenen enllaç entre si """
    for station1 in all_stations:
        for station2 in all_stations:
            if station1._nameline != station2._nameline and station1._name == station2._name: #Si les estacions no comparteixen linia però comparteixen nom, son arestes d'enllaç

                # Afegim aresta d'enllaç al graf
                _type = "Enllaç"
                _distance = get_distance(station1._location, station2._location)
                _colour_id = station1._linecolor

                edge = Edge(_type, _distance, _colour_id)
                metro_graph.add_edge(station1._compound_name, station2._compound_name, attributes  = edge, coordinates = [station1._location, station2._location]) #Atributs: (tipus d'aresta, linia, distancia, color línia)


# ----------------------------------- #
# MÈTODES DEL MAIN I CREACIÓ DEL GRAF #
# ----------------------------------- #

def get_metro_graph() -> MetroGraph:
    """ Retorna un graf del metro de Barcelona amb la informació dels arxius accessos.csv i estacions.csv """
    Metro_Graph = nx.Graph() #Inicialitzem un graf buit que contindra tota la informació de metro de barcelona

    #Obtenim la informacio dels accessos i estacions del metro de Barcelona
    all_accesses = read_accesses()
    all_stations = read_stations()

    qty_stations = len(all_stations)
    for i in range (1, qty_stations):     #Iterem totes les estacions dos a dos repetint sempre una estació
        station1 = all_stations[i-1]
        station2 = all_stations[i]
        add_nodes_and_edges_stations(station1, station2, Metro_Graph) # Afegim els nodes de l'actual iteració i si es necessari els unim amb una aresta de Tram.

    add_nodes_accesses(all_accesses, Metro_Graph)                             # Afegim tots els nodes Accessos
    add_edges_accesses(qty_stations, all_stations, all_accesses, Metro_Graph) # Afegim totes les arestes de tipus access entre Access i estació
    add_transbording_edges(all_stations, Metro_Graph)                         # Afegim totes les Arestes d'enllaç entre estació i estació

    #Mostrem per pantalla el metro del graf de Barcelona
    #show(Metro_Graph)

    #Generem un png amb el metro de Barcelona dibuixat per sobre.
    #plot(Metro_Graph)

    return Metro_Graph

#get_metro_graph()
