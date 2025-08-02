import psycopg2
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import create_engine, text
import logging

def connect_to_postgresql(user, psw, host, dbname, port):
    """Conecta a una base de datos PostgreSQL.
    Args:
        user (str): Usuario de la base de datos.
        psw (str): Contraseña del usuario.
        host (str): Host de la base de datos.
        dbname (str): Nombre de la base de datos.
        port (int): Puerto de conexión a la base de datos.
    Returns:
        sqlalchemy.engine.Engine: Motor de conexión a la base de datos.
    """
    logging.info("Intentando conectar a la base de datos PostgreSQL...", extra={"phase": "LOAD"})
    conn_str = f"postgresql+psycopg2://{user}:{psw}@{host}:{port}/{dbname}"
    try:
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
            logging.info("Conexión exitosa a la base de datos PostgreSQL.", extra={"phase": "LOAD"})
        return engine
    except Exception as e:
        logging.info(f"Error al conectar a la base de datos: {str(e)}", extra={"phase": "LOAD"})
        raise

def read_pokemon_parquet(processed_path, parquet_name):
    """Lee los datos de Pokémon desde un archivo Parquet.
    Args:
        processed_path (Path): Ruta del archivo Parquet.
    Returns:
        pd.DataFrame: DataFrame con los datos de Pokémon.
    """
    try:
        df_pokemons = pd.read_parquet(processed_path / parquet_name)
        logging.info("Datos de Pokémon leídos exitosamente desde Parquet.", extra={"phase": "LOAD"})
        return df_pokemons
    except Exception as e:
        logging.error(f"Error al leer el archivo Parquet: {str(e)}", extra={"phase": "LOAD"})
        raise

def load_pokemons_to_db(processed_path, parquet_name, db_user, db_password, db_host, db_name, db_port):
    """Carga los datos de Pokémon desde un archivo Parquet a la base de datos PostgreSQL.
    Args:
        processed_path (Path): Ruta del archivo Parquet con los datos de Pokémon.
        db_user (str): Usuario de la base de datos.
        db_password (str): Contraseña del usuario de la base de datos.
        db_host (str): Host de la base de datos.
        db_name (str): Nombre de la base de datos.
        db_port (int): Puerto de conexión a la base de datos.
    Returns:
        None
    """
    df_pokemons = read_pokemon_parquet(processed_path, parquet_name)
    engine = connect_to_postgresql(db_user, db_password, db_host, db_name, db_port)
    try:
        with engine.connect() as conn:
            df_pokemons.to_sql('pokemons', conn, if_exists='replace', index=False)
            logging.info("Datos de Pokémon cargados exitosamente en la base de datos.", extra={"phase": "LOAD"})
    except Exception as e:
        logging.error(f"Error al cargar los datos de Pokémon en la base de datos: {str(e)}", extra={"phase": "LOAD"})
        raise
    