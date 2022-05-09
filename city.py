import collections
import osmnx as ox
from typing import List, Tuple, Dict, Union
import networkx as nx
import urllib.request
import pickle
import pandas as pd
from staticmap import StaticMap, Line
import csv
import requests
import matplotlib.pyplot as plt
from haversine import haversine
from easyinput import read
from metro import*
import os as os

PathGraph = nx.Graph         # Definim un PathGraph com el graf de nodes i edges necessaris per anar d'un punt src a un altre punt dst
CityGraph = nx.Graph         # Definim el CityGraph com un graf no dirigit de networkx
OsmnxGraph = nx.MultiDiGraph # Nota: un MultiDiGraph és un graf dirigit multi Arc (poden haver-hi arestes repetides entre els mateixos parells de nodes).
Coord = Tuple[float, float]  # (latitude, longitude)
MetroGraph = nx.Graph        # Definim un MetroGraph com un graf de Networkx

NodeID = Union[int, str]
Path = List[NodeID]

# Observació , les distancies entre nodes del MetroGraph estan definides en kms mentre que les descarregades d'OSMNX ho estan en metres.

# ----------------------------------------------- #
# MÈTODES PER LA CREACIÓ I MOSTRA DEL OSMNX GRAPH #
# ----------------------------------------------- #

def get_osmnx_graph() -> OsmnxGraph:
    """ Retorna un graf dels carrers de Barcelona """
    g = ox.graph_from_place('Barcelona, Catalonia, Spain', simplify = True, network_type='walk')
    save_osmnx_graph(g,'graf.dat')
    return g

def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
    """ Guarda el graf g al fitxer filename """
    f = open(filename , 'wb')
    pickle.dump(g, f)
    f.close()

def load_osmnx_graph(filename: str) -> OsmnxGraph:
    """ Retorna el graf guardat al fitxer filename """
    if os.path.exists(filename):
        pickle_in = open(filename , 'rb')
        g : OsmnxGraph = pickle.load(pickle_in)
        pickle_in.close()
        return g
    else:
        return get_osmnx_graph()

    #Observació: aquesta funció és una funció auxiliar que no cal utilitzar per dur a terme el projecte.
def show_osmnxGraph(g: OsmnxGraph)-> None:
    """ Dibuixa per pantalla el graf dels carrers de Barcelona """

    g = get_osmnx_graph()

    y = nx.get_node_attributes(g, "y")
    x = nx.get_node_attributes(g, "x")

    # al node node, creem un nou atribut que es diu coordinates amb valor [x[node], y[node]]
    for node in g.nodes:
        nx.set_node_attributes(g, {node : [x[node], y[node]]}, 'coordinates')


    coords = nx.get_node_attributes(g, 'coordinates')

    nx.draw(g, coords, node_size = 10)
    plt.show()


# ----------------------------------------------- #
# MÈTODES PER LA CREACIÓ I MOSTRA DEL CITY GRAPH  #
# ----------------------------------------------- #

def get_speed(type : str)-> int:
    """Donat un tipus d'aresta en retorna la velocitat a la que aquesta es recorre en metres per segon """
    if type == "Tram":
        return 7.5 # Velocitat mitjana en metres per segon del metre de barcelona
    else:
        return 1.5 # Velocitat mitjana del caminar d'una persona qualsevol en metres per segon.


def add_Metro_Graph(City_Graph: CityGraph , Metro_Graph : MetroGraph)-> None:
    """ Aquesta acció afegeix les arestes i els nodes del graf del metro de Barcelona
    al graf de la ciutat """

    # Afegim els nodes del metro de Barcelona al graf City_Graph
    for node in Metro_Graph.nodes:
        City_Graph.add_node(node, type = Metro_Graph.nodes[node]["type"], coordinates = Metro_Graph.nodes[node]["coordinates"])

    #Afegim les arestes del metro de Barcelona al graf City_Graph
    for edge in Metro_Graph.edges:

        _type = Metro_Graph.edges[edge]["attributes"]._type
        _distance = Metro_Graph.edges[edge]["attributes"]._distance

        # Decidim quin color té l'aresta que estem tractant en aquest precís instant.
        if _type == "Acces":
            _colour_id = "#000000"
        elif _type == "Tram":
            _colour_id= "#1B00E5"
        else :
            _colour_id = "#FF0000"

        info = Edge(_type, _distance, _colour_id)

        # Afegim tota la informació referent a l'aresta (tipus, distancia, color) dins info (classe Edge definida al mòdul de metro.py)
        City_Graph.add_edge(edge[0], edge[1],time = _distance/get_speed(_type) ,attr = info)



def add_Street_Graph(City_Graph : CityGraph, Street_Graph: OsmnxGraph)-> None:
    """ Aquesta acció afegeix les arestes i els nodes del graf dels carrers de
    Barcelona al graf de la ciutat """

    # Afegim els nodes que ens hem descarregat del graf dels carrers de Barcelona amb OSMNx, al graf City_Graph

    y = nx.get_node_attributes(Street_Graph, "y")
    x = nx.get_node_attributes(Street_Graph, "x")

    for node in list(Street_Graph.nodes):
        nx.set_node_attributes(Street_Graph, {node : [x[node], y[node]]}, 'coordinates')


        City_Graph.add_node(node, type = "Street", coordinates = Street_Graph.nodes[node]["coordinates"])

    # Afegim les arestes dels carrers de Barcelona al City_Graph
    for u, nbrsdict in Street_Graph.adjacency():

         for v, edgesdict in nbrsdict.items():
             dist = edgesdict[0]["length"] # Els grafs d'OSMNX son MultiGrafs , per tant només considerem la primera aresta.
             info = Edge("Street", dist, "#F0F619")
             City_Graph.add_edge(u,v,time = dist/get_speed("Street"),attr = info)



def link_Street_with_Access(City_Graph: CityGraph, Street_Graph : OsmnxGraph,  Metro_Graph: MetroGraph)-> None:
    """ Donats el City_Graph, Street_Graph i Metro_Graph actualitza el City_Graph de tal forma que tot node Access
    té una aresta amb el node Street més proper a ell mateix """

    for node1 in Metro_Graph.nodes:
        if Metro_Graph.nodes[node1]["type"] == "Acces": #Si és un Accés cal connectar-lo amb el node més proper de tipus street.
            dist_min = -1
            id_dist_min = -1 # ID del node amb el que trobem la distància mínima

            # Iterem sobre tots els nodes de tipus carrer i busquem el més proper.
            for node2 in Street_Graph.nodes:
                dist_to_compare = get_distance(Metro_Graph.nodes[node1]["coordinates"],Street_Graph.nodes[node2]["coordinates"])
                if dist_min > dist_to_compare or dist_min == -1: # Si és el primer node que tractem o la distancia minima és menor a la que estem tractant
                    dist_min : int = dist_to_compare             # Actualitzem la distancia mínima i el node que la fa possible.
                    id_dist_min : int= node2
            info = Edge("Street", dist_min, "#FD940A")
            City_Graph.add_edge(node1, id_dist_min, time =dist_min/get_speed("Street") , attr = info)



# Obs: el city graph tindrà -> Nodes: Street, Station, Access. Edges -> : Enllaç, Tram, Acces, Carrer
def build_city_graph(Street_Graph: OsmnxGraph, Metro_Graph: MetroGraph) -> CityGraph:
    """ Retorna un graf fusió de g1 i g2, formant el CityGraph """
    City_Graph = nx.Graph()

    # Afegim els nodes i les arestes del Graf dels carrers de Barcelona al City_Graph.
    add_Street_Graph(City_Graph, Street_Graph)

    # Afegim els nodes i les arestes del Graf del Metro de Barcelona al City_Graph.
    add_Metro_Graph(City_Graph, Metro_Graph)

    # Creem una aresta des de cada un dels nodes de tipus Access al node de tipus Street més proper
    link_Street_with_Access(City_Graph, Street_Graph, Metro_Graph)

    # Eliminem els cicles que ens donava el graf extret d'OSMNX
    City_Graph.remove_edges_from(nx.selfloop_edges(City_Graph))

    return City_Graph

# ----------------------------------------------- #
# MÈTODES PER LA GUARDAR I OBTENIR EL CITY GRAPH  #
# ----------------------------------------------- #

def get_city_graph() -> CityGraph:
    """ Retorna un graf dels carrers de Barcelona """
    Metro_Graph = get_metro_graph()
    Street_Graph = load_osmnx_graph("graf.dat")
    City_Graph = build_city_graph(Street_Graph, Metro_Graph)
    save_city_graph(City_Graph,'city_graf.dat')
    return City_Graph

# Pre: mirar com funciona pickle, i la funcio per veure si un fitxer existeix: os.path.exists
def save_city_graph(City_Graph: CityGraph, filename: str) -> None:
    """ Guarda el graf City_Graph al fitxer filename """
    f = open(filename , 'wb')
    pickle.dump(City_Graph, f)
    f.close()

# Pre: mirar com funciona pickle, i la funcio per veure si un fitxer existeix: os.path.exists
def load_city_graph(filename: str) -> OsmnxGraph:
    """ Retorna el graf guardat al fitxer filename """
    if os.path.exists(filename):
        pickle_in = open(filename , 'rb')
        City_Graph : CityGraph = pickle.load(pickle_in)
        pickle_in.close()
        return City_Graph
    else:
        return get_city_graph()



# ---------------------------------- #
# MÈTODES PER MOSTRAR EL CITY GRAPH  #
# ---------------------------------- #

    """Pre: el graf d'entrada ha de tenir els nodes amb un atribut amb les coordenades d'on es troba"""
def show(City_Graph : CityGraph)-> None:
    """ Donat un Graf el dibuixa per pantalla """
    coords = nx.get_node_attributes(City_Graph, "coordinates")
    nx.draw(City_Graph, coords, node_size = 10)
    plt.show()


def plot(g: CityGraph, filename: str) -> None:
    """ Desa dins d'un arxiu filename la imatge del Citygraph """
    m = StaticMap(2500, 3000, 80)
    m = add_city_nodes(m, g)
    m = add_city_lines(m,g)
    image = m.render()
    image.save(filename)

def add_city_nodes(m: StaticMap, g: CityGraph)-> StaticMap:
    """ Donat un StaticMap i un graf, afegeix els nodes del graf a l'StaticMap """
    coords = nx.get_node_attributes(g,"coordinates") # Retorna un diccionari de la forma (identificador_del_node : coordinates)
    for node in g.nodes:
        if g.nodes[node]["type"] == "Street": # Color verd
            color = "#0F7002"
        elif g.nodes[node]["type"] == "Acces": # Color negre
            color = "#000000"
        else :
            color = "#FF0000" # Color vermell

        marker = CircleMarker(coords[node], color, 5) # (Centre del node, color, radi)
        m.add_marker(marker)
    return m

def add_city_lines(m: StaticMap, g: CityGraph)-> StaticMap:
    """ Donat un StaticMap i un graf, afegeix les arestes del graf a l'StaticMap """
    for edge in g.edges:
        edge_attributes = g.get_edge_data(*edge)
        color = edge_attributes["attr"]._colour_id # Obtenim el color que li hem assignat prèviament a l'aresta.
        line = Line([g.nodes[edge[0]]["coordinates"], g.nodes[edge[1]]["coordinates"]], color, 5)  # (Tupla de punts, color, gruix)
        m.add_line(line)
    return m


# ------------------------------------- #
# MÈTODES AUXILIARS PER TROBAR EL PATH  #
# ------------------------------------- #


def nearest_node(City_Graph: CityGraph, src: Coord)-> Tuple:
    """ Donada una coordenada, troba el node més proper i la seva distancia """
    min_dist = -1
    min_dist_id = -1
    for node in City_Graph.nodes:
        if node != "srcnode" and node!= "dstnode": #Condició per evitar cicles (distàncies 0)
            current_dist = get_distance(City_Graph.nodes[node]["coordinates"], src)

            #Si la distancia que acabem de trobar és menor a la menor que hem trobat previament o és la primera que tractem, la actualitzem
            if current_dist < min_dist or min_dist == -1:
                min_dist = current_dist
                min_dist_id = node

    return (min_dist, min_dist_id) # La posició 0 de la tupla representa la minima distància, i la posició 1 representa l'ID del node
                                   # amb el que el node src manté aquesta distància.


# Obs: s'utilitza ox_g per trobar els nodes més propers a les coordenades. PREGUNTAR SI CAL
def add_auxiliary_elements(City_Graph: CityGraph, src: Coord, dst: Coord)-> None:
    """Afegeix els nodes i les arestes necessàries per vincular el punt de partida i d'arribada
    de qualsevol path amb tota l'estructura del graf """
    City_Graph.add_node("srcnode", coordinates = src)
    first_node  = nearest_node(City_Graph, src)
    City_Graph.add_edge("srcnode", first_node[1], time = first_node[0]/get_speed("Street") , attr = Edge("Auxiliary", first_node[0], "#000000"))

    City_Graph.add_node("dstnode", coordinates = dst)
    last_node = nearest_node(City_Graph, dst)
    City_Graph.add_edge(last_node[1], "dstnode", time = last_node[0]/get_speed("Street"), attr = Edge("Auxiliary", last_node[0], "#000000"))

def delete_auxiliary_elements(City_Graph: CityGraph)-> None:
    """ Elimina els nodes i arestes que hem hagut d'afegir per a un cas concret de cerca"""
    City_Graph.remove_node("dstnode")
    City_Graph.remove_node("srcnode")



# --------------------------- #
# MÈTODES PER TROBAR EL PATH  #
# --------------------------- #


def find_path(City_Graph: CityGraph, src: Coord, dst: Coord) -> Path:
    """ Donat un origen(src) i un desti(dst), retorna el camí(Path) més ràpid """
    add_auxiliary_elements(City_Graph, src, dst)
    Path = nx.dijkstra_path(City_Graph, source = "srcnode", target = "dstnode", weight = "time")
    return Path

def get_time_path(Path : Path, City_Graph : CityGraph)-> float:
    qty_nodes = len(Path)
    time = 0
    for i in range(1 , qty_nodes):
        time += City_Graph.edges[Path[i-1] , Path[i]]["time"]
    return time


def create_path_graph(City_Graph: CityGraph, path: Path)->PathGraph:
    qty_nodes = len(path)
    graph = nx.Graph()
    for i in range(1, qty_nodes):
        node1 = path[i-1]
        node2 = path[i]
        graph.add_node(path[i-1], coordinates = City_Graph.nodes[node1]["coordinates"])
        graph.add_node(path[i-1], coordinates = City_Graph.nodes[node2]["coordinates"])
        graph.add_edge(path[i-1], path[i],type = City_Graph.edges[node1, node2]["attr"]._type,  coordinates = [City_Graph.nodes[node1]["coordinates"],City_Graph.nodes[node2]["coordinates"]])

    graph.add_node("dstnode", coordinates = City_Graph.nodes["dstnode"]["coordinates"])

    return graph


# --------------------------- #
# MÈTODES PER PINTAR EL PATH  #
# --------------------------- #

def plot_path(City_Graph: CityGraph, path: Path)->None:
    graph = create_path_graph(City_Graph, path)
    m = StaticMap(2500, 3000, 80)
    m = add_path_nodes(m,graph)
    m = add_path_lines(m,graph)
    image = m.render()
    image.save("path.png")

def add_path_lines(m: StaticMap, g: PathGraph)->StaticMap:
    for edge in g.edges:
        edge_attributes = g.get_edge_data(*edge)
        if edge_attributes["type"] == "Tram":
            color = "#FF0000"          # Gris és : "#BABAB6"
        else :
            color = "#000000"
        line = Line(edge_attributes["coordinates"], color, 5)  # (Tupla de punts, color, gruix)
        m.add_line(line)
    return m

def add_path_nodes(m : StaticMap, g : PathGraph) -> StaticMap:
    """ Donat un StaticMap i un graf, afegeix els nodes del graf a l'StaticMap """
    for node in g.nodes():
        coords = nx.get_node_attributes(g,"coordinates") # Retorna un diccionari de la forma (identificador_del_node : coordinates)
        marker = CircleMarker(coords[node], "#000000", 10)
        m.add_marker(marker)
    return m


# -----> Proves per a comprovar que funciona <----- #

#---------------------------------------------------#

# City_Graph = load_city_graph("city_graf.dat")
#
# plot(City_Graph, "vista.png")
#
# #path = find_path(City_Graph, [2.1224736657028225, 41.39440575084319], [2.1722533841178095, 41.424977979527746])
# #path = find_path(City_Graph, [2.1350594815841912,41.40990499200444], [2.1292361938137767,41.40032407926403])
# path = find_path(City_Graph, [2.0965190294167204,41.41618835553193], [2.122574472898867, 41.40071428187891])
# plot_path(City_Graph, path)
# graph = create_path_graph(City_Graph, path)
#
# coords = nx.get_node_attributes(graph, "coordinates")
# nx.draw(graph, coords, node_size = 10)
# plt.show()

#---------------------------------------------------#
