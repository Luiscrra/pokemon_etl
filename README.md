# Pokémon ETL con Airflow, Docker y PostgreSQL

Este proyecto implementa un **pipeline ETL** que extrae datos desde la [PokeAPI](https://pokeapi.co/), los transforma y los carga en **PostgreSQL**, además de generar un archivo **Parquet** y **CSV** para análisis. El flujo se orquesta con **Apache Airflow** y está totalmente contenerizado con **Docker**.

---

## **Características**
- Extracción asíncrona de datos de Pokémon y especies desde PokeAPI.
- Transformación de datos en **pandas** y guardado en **Parquet** (Snappy) y CSV.
- Carga a **PostgreSQL** mediante SQLAlchemy.
- Configuración centralizada en `config.json`.
- Ejecución manual o mediante DAG de **Airflow**.
- **Docker Compose** para levantar Airflow, PostgreSQL y el contenedor ETL.
- Gestión de dependencias con **Poetry**.

## 📂 **Estructura del proyecto**
```
pokemon_etl/
├── docker-compose.yaml         # Orquestación de servicios
├── pyproject.toml              # Dependencias (Poetry)
├── dags/                       # DAG de Airflow
│   └── pokemon_dags.py
├── src/pokemon_etl/            # Código ETL
│   ├── config_manager.py
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   └── __init__.py
├── config_file/config.json     # Configuración del pipeline
├── data/
│   ├── raw/                    # Datos crudos (API)
│   └── processed/              # Datos procesados (Parquet y CSV)
├── logs/                       # Logs de ejecución
└── notebooks/                  # Experimentos Jupyter
```

## **Tecnologías**
- **Python** 3.11
- **Poetry** para la gestión de dependencias
- **Apache Airflow**
- **Docker & Docker Compose**
- **PostgreSQL**
- **pandas**, **pyarrow**, **aiohttp**, **SQLAlchemy**

---

## **Configuración**
Variables clave en `config_file/config.json`:
```json
"db_config": {
  "db_name": "pokemon_db",
  "user": "myuser",
  "password": "mypassword",
  "host": "pokemon-db",
  "port": 5432
}
```

En **Airflow**:
- Variables: rutas y nombres de archivo.
- Connection: `postgres_pokemon` con credenciales de DB.

---

## **Instalación y ejecución**
Clona el repositorio:
```bash
git clone https://github.com/tuusuario/pokemon_etl.git
cd pokemon_etl
```

### **1. Ejecutar con Docker Compose**
Levanta Airflow + PostgreSQL + ETL:
```bash
docker-compose up --build
```
Accede a Airflow en:  
`http://localhost:8080`  
Usuario y clave por defecto: `airflow / airflow`

Activa el DAG: **pokemon_etl_dag**.

### **2. Ejecutar localmente**
Instala dependencias:
```bash
poetry install
```
Ejecuta el pipeline:
```bash
poetry run python src/pokemon_etl/__init__.py
```

## **Salida**
- **Archivo Parquet**: `data/processed/pokemones.parquet`
- **Archivo CSV**: `data/processed/pokemones.csv`
- **Tabla en PostgreSQL**: `pokemons`