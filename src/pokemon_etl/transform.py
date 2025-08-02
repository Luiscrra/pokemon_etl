import json
import logging
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def load_species(raw_species_path, generations):
    """Carga las especies de Pokémon desde archivos JSON crudos.
    Args:
        raw_species_path (Path): Ruta donde se encuentran los archivos crudos de especies.
        generations (list): Lista de generaciones a cargar.
    Returns:
        list: Lista de especies de Pokémon.
    """
    species = []
    for generation in generations:
        try:
            with open(f"{raw_species_path}/{generation}.json", "r", encoding="utf-8") as file:
                pokemon_gens = json.load(file)
                species.extend(pokemon_gens)
            logging.info(f"Se han cargado {len(pokemon_gens)} especies de la generación {generation}.", extra={"phase": "TRANSFORM"})
        except FileNotFoundError:
            logging.error(f"Archivo no encontrado: {raw_species_path}/{generation}.json", extra={"phase": "TRANSFORM"})
            continue
        except json.JSONDecodeError:
            logging.error(f"Error al decodificar JSON en el archivo: {raw_species_path}/{generation}.json", extra={"phase": "TRANSFORM"})
            continue
    return species

def transform_species(raw_species_path, generations):
    """Transforma las especies de Pokémon cargadas desde archivos JSON crudos.
    Args:
        raw_species_path (Path): Ruta donde se encuentran los archivos crudos de especies.
        generations (list): Lista de generaciones a transformar.
    Returns:
        pd.DataFrame: DataFrame con las especies transformadas.
    """    
    pokemon_species= load_species(raw_species_path, generations)
    species_data = []
    for species in pokemon_species:
        try:
            if not isinstance(species, dict):
                raise ValueError("El objeto no es un diccionario.")
        except ValueError as e:
            logging.error(f"Error al procesar la especie: {e}", extra={"phase": "TRANSFORM"})
            continue
        extracted_data = {
            "species_id": species["id"],
            "name": species["name"],
            "color": species["color"]["name"],
            "habitat": species["habitat"]["name"] if species.get("habitat") else None,
            "generation": species["generation"]["name"],
            "previous_evolution": species["evolves_from_species"]["name"] if species.get("evolves_from_species") else None,
            "is_mythical": species["is_mythical"],
            "is_baby": species["is_baby"],
            "is_legendary": species["is_legendary"],
            "nat_pokedex_entry" : next(
                (entry["entry_number"] for entry in species["pokedex_numbers"] if entry["pokedex"]["name"] == "national"),
                None
            )
        }
        species_data.append(extracted_data)
    df_species = pd.DataFrame(species_data)
    return df_species

def load_pokemons(raw_pokemon_path):
    """Carga los Pokémon desde archivos JSON crudos.
    Args:
        raw_pokemon_path (Path): Ruta donde se encuentran los archivos crudos de Pokémon.
    Returns:
        list: Lista de Pokémon.
    """
    pokemons = []
    ruta = Path(raw_pokemon_path)
    files = [f.name for f in ruta.iterdir() if f.is_file()]
    for file in files:
        try:
            with open(f"{raw_pokemon_path}/{file}", "r", encoding="utf-8") as file:
                page_data = json.load(file)
                pokemons.extend(page_data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Archivo no encontrado: {file}")
        except json.JSONDecodeError:
            logging.error(f"Error al decodificar JSON en el archivo: {file}")
            continue
    logging.info(f"Se han cargado {len(pokemons)} Pokémon desde los archivos crudos.", extra={"phase": "TRANSFORM"}) 
    return pokemons

def transform_pokemones(raw_pokemon_path):
    """Transforma los Pokémon cargados desde archivos JSON crudos.
    Args:
        raw_pokemon_path (Path): Ruta donde se encuentran los archivos crudos de Pokémon.
    Returns:
        pd.DataFrame: DataFrame con los Pokémon transformados.
    """
    pokemons= load_pokemons(raw_pokemon_path)
    pokemons_data = []
    for pokemon in pokemons:
        extracted_data = {
            "pokemon_id": pokemon["id"],
            "name": pokemon["name"],
            "hp_base_stat" : next(
                (stats["base_stat"] for stats in pokemon["stats"] if stats["stat"]["name"] == "hp"),
                None
            ),
            "attack_base_stat" : next(
                (stats["base_stat"] for stats in pokemon["stats"] if stats["stat"]["name"] == "attack"),
                None
            ),
            "defense_base_stat" : next(
                (stats["base_stat"] for stats in pokemon["stats"] if stats["stat"]["name"] == "defense"),
                None
            ),
            "special_attack_base_stat" : next(
                (stats["base_stat"] for stats in pokemon["stats"] if stats["stat"]["name"] == "special-attack"),
                None
            ),
            "special_defense_base_stat" : next(
                (stats["base_stat"] for stats in pokemon["stats"] if stats["stat"]["name"] == "special-defense"),
                None
            ),
            "speed_base_stat" : next(
                (stats["base_stat"] for stats in pokemon["stats"] if stats["stat"]["name"] == "speed"),
                None
            ),
            "type_1": pokemon["types"][0]["type"]["name"] if pokemon["types"] else None,
            "type_2": pokemon["types"][1]["type"]["name"] if len(pokemon["types"]) > 1 else None
        }
        pokemons_data.append(extracted_data)
    df_pokemons = pd.DataFrame(pokemons_data)
    return df_pokemons

def join_species_pokemons(raw_species_path, raw_pokemon_path, generations, processed_path, parquet_name, csv_name):
    """Une los DataFrames de especies y Pokémon, y guarda el resultado en un archivo Parquet.
    Args:
        raw_species_path (Path): Ruta donde se encuentran los archivos crudos de especies.
        raw_pokemon_path (Path): Ruta donde se encuentran los archivos crudos de Pokémon.
        generations (list): Lista de generaciones a procesar para las especies.
        processed_path (Path): Ruta donde se guardará el archivo Parquet resultante.
    Returns:
        None
    """
    df_species= transform_species(raw_species_path, generations)
    df_pokemons = transform_pokemones(raw_pokemon_path)
    df_combined = pd.merge(df_pokemons, df_species, left_on="pokemon_id", right_on="species_id", how="right")
    table = pa.Table.from_pandas(df_combined)
    pq.write_table(table, f"{processed_path}/{parquet_name}", compression="snappy")
    df_combined.to_csv(f"{processed_path}/{csv_name}", index=False)
    logging.info(f"Se ha guardado el DataFrame en formato parquet y CSV con {len(df_combined)} registros en {processed_path}", extra={"phase": "TRANSFORM"})
