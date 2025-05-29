import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

# URI de conexión obtenida desde MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")

# Nombre de la base de datos
DB_NAME = "inversion_colombia"

# Crear cliente y acceder a la base de datos
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

print("✅ Conexión exitosa a MongoDB Atlas")
