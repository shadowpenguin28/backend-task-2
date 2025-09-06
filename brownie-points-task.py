import requests

def get_pokemon_type(pokemon_name_or_id):
    request_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name_or_id.lower()}"
    try:
        response = requests.get(request_url)
        response.raise_for_status()

        response = response.json()
        types = []
        for type in response["types"]:
            types.append(type["type"]["name"])
        print(f"Retrieved types: {types}")
        return types
    except Exception as e:
        print(f"An error occurred while fetching pokemon type! : {e}")
        return None

def get_damage_multipliers(pokemon_types):
    '''Takes a list of types and retrieves damage multipliers => 0x, 2x, 4x'''
    request_url = "http://localhost:8000/?defender={}"
    damages = []

    for pokemon_type in pokemon_types:
        type_damage_multiplier_url = request_url.format(pokemon_type)
        try:
            response = requests.get(type_damage_multiplier_url)
            response.raise_for_status()

            response = response.json()
            damages.append(response["damage_from"])
        except Exception as e:
            print(f"Error contacting local server: {e}")
            return None
    
    # go through and do the damage computation
    final = {}
    responseDict = {"0x": [], "2x": [], "4x": []}
    for damage_info in damages:
        for key in damage_info:
            if key in final and damage_info[key] != None:
                final[key] *= damage_info[key]
            else:
                final[key] = damage_info[key]
    for k in final:
        if final[k] == 0:
            responseDict["0x"].append(k)
        elif final[k] == 2:
            responseDict["2x"].append(k)
        elif final[k] == 4:
            responseDict["4x"].append(k)
    
    return responseDict
    
pokemon_name_or_id = input("Enter pokemon name/id: ")
if pokemon_name_or_id:
    pokemon_types = get_pokemon_type(pokemon_name_or_id)
if pokemon_types:
    damage_multipliers = get_damage_multipliers(pokemon_types)
if damage_multipliers:
    for damage_multiplier in damage_multipliers:
        print(f"{damage_multiplier} => {damage_multipliers[damage_multiplier] if damage_multipliers[damage_multiplier] else "Null"}")
else:
    print("Unable to retrieve damage multipliers/weaknesses")

