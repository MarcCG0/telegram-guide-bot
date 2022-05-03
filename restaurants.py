from dataclasses import dataclass
from typing import Optional, TextIO
from typing import List, Tuple
import pandas as pd
import easyinput as ei
# Llibreria alternativa al fuzzy search.
import fuzzywuzzy as fw # Per instalar el packet : pip3 install fuzzywuzzy i pip3 install fuzzywuzzy[speedup], Source: https://pypi.org/project/fuzzywuzzy/
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


Coordinate = str  # Definim una coordenada com un enter.

@dataclass
class Restaurant:
    name: str
    street_name: str
    street_number : str
    neighbourhood: str
    district: str
    zip_code: int
    town: str
    type : str
    x_coord : Coordinate
    y_coord : Coordinate

Restaurants = List[Restaurant] # Definim Restaurants com una llista de Restaurants.

def read() -> Restaurants:
    """A partir de la informació que conté el fitxer csv amb la base de dades dels restaurants, retorna un llistat de tots els restaurants"""

    #Fitxer on es troba tota l'informació referent als Restaurants

    f = open('restaurants.csv' , 'r')

    #Assignem a cada atribut el nom de la columna que li pertoca en el fitxer restaurants.csv

    name : str = 'name'
    street_name : str = 'addresses_road_name'
    street_number : str = 'addresses_start_street_number'
    neighbourhood : str= 'addresses_neighborhood_name'
    district: str = 'addresses_district_name'
    zip_code : str= 'addresses_zip_code'
    town : str= 'addresses_town'
    type : str = 'secondary_filters_name'
    x_coord : str = 'geo_epgs_4326_x'
    y_coord : str = 'geo_epgs_4326_y'

    #Creem un dataFrame que conté tota la informació de les columnes que ens interesen

    df = pd.read_csv(f, usecols=[name, street_name, street_number, neighbourhood, district, zip_code, town, type, x_coord, y_coord])

    restaurants : List[Restaurant] = []

    for row in df.itertuples(): # Recorregut de les columnes que hem escollit previament del fitxer

        # Creem un restaurant amb la informació de la fila en la que ens trobem tractant al bucle i afegim aquest restaurant a la nostra llista de restaurants.
        restaurant = Restaurant(row.name, row.addresses_road_name, row.addresses_start_street_number, row.addresses_neighborhood_name, row.addresses_district_name, row.addresses_zip_code, row.addresses_town, row.secondary_filters_name, row.geo_epgs_4326_x, row.geo_epgs_4326_y)
        restaurants.append(restaurant)
    return restaurants      # Un cop allistats tots els restaurants, els retornem.


def find(query: str, restaurants : Restaurants) -> Restaurants:
    """A partir d'un string d'entrada, retorna un llistat dels restaurants que contenen informació versemblant a aquest string en algun dels seus camps. """
    desired_restaurants : Restaurants = []

    for restaurant in restaurants:
        features = [str(restaurant.name), str(restaurant.street_name), str(restaurant.street_number), str(restaurant.neighbourhood), str(restaurant.district), str(restaurant.zip_code), str(restaurant.town)]
        #Recorrem tots els camps d'un restaurant donat.
        for feature in features:
            Ratio = fuzz.partial_ratio(query.lower(), feature.lower())

            if Ratio == 100: # Si alguna de les paraules que s'han introduït es troben en algun subconjunt de l'string d'entrada l'afegim a la llista de desired_restaurants
                desired_restaurants.append(restaurant)
                break

    return desired_restaurants




def main() :
    restaurants_barcelona = read()
    query = ei.read(str)
    print(find(query, restaurants_barcelona))

main()
