import requests
import prettytable # to print matrix in console :D
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

type_names = [] # stores all type names fetched from PokeAPI
effectiveness_matrix = [] # the matrix to be constructed
type_to_index = {} # dictionary maps type names to matrix indices

def fetch_all_types(): 
    """Fetch all the pokemon types and their urls"""
    request_url = f"https://pokeapi.co/api/v2/type/"
    response = requests.get(request_url).json()
    types_list = []
    type_data = {}

    for type in response['results']:

        type_name = type['name']
        type_url = type['url']
        types_list.append((type_name, type_url))

        type_info = requests.get(type_url)
        type_data[type_name] = type_info.json()["damage_relations"]
    return type_data
    
def construct_matrix(type_data):
    global type_names, effectiveness_matrix, type_to_index

    # initialise the global variables
    type_names = sorted(type_data.keys())
    matrix_size = len(type_names)

    type_to_index = {type_name : i for i, type_name in enumerate(type_names)} 
    effectiveness_matrix = [[1.0 for _ in range(matrix_size)] for _ in range(matrix_size)] 

    # loop over the data and construct the matrix
    for type_name, damage_relations in type_data.items():
        defense_index = type_to_index[type_name] # row index

        # process immunity "no_damage" (0x)
        for immunity in damage_relations["no_damage_from"]:
            attacking_type = immunity["name"]
            attacking_index = type_to_index[attacking_type] # column index
            effectiveness_matrix[defense_index][attacking_index] = 0.0

        # process resistance "half_damage_from" (0.5x)
        for resistance in damage_relations["half_damage_from"]:
            attacking_type = resistance["name"]
            attacking_index = type_to_index[attacking_type]
            effectiveness_matrix[defense_index][attacking_index] = 0.5
        
        # process weakness "double_damage_from" (2x)
        for weakness in damage_relations["double_damage_from"]:
            attacking_type = weakness["name"]
            attacking_index = type_to_index[attacking_type]
            effectiveness_matrix[defense_index][attacking_index] = 2.0
        
    # fix the matrix for unkown type
    # None values because nothing is known about these types
    unknown_index = type_to_index["unknown"]
    effectiveness_matrix[unknown_index] = [None for _ in range(matrix_size)] # set unknown row to None

    for row in effectiveness_matrix:
        row[unknown_index] = None # set column values for unknown to None

    # END OF CONSTRUCTION
    print(f"Constructed a {matrix_size}x{matrix_size} matrix with damage_relations")

def display_matrix(damage_matrix):
    table = prettytable.PrettyTable()
    table.field_names = ["Name"] + type_names

    for name in type_names:
        name_index = type_to_index[name]
        table.add_row([name] + effectiveness_matrix[name_index])

    print(table)

# =======================================================
#                MATRIX LOOKUP FUNCTIONS       
# =======================================================

def get_effectiveness(attacker_type, defender_type):
    """Get effectiveness between two types"""
    if attacker_type not in type_to_index or defender_type not in type_to_index:
        return None
    
    defender_index = type_to_index[defender_type]
    attacker_index = type_to_index[attacker_type]
    return effectiveness_matrix[defender_index][attacker_index]

