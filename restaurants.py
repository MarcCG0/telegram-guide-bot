from dataclasses import dataclass
from typing import Optional, TextIO, TypeAlias
from typing import List, Tuple, Dict
import pandas as pd  # type: ignore
import easyinput as ei  # type: ignore
import operator
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


Coordinate: TypeAlias = float  # Definim una coordenada com un float


@dataclass
class Restaurant:
    name: str
    street_name: str
    street_number: str
    district: str
    neighbourhood: str
    phone: str
    x_coord: Coordinate
    y_coord: Coordinate


# Definim Restaurants com una llista de Restaurants
Restaurants: TypeAlias = List[Restaurant]

# ----------------- #
# FUNCIÓ DE LECTURA #
# ----------------- #


def read_restaurants() -> Restaurants:
    """A partir de la informació que conté el fitxer csv amb la base de dades
    dels restaurants, retorna un llistat de tots els restaurants
    """
    # Fitxer on es troba tota la informació referent als Restaurants
    f = open('restaurants.csv', 'r')

    # Assignem a cada atribut el nom de la columna que li pertoca en el fitxer
    name: str = 'name'
    street_name: str = 'addresses_road_name'
    street_number: str = 'addresses_start_street_number'
    neighbourhood: str = 'addresses_neighborhood_name'
    district: str = 'addresses_district_name'
    phone: str = 'values_value'
    x_coord: Coordinate = 'geo_epgs_4326_x'
    y_coord: Coordinate = 'geo_epgs_4326_y'

    # DataFrame que conté la informació de les columnes que ens interessen
    df = pd.read_csv(f, usecols=[name, street_name, street_number,
                                 neighbourhood, district, phone, x_coord,
                                 y_coord])

    restaurants: List[Restaurant] = []

    # Recorregut de les columnes que hem escollit previament del fitxer
    for row in df.itertuples():

        # Creem un restaurant amb la informació de la fila actual
        restaurant = Restaurant(row.name, row.addresses_road_name,
                                row.addresses_start_street_number,
                                row.addresses_neighborhood_name,
                                row.addresses_district_name,
                                row.values_value,
                                row.geo_epgs_4326_x, row.geo_epgs_4326_y)
        # Afegim aquest restaurant a la llista
        restaurants.append(restaurant)
    return restaurants


# ----------------- #
# FUNCIONS DE CERCA #
# ----------------- #


def get_dictionary(restaurants: Restaurants) -> Dict[str, Restaurant]:
    """ Retorna un diccionari de la forma {nom del restaurant:
    instància de la classe d'aquell restaurant} per a tot el llistat de
    restaurants
    """
    dict: Dict[string, Restaurant] = {}
    for restaurant in restaurants:
        dict[restaurant.name] = restaurant

    return dict


def find_matching_restaurants(list_query: List,
                              restaurants: Restaurants) -> Restaurants:
    """ Donada una cerca, multiple o única, la duu a terme tot utilitzant
    la cerca difusa (Distància de levenshtein)
    """
    # Inicialitzem la llista i el diccionari buits
    matching_with_query: Restaurants = []
    dict_appearances: Dict[string, int] = {}

    # Recorrem restaurants i assignem un grau de "matching" respecte la cerca
    # efectuada per l'usuari
    for restaurant in restaurants:
        attributes = [str(restaurant.name), str(restaurant.street_name),
                      str(restaurant.street_number), str(restaurant.district),
                      str(restaurant.neighbourhood)]
        for query in list_query:
            for attribute in attributes:
                for string in attribute.split():
                    ratio: int = fuzz.ratio(query.lower(), string.lower())
                    if (ratio > 85 or (len(query) > 2 and query.lower() in
                                       string.lower())):
                        if restaurant.name in dict_appearances:
                            dict_appearances[restaurant.name] += 1 * ratio
                        else:
                            dict_appearances[restaurant.name] = 1 * ratio

    # Un cop tenim els candidats, els ordenem per importància
    name_restaurant_dict: Dict[string, Restaurant] = get_dictionary(
        restaurants)
    matching_restaurants: Restaurants = []
    for restaurant_name in sorted(dict_appearances.items(),
                                  key=operator.itemgetter(1), reverse=True):
        if (len(matching_restaurants) > 12 or
                dict_appearances[restaurant_name[0]] == 0):
            break
        elif dict_appearances[restaurant_name[0]] > 55 * len(list_query):
            matching_restaurants.append(
                name_restaurant_dict[restaurant_name[0]])

    return matching_restaurants


def find_restaurants(query: str, restaurants: Restaurants) -> Restaurants:
    """Donada una cerca (str) retorna la llista dels 12 restaurants que millor
    la satisfan
    """
    matching_restaurants: Restaurants = []
    # Obtenim una llista amb les paraules de la cerca
    list_query: List[str] = query.split(";")
    # Cerca multiple o única fent ús també de la distància de Levenshtein
    matching_restaurants = find_matching_restaurants(list_query, restaurants)
    return matching_restaurants[:12]
