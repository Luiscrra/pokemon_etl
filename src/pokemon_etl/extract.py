import json
import logging
import asyncio
import aiohttp
from pathlib import Path

def create_directory(path):
    """Crea un directorio si no existe.
    Args:
        path (str): Ruta del directorio a crear.
    """
    from pathlib import Path
    Path(path).mkdir(parents=True, exist_ok=True)
    logging.info(f"Directorio creado: {path}", extra={"phase": "EXTRACT"})


async def fetch(session, url):
    """Realiza una solicitud GET asíncrona.
    Args:
        session (aiohttp.ClientSession): Sesión HTTP asíncrona.
        url (str): URL a la que se realiza la solicitud.
    Returns:
        dict: Respuesta JSON de la solicitud.
    """
    async with session.get(url) as response:
        if response.status != 200:
            error_msg = f"Error HTTP {response.status} al acceder a {url}"
            logging.error(error_msg, extra={"phase": "EXTRACT"})
            raise Exception(error_msg)
        return await response.json()
    
async def get_pokemon_gens(session, base_url, generation_list): 
    """Obtiene las generaciones de Pokémon desde la API.
    Args:
        session (aiohttp.ClientSession): Sesión HTTP asíncrona.
        base_url (str): URL base de la API.
        generation (list): lista de las generaciones a obtener.
    Returns:
        list: Lista de diccionarios con nombre y URLs de las generaciones a extraer.
    """
    url = f"{base_url}generation/"
    data = await fetch(session, url)
    return [{'nombre':generation['name'],'url':generation['url']} for generation in data['results'] if generation['name'] in generation_list]

async def get_pokemon_list(session, base_url, limit=2000):
    """Obtiene la lista de Pokémon desde la API, aplica un limite de 2000 pokemones para asegurar que se obtienen todos.
    Args:
        session (aiohttp.ClientSession): Sesión HTTP asíncrona.
        base_url (str): URL base de la API.
        limit (int): Número máximo de Pokémon a obtener.
    Returns:
        list: Lista de URLs de los Pokémon.
    """
    url = f"{base_url}pokemon?limit={limit}"
    data = await fetch(session, url)
    return [pokemon['url'] for pokemon in data['results']]

async def get_url_data(session, url):
    """Obtiene el contenido de una URL.
    Args:
        session (aiohttp.ClientSession): Sesión HTTP asíncrona.
        url (str): URL.
    Returns:
        dict: Contenido de la URL.
    """
    return await fetch(session, url)

async def get_raw_pokemons(raw_path, base_url):
    """Obtiene los datos crudos de los Pokémon y los guarda en archivos JSON.
    Args:
        raw_path (Path): Ruta donde se guardarán los datos crudos.
        base_url (str): URL base de la API.
    Returns:
        None
    """
    async with aiohttp.ClientSession() as session:
        logging.info("Obteniendo lista de Pokémon...", extra={"phase": "EXTRACT"})
        urls = await get_pokemon_list(session, base_url)

        chunk_size = 50  # número de requests concurrentes
        for i in range(0, len(urls), chunk_size):
            chunk = urls[i:i + chunk_size]
            tasks = [get_url_data(session, url) for url in chunk]
            results = await asyncio.gather(*tasks)
            
            # Guardar cada lote en un archivo
            page = i // chunk_size + 1
            with open(f"{raw_path}/pokemon_page_{page}.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4)
            
            logging.info(f"Lote {page} guardado ({len(results)} Pokémon).", extra={"phase": "EXTRACT"})

async def get_raw_species(raw_path, base_url, generation_list):
    """Obtiene los datos crudos de las especies de Pokémon por generación y los guarda en archivos JSON.
    Args:
        raw_path (Path): Ruta donde se guardarán los datos crudos.
        base_url (str): URL base de la API.
        generation_list (list): Lista de generaciones a obtener.
    Returns:
        None
    """
    async with aiohttp.ClientSession() as session:
        logging.info("Obteniendo lista de generaciones...", extra={"phase": "EXTRACT"})
        generations = await get_pokemon_gens(session, base_url, generation_list)
        for generation in generations:
            logging.info(f"Descargando {generation['nombre']} desde: {generation['url']}", extra={"phase": "EXTRACT"})
            menu = await get_url_data(session, generation['url'])

            pokemones = []
            for pokemon in menu["pokemon_species"]:
                details = await get_url_data(session, pokemon["url"])
                pokemones.append(details)

            with open(raw_path / f"{generation['nombre']}.json", "w", encoding="utf-8") as fout:
                json.dump(pokemones, fout, indent=4)
            logging.info(f"Generación {generation['nombre']} guardada en {raw_path}", extra={"phase": "EXTRACT"})

