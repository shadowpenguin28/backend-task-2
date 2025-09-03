import requests
import os
import sys
import json

def get_pokemon_data(pokemon_name_or_id):
    """Fetch pokemon data via Name or ID, returns data in a python dictionary.
    returns None if an error occurs. """

    request_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name_or_id.lower()}"

    try:
        response = requests.get(request_url)
        response.raise_for_status() # raise an error for bad response
        return response.json()
    except: # Error in fetching data
        print("An error occurred while trying to fetch data.")
        return None

def get_species_data(pokemon_data):
    """Returns the species data from the species url of the respective pokemon."""
    species_url = pokemon_data['species']['url']
    try:
        response = requests.get(species_url)
        response.raise_for_status()
        return response.json()
    except:
        print("An error occurred while fetching pokemon species (mythical/legendary).")
        return None

def extract_data(pokemon_data, species_data):
    """Extracts 1) Abilities, 2) Types, 3) is_mythical, 4) is_legendary"""
    # if no data
    if not pokemon_data or not species_data:
        return None
    
    # abilities
    abilities = []
    for ability in pokemon_data["abilities"]:
        abilities.append({
            "name": ability['ability']['name'],
            "is_hidden": ability["is_hidden"],
        })

    # types
    types = []
    for type in pokemon_data["types"]:
        types.append(type["type"]["name"])
    
    is_mythical = species_data["is_mythical"]
    is_legendary = species_data["is_legendary"]
    
    return {
        "abilities": abilities,
        "types": types,
        "is_mythical": is_mythical,
        "is_legendary": is_legendary,
    }

def read_file(filename):
    """Reads filename/filepath and takes pokemon names as input"""
    if not os.path.exists(filename): # if file is not found
        print(f"'{filename}' not found!")
        return None
    pokemon_list = []
    
    with open(filename, 'r') as f:
        for line in f:
            pokemon = line.strip()
            if pokemon: # line is not empty
                pokemon_list.append(pokemon)
    
    return pokemon_list

def create_json(pokemon_list, res_file_name="output.json"):
    pokemon_json = {}

    for pokemon in pokemon_list:
        # PROCESS pokemon
        pokemon_data = get_pokemon_data(pokemon)
        species_data = get_species_data(pokemon_data)
        filtered_pokemon_info = extract_data(pokemon_data, species_data)

        if not filtered_pokemon_info:
            print(f"Skipping {pokemon} due to possible API/processing errors!")
            continue

        name = pokemon_data["name"]
        pokemon_json[name] = filtered_pokemon_info

    with open(res_file_name, 'w') as result_file:
        json.dump(pokemon_json, result_file, indent=4)
    
    print(f"Created output json: {res_file_name}")
    return pokemon_json

def main():
    if len(sys.argv) < 2:
        print("Usage: python task-a.py <input_filename> <output_filename>")
        print("Example: python task-a.py pokemon_data.json")
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]

    pokemon_list = read_file(input_filename)
    if not pokemon_list:
        print(f"No pokemons in {input_filename} or file does not exist.")
        return None

    print(f"Processing {len(pokemon_list)} pokemons!")
    pokemon_json = create_json(pokemon_list, output_filename)

    print(f"Successfully processed {len(pokemon_json)} out of {len(pokemon_list)} pokemon(s)!")

if __name__ == "__main__":
    main()

    

    






        



