# Proyecto ETL con PokeAPI - Notas de Aprendizaje

## Objetivo del Proyecto
- Crear un proyecto ETL **modular**, que extraiga datos de la API pública **PokeAPI**, los transforme y los cargue en:
  - Un archivo **Parquet**.
  - Una base de datos **PostgreSQL** para consultas SQL.
- Orquestar el flujo con **Airflow** y contenerizar todo con **Docker**.
- Consultar los datos con **pgAdmin**.
- Gestionar dependencias con **Poetry**.

## Herramientas a Aprender y Usar
- **Poetry** → Para manejar entornos virtuales y dependencias.
- **Docker** → Para contenerizar la aplicación y sus servicios.
- **Airflow** → Para programar y monitorear el ETL.
- **pgAdmin** → Para gestionar la base de datos PostgreSQL.
- **PokeAPI** → API pública para obtener datos de Pokémon.
- **PostgreSQL** → Base de datos para consulta.
- **Python (requests, pandas, pyarrow)** → Implementación del ETL.

## Instalaciones Y Configuraciones

### Poetry 
1. Instale poetry en windows usando el comando 
```bash
curl -sSL https://install.python-poetry.org | python
```
2. Me posicione en la carpeta donde queria iniciar el proyecto y ejecute el comando
```bash
poetry new pokemon_etl #(esto instalo pytest tambien)
```
3. Active el entorno de Poetry con el comando
```bash
poetry env activate
```
4. Agregue las librerías request, pandas y pyarrow (para parquet) usando el comando
```bash
poetry add requests pandas pyarrow
```
5. Agregue la libreria pytest pero solo para el ambiente desarrollo con el comando
```bash
poetry add --dev pytest
```
6. Elimine librerías que no necesitaba o que descarte con el comando
```bash
poetry remove lib
```
7. Para poder exportar vamos a instalar el plugin con el comando
```bash
poetry self add poetry-plugin-export
```
8. Ejecutamos este codigo para generar el archivo requirements.txt solo con las librerías de productivo
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```


### Docker
1. Habilite WSL (Windows Subsystem for Linux) con el comando
```bash
wsl --install
```
2. Instale Docker Desktop
3. Para este proyecto se contaran con múltiples contenedores:
  - **postgres**: Base de datos
  - **pgAdmin**: para gestioanr DB
  - **airflow-webserver**: Interfaz de Airflow
  - **airflow-scheduler**: Orquestación
  - **airflow-worker**: Ejecución de tareas
4. Por ello, se debe desplegar docker con un docker-compose y red compartida en el mismo para que todos los servicios se vean.  
docker-compose te permite definir todo tu stack (Postgres, Airflow, pgAdmin) en un archivo YAML y levantarlo con un solo comando. Mucho más limpio que usar 3 o 4 comandos docker run.  
5. Desde la raíz del proyecto se ejecutan los comandos:
  ```bash
  docker-compose up airflow-init   # Inicializa Airflow
  docker-compose up -d             # Levanta todos los servicios
  docker ps                        # Enlista contenedores
  ```

### Postgresql
1. Los parámetros de puerto, usuario, contraseña, y bd se definen en el archivo docker-compose
  ```yaml
  POSTGRES_USER: myuser
  POSTGRES_PASSWORD: mypassword
  POSTGRES_DB: pokemon_db
  ```
2. Conexión desde otro contenedor:
  - **Host**: `pokemon-db` (nombre del servicio).
  - **Puerto**: 5432
3. En Docker Compose, **el nombre del servicio es el hostname** en la red interna.
4. Para acceder a postgresql desde terminal ejecutar: 
```bash
docker exec -it nombre_contenedor_postgres psql -U myuser -d nombre_db
```

### Airflow
- **DAG (Directed Acyclic Graph)** → Flujo de trabajo.
- **Task** → Cada paso (extract, transform, load).
- **Scheduler** → Programa y ejecuta tareas.
- **Webserver** → UI para monitoreo.

Configuracion:
- Carpeta `dags/` → Contiene archivos `.py` con definición del DAG.
- **Volumen**: Un volumen en Docker es una forma de compartir archivos entre tu máquina host y el contenedor o de persistir datos cuando el contenedor se elimina.

Tipos de uso:
- Persistencia → Para que los datos no se borren cuando reinicias el contenedor (ej. datos de Postgres).
- Montaje de código → Para que el contenedor tenga acceso al código fuente que está en tu PC.
- Volúmenes en `docker-compose`:
  ```yaml
  volumes:
    - ./dags:/opt/airflow/dags
    - ./src:/opt/airflow/src
    - ./config_file:/opt/airflow/config_file
  environment:
    PYTHONPATH: /opt/airflow/src #Esto añade /opt/airflow/src al sys.path dentro del contenedor, permitiendo que Python encuentre los módulos desarrollados.
  ```

### **Comandos**
- Inicializar Airflow:
  ```bash
  docker-compose up airflow-init
  ```
- Levantar servicios:
  ```bash
  docker-compose up -d
  ```
- UI: [http://localhost:8080](http://localhost:8080)
  - Usuario: `admin`
  - Password: `admin`


## Aprendizaje codigo

### 1. **Manejo de multiples llamadas**: 
Cuando se necesitan hacer **muchas llamadas HTTP** (o incluso llamadas anidadas) para guardar datos, es más eficiente utilizar **framework de llamadas en paralelo y asíncronas** en lugar de hacerlo secuencialmente. Esto reduce el tiempo de espera y el bloqueo de recursos.
- **asyncio**: Librería estándar de Python para manejar asincronía.
- **aiohttp**: Cliente HTTP asíncrono que funciona con asyncio.

Cuando tienes un flujo con **muchas peticiones HTTP** o **operaciones I/O intensivas**, la asincronía te permite aprovechar mejor el tiempo y los recursos.

Puedes usar esta función para obtener la respuesta del endpoint en json

```python
async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()
```
Para invocarla debes usar una **sesión HTTP asíncrona**:

```python
import aiohttp
import asyncio

async def main():
    async with aiohttp.ClientSession() as session:
        data_json = await fetch(session, "https://url.com")
        print(data_json)

# Ejecutar el código principal
asyncio.run(main())
```
Ejemplo con múltiples llamadas:
```python
urls = ["https://pokeapi.co/api/v2/pokemon/1", "https://pokeapi.co/api/v2/pokemon/2"]

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)  # Ejecuta en paralelo
        print(results)

asyncio.run(main())
```

Importante:
- **`await` es obligatorio** antes de llamar a `fetch()` porque es una función asíncrona (definida con `async def`).
- Si no usas `await`, la función devuelve un **coroutine** y no el resultado real.

### 2. **Clases**:
Una clase es como un **molde o plano** que define cómo se crean los objetos.  
Por ejemplo, la clase `Pokemon` define cómo son los Pokémon, y luego podemos crear instancias (objetos) como `Pikachu`, `Charmander`, etc.

En la clase se definen:
  - **Atributos** → características (ejemplo: nombre, tipo, nivel).
  - **Métodos** → comportamientos o acciones (ejemplo: atacar, evolucionar).

**Sintaxis básica:**
```python
class NombreClase:
    # Constructor
    def __init__(self, atributos):
        self.atributo = valor

    # Método
    def metodo(self):
        # acción
```
Ejemplo: Clase básica de Pokémon**
```python
class Pokemon:
    def __init__(self, nombre, tipo, nivel=1):
        self.nombre = nombre      # Atributo
        self.tipo = tipo          # Atributo
        self.nivel = nivel        # Atributo
    
    def atacar(self):             # Metodo
        print(f"{self.nombre} usa un ataque básico.")
```

**Crear objetos (instanciar)**
```python
pikachu = Pokemon("Pikachu", "Eléctrico", nivel=5)
charmander = Pokemon("Charmander", "Fuego")

pikachu.atacar()      # Pikachu usa un ataque básico.
print(pikachu.tipo)   # Eléctrico
```

**Conceptos importantes**

**Atributos**
- Son variables que pertenecen al objeto.
- Se accede con `self.atributo`.

Ejemplo:
```python
print(pikachu.nombre)  # Pikachu
pikachu.nivel = 10     # Modificar atributo
```

**Métodos**
- Son funciones dentro de la clase.
- Siempre llevan `self` como primer parámetro.

Ejemplo:
```python
def subir_nivel(self):
    self.nivel += 1
    print(f"{self.nombre} subió al nivel {self.nivel}")
```

### 3. **Manejo de Excepciones**:

En Python, el manejo de errores se hace con **excepciones**. Las excepciones permiten **detener la ejecución controladamente** cuando ocurre un error y manejarlo sin que el programa se rompa.

**¿Qué es una excepción?**
- Una **excepción** es un evento que ocurre durante la ejecución y **interrumpe el flujo normal del programa**.
- Ejemplo: intentar dividir entre cero o abrir un archivo inexistente.

Ejemplo sin manejo:
```python
print(10 / 0)  # ZeroDivisionError
```
Esto lanza: ZeroDivisionError: division by zero

**try y except**
- **try**: Bloque donde pones el código que puede fallar.
- **except**: Bloque donde defines qué hacer si ocurre una excepción.

```python
try:
    print(10 / 0)
except ZeroDivisionError:
    print("¡Error! No se puede dividir entre cero.")
```

**Capturar cualquier excepción**
```python
try:
    x = int("pikachu")  # ValueError
except Exception as e:
    print(f"Ocurrió un error: {e}")
```
Salida:
```
Ocurrió un error: invalid literal for int() with base 10: 'pikachu'
```
**else**
El bloque **else** se ejecuta **solo si no hubo excepción**.

Ejemplo:
```python
try:
    numero = int("42")
except ValueError:
    print("Valor no válido.")
else:
    print("Conversión exitosa:", numero)
```

**raise (lanzar excepciones)**: podemos **forzar** un error con `raise` para validar condiciones.

Ejemplo:
```python
def capturar_pokemon(nombre):
    if nombre == "":
        raise ValueError("El nombre del Pokémon no puede estar vacío.")
    print(f"¡Has capturado a {nombre}!")

try:
    capturar_pokemon("")
except ValueError as e:
    print("Error:", e)
```

## Aprendizaje de Docker
Docker es una **plataforma para crear, ejecutar y administrar contenedores**. Un **contenedor** es como una **caja ligera y portátil que contiene todo lo necesario para ejecutar una aplicación**: código, librerías, dependencias, configuración, etc.  

Esto permite que tu aplicación se ejecute **igual en cualquier entorno** (tu PC, un servidor, la nube).

Conceptos clave

### 1. **Imagen (Image)**
- Una **imagen** es una **plantilla inmutable** (snapshot) que contiene el sistema operativo mínimo + dependencias + aplicación. Es como una clase y el contenedor es la variable que se instancia.
- No se puede tener mas de una imagen por contenedor.
- Se construye normalmente con un **Dockerfile**, que define **cómo crear la imagen**.
- Ejemplo:  
  - `python:3.10-slim` → imagen oficial de Python ligera.
  - `mysql:8.0` → imagen oficial de MySQL.

- Las imagenes que se descargen ya sea por el comando:
```bash 
docker pull nombre_imagen
```
O por docker-compose estaran disponibles de forma global y para enlistar las imagenes descargadas
```bash
docker images
```
- Para eliminar una imagen primero debemos asegurarnos de que no es usada por ningun contenedor. Para ello buscamos que contenedores usan esa imagen
```bash
docker ps -a --filter "ancestor=IMAGE_ID"
```
Luego para eliminar el docker debemos ejecutar
```bash
docker rmi CONTAINER_ID
```
Ahora si podemos 

### 2. **Contenedor (Container)**
- Es una **instancia en ejecución** de una imagen.
- Puedes tener múltiples contenedores basados en la misma imagen.
- Son **aislados** (cada uno tiene su propio sistema de archivos y red), pero comparten el **kernel** del host.

Ejemplo:
```bash
docker run -d --name miapp -p 8080:80 nginx
```
Esto:
- Descarga la imagen `nginx` (si no la tienes).
- Crea un contenedor con nombre `miapp`.
- Mapea el puerto **8080 del host → 80 del contenedor**.
- Lo ejecuta en segundo plano (`-d`).

### 3. **Dockerfile**
- Es un **archivo de instrucciones** para construir imágenes personalizadas.
- Ejemplo:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```
Esto crea una imagen con Python, copia tu código y lo deja listo para correr.

### 4. **`docker run`**
- Es el comando para **crear y ejecutar un contenedor** desde una imagen.
- Formato:
```bash
docker run [opciones] imagen [comando]
```
- Ejemplos:
  - `docker run -it ubuntu bash` → contenedor interactivo con Ubuntu.
  - `docker run -d -p 8080:80 nginx` → corre NGINX en segundo plano.

Opciones útiles:
- `-d` → modo **detached** (segundo plano).
- `-p host:container` → mapear puertos.
- `--name` → asignar nombre.
- `-v host:container` → montar volúmenes.

### 5. **`docker ps`**
- Lista contenedores en ejecución.
- `docker ps -a` → lista todos (incluidos los detenidos).

### 6. **Volúmenes**
- Permiten **persistir datos** fuera del contenedor.
- Si eliminas el contenedor, los datos siguen existiendo.
- Ejemplo:
```bash
docker run -d -v /mi/carpeta:/data nginx
```

### 7. **`docker compose`**
- Herramienta para **orquestar múltiples contenedores** (ej: app + base de datos + redis).
- Usa un archivo `docker-compose.yml` para definir servicios.
- Ejemplo:
```yaml
version: '3'
services:
  web:
    image: nginx
    ports:
      - "8080:80"
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: secret
```
- Levantar todo:
```bash
docker-compose up -d
```
Esto:
- Crea **dos contenedores** (nginx y mysql).
- Los conecta en la misma red interna.
- Maneja variables, volúmenes y dependencias.