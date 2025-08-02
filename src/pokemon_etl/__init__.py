from datetime import datetime
import logging
import asyncio
from pokemon_etl.config_manager import ConfigManager
from pokemon_etl.extract import get_raw_pokemons, get_raw_species
from pokemon_etl.transform import join_species_pokemons
from pokemon_etl.load import load_pokemons_to_db

start_time = datetime.now()

if __name__ == "__main__":

    # Cargar la configuración
    # Se obtiene la hora de inicio
    start_time = datetime.now()
    # Se crea una instancia de ConfigManager para manejar la configuración del ETL, se le pasa la hora de ini
    configuracion = ConfigManager(start_time)
    config_file_path = configuracion.config_file
    # Se obtienen parametros de la API
    base_url = configuracion.api_base_url
    generations = configuracion.generations
    # Se obtienen las rutas de los archivos
    raw_pokemon_path = configuracion.raw_pokemon_path
    raw_species_path = configuracion.raw_species_path
    processed_path = configuracion.processed_path
    logs_path = configuracion.logs_path
    # Se obtienen los nombres de los archivos
    parquet_name = configuracion.parquet_name
    csv_name = configuracion.csv_name
    # Se obtienen los parametros de la base de datos
    db_user = configuracion.db_user
    db_password = configuracion.db_password
    db_host = 'localhost'#configuracion.db_host
    db_name = configuracion.db_name
    db_port = configuracion.db_port

    logfilename = f"{logs_path}/{start_time.strftime('%m%Y')}/etl_{start_time.strftime('%d%m%Y_%H%M%S.log')}"

    # Configuración del logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - [%(phase)s] - %(message)s")
    # Handler para archivo
    file_handler = logging.FileHandler(logfilename)
    file_handler.setFormatter(formatter)
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    # Agregar handlers al logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.info(f"Inicia proceso {start_time.strftime('%Y-%m-%d %H:%M:%S')}", extra={"phase": "ETL"})
    logging.info(f"Directorio de logs: {logs_path}", extra={"phase": "ETL"})
    logging.info(f"Directorio de especies crudas: {raw_species_path}", extra={"phase": "ETL"})
    logging.info(f"Directorio de Pokemon crudos: {raw_pokemon_path}", extra={"phase": "ETL"})
    logging.info(f"Directorio archivo config: {config_file_path}", extra={"phase": "ETL"})
    logging.info(f"URL base de la API: {base_url}", extra={"phase": "ETL"})
    logging.info(f"Generaciones a procesar: {generations}", extra={"phase": "ETL"})
    logging.info(f"Parámetros de conexión a la base de datos: user={db_user}, host={db_host}, dbname={db_name}, port={db_port}", extra={"phase": "ETL"})

    logging.info("Inicia el proceso de extraccion de datos crudos.", extra={"phase": "ETL"})
    asyncio.run(get_raw_species(raw_species_path, base_url, generations))
    asyncio.run(get_raw_pokemons(raw_pokemon_path, base_url))
    logging.info(f"Finaliza proceso de extraccion {start_time.strftime('%Y-%m-%d %H:%M:%S')}", extra={"phase": "ETL"})

    logging.info("Inicia el proceso de transformación de datos crudos.", extra={"phase": "ETL"})
    join_species_pokemons(raw_species_path, raw_pokemon_path, generations, processed_path, parquet_name, csv_name)
    logging.info(f"Finaliza proceso de transformación {start_time.strftime('%Y-%m-%d %H:%M:%S')}", extra={"phase": "ETL"})

    logging.info("Inicia el proceso de carga de datos a la base de datos.", extra={"phase": "ETL"})
    load_pokemons_to_db(processed_path, parquet_name, db_user, db_password, db_host, db_name, db_port)
    logging.info(f"Finaliza proceso de carga {start_time.strftime('%Y-%m-%d %H:%M:%S')}", extra={"phase": "ETL"})
    logging.info(f"Tiempo total de ejecución: {datetime.now() - start_time}", extra={"phase": "ETL"})
