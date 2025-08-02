import json
from pathlib import Path

class ConfigManager:
    """
    Maneja la configuración del ETL de Pokémon.
    Carga la configuración desde un archivo JSON y proporciona métodos para acceder a los parámetros de:
    - API
    - Rutas
    - Base de datos.
    """
    def __init__(self, start_time, config_path: str = "config_file/config.json"):
        self.config_file = Path(config_path)
        self.config = self._load_config()
        self.api_config = self.config.get("api_config")
        self.path_config = self.config.get("path_config")
        self.db_config = self.config.get("db_config")
        self._validate_and_create_dirs(start_time)
        self.api_base_url = self._get_api_param("api_base_url")
        self.generations = self._get_api_param("generations")
        self.raw_pokemon_path = self._get_part_path("raw_pokemon_path")
        self.raw_species_path = self._get_part_path("raw_species_path")
        self.processed_path = self._get_part_path("processed_path")
        self.logs_path = self._get_part_path("logs_path")
        self.db_user = self._get_db_param("user")
        self.db_password = self._get_db_param("password")
        self.db_host = self._get_db_param("host")
        self.db_name = self._get_db_param("db_name")
        self.db_port = self._get_db_param("port")
        self.parquet_name = self._get_file_param("parquet_name")
        self.csv_name = self._get_file_param("csv_name")
        
    def _load_config(self) -> dict:
        """
        Primero, evalua que el archivo de configuración exista en la ruta
        Luego, carga el JSON.
        """
        if not self.config_file.exists():
            raise FileNotFoundError(f"No se ha hallado el archivo de configuracion: {self.config_file}")
        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _validate_and_create_dirs(self, start_time) -> None:
        """Crea las rutas necesarias si no existen."""
        required_paths = ["raw_species_path", "raw_pokemon_path", "processed_path", "logs_path"]
        for key in required_paths:
            value = self.path_config.get(key)
            if not value:
                raise ValueError(f"Falta la ruta '{key}' en path_config")
        paths = [
            Path(self.path_config.get("raw_species_path")),
            Path(self.path_config.get("raw_pokemon_path")),
            Path(self.path_config.get("processed_path")),
            Path(self.path_config.get("logs_path")),
            Path(f"{self.path_config.get('logs_path')}/{start_time.strftime('%m%Y')}"),
        ]
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
    
    def _get_api_param(self, param: str) -> str:
        """Obtiene un parámetro específico de la configuración de la API."""
        if param not in self.api_config:
            raise KeyError(f"El parámetro '{param}' no se encuentra en la configuración de la API.")
        return self.api_config.get(param)
    
    def _get_part_path(self, part: str) -> Path:
        """Obtiene una ruta específica de la configuración."""
        if part not in self.path_config:
            raise KeyError(f"La parte '{part}' no se encuentra en la configuración de rutas.")
        return Path(self.path_config.get(part,""))

    def _get_db_param(self,param: str) -> str:
        """Obtiene un parámetro de la configuración de la base de datos."""
        if param not in self.db_config:
            raise KeyError(f"El parámetro '{param}' no se encuentra en la configuración de la base de datos.")
        return self.db_config.get(param)
    
    def _get_file_param(self, param: str) -> str:
        """Obtiene un parámetro de la configuración de archivos."""
        if param not in self.config.get("file_config", {}):
            raise KeyError(f"El parámetro '{param}' no se encuentra en la configuración de archivos.")
        return self.config.get("file_config").get(param)
