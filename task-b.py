import requests
import prettytable # to print matrix in console :D
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

type_names = [] # stores all type names fetched from PokeAPI
effectiveness_matrix = [] # the matrix to be constructed
type_to_index = {} # dictionary maps type names to matrix indices

# =============================================
#        INITIALISATION FUNCTIONS
# =============================================

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

def get_defender_weakness(defender_type):
    """Get all damage multipliers for a given pokemon type under attack"""
    if defender_type not in type_to_index:
        return None
    defender_index = type_to_index[defender_type]
    defender_row = effectiveness_matrix[defender_index]

    return {type_names[i]: defender_row[i] for i in range(len(defender_row))}

def get_attacker_strength(attacker_type):
    "Get damage multipliers for a given pokemon type attacking"
    if attacker_type not in type_to_index:
        return None
    attacker_index = type_to_index[attacker_type]
    attacker_col = effectiveness_matrix[:][attacker_index]
    return {type_names[i]: attacker_col[i] for i in range(len(attacker_col))}

# =======================================================
#                BUILD AND RUN HTTP SERVER       
# =======================================================

class pokemonEffectivenessAPI(BaseHTTPRequestHandler):
    """HTTP Request Handler"""
    def do_GET(self):
        """Handle GET Requests"""
        if not type_names:
            self.send_error(500, "Matrix not initialised")
            return None
        
        # Parse URL and passed params
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        response = {}
        # Extract parameters
        try:
            attacker = params.get('attacker', [None])[0]
            defender = params.get('defender', [None])[0]

            if attacker and defender: 
                # First endpoint => Return Damage multiplier for attacker attacking defender
                multiplier = get_effectiveness(attacker, defender)
                if multiplier is not None:
                    response = {
                        'attacker': attacker,
                        'defender': defender,
                        'multiplier': multiplier,
                    }
                else:
                    self.send_error(400, "Invalid pokemon type!")
            elif defender:
                # Second endpoint 
                weakness = get_defender_weakness(defender)
                if weakness is not None:
                    response = {
                        "defender": defender,
                        "damage_from": weakness,
                    }
                else:
                    self.send_error(400, "Invalid defender_type!")
            elif attacker:
                # Third endpoint
                strength = get_attacker_strength(attacker)
                if strength is not None:
                    response = {
                        "attacker": attacker,
                        "damage_to": strength,
                    }
                else:
                    self.send_error(400, "Invalid attacker type!")
            else:
                # Send help!
                response = {
                    "available_types": type_names,
                    "help_info" : '''
Usage guide: 
1. Attack-Defense Analysis: https://localhost:8000?attacker={attacker_type}&defender={defender_type}
2. Defender Analysis: https://localhost:8000?defender={defender_type}
3. Attacker Analysis: https://localhost:8000?attacker={attacker_type}'''
                }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*') # Allow CORS
            self.end_headers()

            response_json = json.dumps(response, indent=2)
            self.wfile.write(response_json.encode())

        except Exception as e:
            self.send_error(500, f"Server Error : {str(e)}")


# ==============================================================
#                      RUN SERVER
# =============================================================
def start_http_server(port=8000):
    """Function to run HTTP Server =>"""
    print('='*60)
    print(f"Starting HTTP Server on port {port}")
    server_address = ('', port)
    httpserver = HTTPServer(server_address, pokemonEffectivenessAPI)
    print(f"Server running at http://localhost:{port}")
    print("API Endpoints:")
    print(f"\tSpecific matchup: http://localhost:{port}/?attacker=fire&defender=grass")
    print(f"\tDefender analysis: http://localhost:{port}/?defender=grass")
    print(f"\tAttacker analysis: http://localhost:{port}/?attacker=fire")
    print(f"\tAvailable types: http://localhost:{port}/")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    try: 
        httpserver.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server...")
        httpserver.shutdown()
        httpserver.server_close()

def main():
    # Build the type matrix
    print("=> Fetching Data...")
    data = fetch_all_types()

    print("=> Constructing Effectiveness Matrix...")
    matrix = construct_matrix(data)
    
    #Display the damage matrix in console
    display_matrix(matrix)

    # Start HTTP Server
    start_http_server()

if __name__ == "__main__":
    main()
            