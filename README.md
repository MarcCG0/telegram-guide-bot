# MetroNyan

Tria restaurant i vés-hi en metro 🍕 🚇

*MetroYourRestaurant*, el bot que et porta en metro al restaurant que tu vols!

![images/citydraw.png](images/citydraw.png)

## Introducció

El projecte consisteix en un bot de Telegram® desenvolupat amb Python que té com a objectiu guiar l'usuari fins al restaurant que desitja el més rapid possible ja sigui a peu i/o en metro. Això sí, sempre i quan sigui dins de Barcelona!

**INSERTAR FOTO EXEMPLE CONVERSA**

--nosesical------------------------

Per poder dur a terme hem hagut d'usar les següents dades:
- El mapa dels carrers de Barcelona obtingut d'[Open Street Map](https://www.openstreetmap.org).

- La [llista d'equipaments de restaurants de la ciutat de Barcelona](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/equipament-restaurants).

- La [Llista de les estacions de Metro de TMB](https://developer.tmb.cat/data/estacions).

- La [Llistat dels accessos de Metro de TMB](https://developer.tmb.cat/data/accessos).

------------------------xdf-------------

## Instruccions
Per tal de poder utilitzar el bot, primer l'usuari haurà de tenir instal·lada l'aplicació Telegram®. Posteriorment, s'haurà de registrar i a l'apartat de **xats** haurà de buscar `MetroYourRestaurant` per poder rebre les indicacions correctes per arribar al restaurant desitjat.

Per inicialitzar el bot haurà d'introduir la comanda `/start`, a més podrà obtenir informació addicional de totes les comandes disponibles introduint `/help`, aquesta li mostrarà un llistat i només cal que segueixi les indicacions que el mateix bot li anirà proporcionant.

#### Comandes disponibles
`/start` Inicialitza el bot

`/help` Mostra llistat de les comandes disponibles i la funcionalitat d'aquestes

`/author` Retorna els noms dels autors del projecte

`/find <query>` Retorna una llista de màxim 12 restaurants que satisfan la cerca feta per l'usuari

`/info <number>` Mostra la informació del restaurant especificat amb el número de la llista anterior

`/guide <number>` Mostra el camí més ràpid des d'on es troba l'usuari fins al restaurant demanat (a través del número amb el que s'identifica a la llista anterior)

`/travel_time` Diu el temps que es trigarà a fer la última ruta que s'ha fet amb */guide <number>*

## Requeriments
Per tal de poder utilitzar sense cap problema el bot implementat, caldrà instal·lar les llibreries adjuntes en el fitxer `requirements.txt`.

## Funcionalitat dels moduls
### Restaurants
El mòdul `restaurants.py` recull la definició de la classe Restaurant amb tots els atributs que necessitarem durant tot el projecte.

```python3
@dataclass
class Restaurant: ...
    
Restaurants: TypeAlias = List[Restaurant]
```

També és l'encarregat de llegir totes les dades necessàries del fitxer **restaurants.csv** i assignar cada atribut la columna del fitxer que li pertoca. També trobem la implementació dels diferents tipus de cerques (multiple i difusa) per tal de que quan l'usuari busqui un restaurant, el bot sigui capaç de retornar-li una llista que la satisfaci.
    
```python3
def find_restaurants(query: str, restaurants: Restaurants) -> Restaurants: ...
def get_results_by_fuzzysearch(query: str, restaurants: Restaurants,
                               satisfying_query: Restaurants) -> Restaurants: ...
def find_multiple(query: List[str], restaurants: Restaurants) -> Restaurants: ...
```
La cerca difusa, ens permetrà trobar resultats semblants a les cerques introduides, és a dir, mitjançant un cert ratio (i en funció d'aquest aplicarà la distància de Levenshtein) decidirà si el resultat trobat per la cerca és un bon resultat o no. 
La múltiple ens permetrà fer cerques que continguin més d'una paraula.
    
### Metro
El mòdul `metro.py` recull la definició de les següents classes: Station, Access, Edge.
```python3
@dataclass
class Station:
    ...

@dataclass
class Access:
    ...

@dataclass
class Edge:
    ...

Point: TypeAlias = Tuple[float, float]  # punt sobre el pla de coordenades de Barcelona
MetroGraph: TypeAlias = nx.Graph    
Stations: TypeAlias = List[Station]
Accesses: TypeAlias = List[Access]
``` 
L'objectiu d'aquest mòdul és crear el graf de la xarxa de metro de Barcelona. Per poder aconseguir-ho primer s'ha implementat una funció per obtenir les dades necessàries dels fitxers **estacions.csv** i **accessos.csv** i assignar cada atribut la columna del fitxer que li pertoca. 
    
```python3
def read_stations() -> Stations: ...
def read_accesses() -> Accesses: ...
```     
Per tal de poder afegir els nodes i les arestes al graf del metro, s'han implementat les següents funcions que afegeixen els nodes i les arestes de les estacions, els nodes i arestes dels accessos i les arestes de transbord. Aquesta última tracta les atrestes de tipus "Enllaç".
    
En aques procés d'afegir tota aquesta informació alhora també ja estem obtenint i guardant dades i informació que ens serà útil per poder continuar amb la realització del projecte, com per exemple el color quu han de tenir les arestes segons de quin tipus siguin o per exemple la distància entre dues estacions, entre d'altres. 

```python3
def add_nodes_and_edges_stations(station1: Station, station2: Station,
                                 metro_graph: MetroGraph) -> None: ...
def add_edges_accesses(
        qty_stations: int, all_stations: Stations, all_accesses: Accesses,
        metro_graph: MetroGraph) -> None: ...
def add_nodes_accesses(all_accesses: Accesses,
                       metro_graph: MetroGraph) -> None: ...
def add_transbording_edges(all_stations: Stations,
                           metro_graph: MetroGraph) -> None: ...
```
També han estat implementades funcions auxiliars amb les quals s'obtindran les coordenades x,y d'un punt donat i la distància entre dos punts point1 i point2 mitjançant "haversine".
    
```python3
def get_coordinates(info: str) -> Point: ...
def get_distance(point1: Point, point2: Point) -> float: ...
```

En quant a la presentació del graf del metro de Barcelona, han estat implementades diverses funcions les quals ens permeten imprimir un graf més senzill que només ens mostra nodes tots blaus i arestes totes negres. Després, afegint els nodes i les arestes del graf (i fent ús de la informació que contenen aquests) s'aconsegueix que aquest s'imprimeixi ja amb les arestes del color corresponent, sobre del mapa de la ciutat de Barcelona amb l'ajuda d'StaticMap.
    
```python3
def show(Metro_Graph: MetroGraph) -> None: ... # graf "senzill" amb les arestes negres i els nodes blaus
def plot(g: MetroGraph) -> None: ... # desa el mapa de la ciutat com a imatge
def add_lines(m: StaticMap, g: MetroGraph) -> StaticMap: ... # afegeix les arestes del graf al StaticMap
def add_nodes(m: StaticMap, g: MetroGraph) -> StaticMap: ...  # afegeix els nodes del graf al StaticMap 
```

Per a la creació del graf, només s'ha implementat una funció que retorna el graf del metro de Barcelona amb la informació dels dos arxius llegits anteriorment.
    
```python3
def get_metro_graph() -> MetroGraph: ...
```

### City
El mòdul `city.py` recull la definició dels següents tipus:
```python3
CityGraph: TypeAlias = nx.Graph  # graf no dirigit de networkx
OsmnxGraph: TypeAlias = nx.MultiDiGraph  **#especif**
Coord: TypeAlias = Tuple[float, float]  # (latitude, longitude)
NodeID: TypeAlias = Union[int, str]
Path: TypeAlias = List[NodeID]
```

La finalitat d'aquest mòdul és fusionar dos grafs, el graf del metro de Barcelona que hem creat amb el mòdul `metro.py` i el graf dels carrers de la ciutat de Barcelona, aquest no el creem nosaltres sinó que utilitzem l'OsmnxGraph com un *MultiDiGraph* de `networkx`, per tal d'aconseguir-lo (que en el nostre cas, donada una ciutat, és capaç de crear el graf dels carrers d'aquesta, ja que és el que nosaltres volem).
    
Per a la creació i mostra el graf dels carrers de Barcelona (*OsmnxGraph*), s'han implementat diverses funcions on es comença creant aquest graf com s'ha mencionat prèviament, amb l'ajuda del mòdul `osmnx` seguidament el guardem en un fitxer i finalment es retorna el graf guardat.

```python3
def get_osmnx_graph() -> OsmnxGraph: ... # retorna el graf dels carrers
def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None: ... # guarda el graf
def load_osmnx_graph(filename: str) -> OsmnxGraph: ...  # retorna el graf guardat
```

Per a la creació i mostra del *CityGraph*, s'afegirà el graf del metro *MetroGraph* i el graf dels carrers de la ciutat *StreetGraph*, a més també s'observa que cal enllaçar els accessos del metro amb el node més proper del *StreetGraph*, per tant s'implementa una altra funció amb aquest fi. A més també cal saber les coordenades dels accessos, ja que prèviament s'havien definit com y, x i ara les necessitem com x, y. Finalment construim el graf de la ciutat fent crides a cadascuna de les funcions definides anteriorment. També s'implementa una funció que estableix les velocitats mitjanes a la qual una persona camina i la del metro.

```python3
def get_travel_time(type: str, distance: float) -> float: ... # establir velocitats
def add_Metro_Graph(City_Graph: CityGraph, Metro_Graph: MetroGraph) -> None: ... # afegir el graf del metro
def add_Street_Graph(City_Graph: CityGraph, Street_Graph: OsmnxGraph) -> None: ... # afegir el graf dels carrers
def get_acces_coords(Metro_Graph: MetroGraph, y: List, x: List,
                     access_nodes: List) -> None: ... # modifica les coordenades per tal de tenir x, y
def link_Street_with_Access(City_Graph: CityGraph, Street_Graph: OsmnxGraph,
                            Metro_Graph: MetroGraph) -> None: ... # enllaç d'accessos i node més proper del StreetGraph
def build_city_graph(Street_Graph: OsmnxGraph,
                     Metro_Graph: MetroGraph) -> CityGraph: ... # fusio dels dos grafs
```

Per poder guardar i obtenir el *CityGraph*, s'ha fet us de funcions similars a les implementades per a la creació i mostra de l'*OsmnxGraph*, es comença creant l'*StreetGraph*, cridant les diferents funcions que s'han implementat abans per crear la fusió entre el graf del metro i el dels carrers de Barcelona. Després es guarda en un fitxer i finalment retorna el graf gurdat en el fitxer.

```python3
def get_city_graph() -> CityGraph: ... # retorna la fusió dels dos grafs
def save_city_graph(City_Graph: CityGraph, filename: str) -> None: ... # desa el CityGraph a l'arxiu filename
def load_city_graph(filename: str) -> CityGraph: ... # Retorna el graf guardat al fitxer filename
```

Per mostrar-lo, s'ha seguit una metodologia semblant a el que s'ha fet per la presentació del graf del metro. S'han implementat varies funcions per tal d'aconseguir dibuixar el *CityGraph* per pantalla i després es millora aquesta mostra desant aquest graf sobre el mapa de Barcelona, gràcies a l'ajuda de l'StaticMap. Per poder aconseguir mostrar-lo sobre la imatge del mapa de Barcelona, hem d'afegir els nodes i les arestes del graf de la ciutat d'aquest sobre el mapa.

```python3
def show_city(City_Graph: CityGraph) -> None: ... # dibuixa per pantalla el CityGraph
def plot_city(g: CityGraph, filename: str) -> None: ... # guarda el citygraph dins d'un arxiu
def add_city_nodes(m: StaticMap, g: CityGraph) -> StaticMap: ... # afegeix els nodes del graf a l'StaticMap
def add_city_lines(m: StaticMap, g: CityGraph) -> StaticMap: ... # afegeix les arestes del graf a l'StaticMap
```

Per tal de poder trobar el camí més ràpid que portarà l'usuari al restaurant desitjat, s'han creat dues funcions. La primera que retorna el camí més rapid donats un destí i un origen i la segona que calcula el temps de durada de la ruta.
    
```python3
def find_path(Street_Graph: OsmnxGraph, City_Graph: CityGraph, src: Coord, dst: Coord) -> Path: ...
def get_time_path(Path: Path, City_Graph: CityGraph) -> float: ...
```

Per pintar el camí que l'usuari ha de seguir per arribar al seu destí, s'ha creat una funció que dibuixa el camí sobre el mapa de Barcelona amb ajuda de l'StaticMap i per poder aconseguir-ho s'han afegit els nodes i les arestes del graf sobre el mapa.

```python3
def plot_path(City_Graph: CityGraph, path: Path, filename: str) -> None: ... # dibuixa el camí
def add_path_lines(m: StaticMap, g: CityGraph, path: Path) -> StaticMap: ... # afegeix les arestes
def add_path_nodes(m: StaticMap, g: CityGraph, path: Path) -> StaticMap: ... # afegeix els nodes
```
    
### Bot
L'objectiu del mòdul `bot.py` és donades unes comandes per part d'un usuari, que aquest sigui capaç d'entendre-les i guii l'usuari al restaurant que desitja indicant-li la ruta més ràpida ja sigui en metro i/o a peu.
Per poder aconseguir-ho s'han definit diferents funcions. 
Primer ha d'obtenir el graf de la ciutat. Després s'ha continuat definint funcions per a donar resosta a les comandes introduides per l'usuari.
    
```python3
# les comandes estan especificades a l'inici
def start(update, context): ...
def help(update, context): ...
def author(update, context): ...
def find(update, context): ...
def info(update, context): ...
def guide(update, context): ...
def time(update, context): ...
``` 

I també s'han creat algunes auxiliars per acabar de completar les anteriors.

```python3
def initialize(update, context): ... # inicialitza les dades per poder comprovar si s'han efectuat  comandes
def indicate_path(path: Path, update, context) -> None: ... # dona indicacions per a facilitar el camí a l'usuari
def where(update, context): ... # emmagatzema la ubicació enviada per l'usuari
```

A més, si l'usuari introdueix comandes amb valors incorrectes, és a dir, que no són valids s'envia un missatge informant del problema.
    
Finalment, es guarda en un fitxer tipus *.txt* el token pr poder modificar i configurar el bot i s'inicialitza l'updater i el dispatcher. S'ha acabat vinculant les comandes amb les funcions que han d'invocar cada una de les comandes i s'engega el bot.
    

## Informació addicional
Totes les dades utilitzades per a la realització del bot, han estat extretes dels fitxers de dades els quals es poden trobar adjunts al projecte.

En cas que l'usuari es trobi fora de Barcelona i enviï la seva ubicació real, es crearà una aresta fins al node mes proper que sí estigui inclòs al graf de la ciutat de Barcelona i d'allà ja farà el camí correcte.
    
## Autors
Aquest projecte ha estat creat pel Marc Camps i la Carlota Gozalbo, estudiants del 1r curs del Grau en Ciència i Enginyeria de Dades a la Universitat Politècnica de Catalunya.
    
