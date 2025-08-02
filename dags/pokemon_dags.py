from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.hooks.base import BaseHook
from datetime import datetime, timedelta
import asyncio
from pathlib import Path

# Importa tus módulos
from pokemon_etl.config_manager import ConfigManager
from pokemon_etl.extract import get_raw_species, get_raw_pokemons
from pokemon_etl.transform import join_species_pokemons
from pokemon_etl.load import load_pokemons_to_db

# Configuración global del DAG
default_args = {
    "owner": "Luis",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

# Definir variables predeterminadas para el DAG desde json
config = ConfigManager(datetime.now())
def_raw_species_path = config.raw_species_path
def_raw_pokemon_path = config.raw_pokemon_path
def_processed_path = config.processed_path
def_parquet_name = config.parquet_name
def_csv_name = config.csv_name
def_generations = config.generations
def_api_base_url = config.api_base_url

# Leer Variables desde Airflow UI
raw_species_path = Path(Variable.get("pokemon_raw_species_path", default_var=def_raw_species_path))
raw_pokemon_path = Path(Variable.get("pokemon_raw_pokemon_path", default_var=def_raw_pokemon_path))
processed_path = Path(Variable.get("pokemon_processed_path", default_var=def_processed_path))
parquet_name = Variable.get("pokemon_parquet_name", default_var=def_parquet_name)
csv_name = Variable.get("pokemon_csv_name", default_var=def_csv_name)
raw_generations = Variable.get("pokemon_generations", default_var=None)
if raw_generations:
    generations = [g.strip() for g in raw_generations.split(",") if g.strip()]
else:
    generations = def_generations
api_base_url = Variable.get("pokemon_api_base_url", default_var=def_api_base_url)

# Leer conexión de Postgres desde Airflow UI
postgres_conn = BaseHook.get_connection("postgres_pokemon")
db_user = postgres_conn.login
db_password = postgres_conn.password
db_host = postgres_conn.host
db_name = postgres_conn.schema
db_port = postgres_conn.port

# Wrappers para las funciones del ETL
def setup_dirs():
    """Crea los directorios necesarios para el ETL."""
    raw_species_path.mkdir(parents=True, exist_ok=True)
    raw_pokemon_path.mkdir(parents=True, exist_ok=True)
    processed_path.mkdir(parents=True, exist_ok=True)

def extract_data():

    asyncio.run(get_raw_species(raw_species_path, api_base_url, generations))
    asyncio.run(get_raw_pokemons(raw_pokemon_path, api_base_url))

def transform_data():

    join_species_pokemons(
        raw_species_path,
        raw_pokemon_path,
        generations,
        processed_path,
        parquet_name,
        csv_name
    )

def load_data():
    load_pokemons_to_db(
        processed_path,
        parquet_name,
        db_user,
        db_password,
        db_host,
        db_name,
        db_port
    )

# Definir el DAG
with DAG(
    dag_id="pokemon_etl_dag",
    default_args=default_args,
    description="ETL de Pokémon con Variables y Connections en Airflow",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["etl", "pokeapi"],
) as dag:
    
    setup_task = PythonOperator(
        task_id="setup_directories",
        image="pokemon_etl:latest",
        docker_url="unix://var/run/docker.sock",
        python_callable=setup_dirs
    )

    extract_task = PythonOperator(
        task_id="extract_data",
        image="pokemon_etl:latest",
        docker_url="unix://var/run/docker.sock",
        python_callable=extract_data
    )

    transform_task = PythonOperator(
        task_id="transform_data",
        image="pokemon_etl:latest",
        docker_url="unix://var/run/docker.sock",
        python_callable=transform_data
    )

    load_task = PythonOperator(
        task_id="load_data",
        image="pokemon_etl:latest",
        docker_url="unix://var/run/docker.sock",
        python_callable=load_data
    )

    setup_task >> extract_task >> transform_task >> load_task