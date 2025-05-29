from bson import ObjectId
from werkzeug.security import generate_password_hash
from utils.conexion_mongo import db

coleccion = db["usuarios"]

def listar_usuarios():
    return list(coleccion.find())

def obtener_usuario(usuario_id):
    return coleccion.find_one({"_id": ObjectId(usuario_id)})

def crear_usuario(datos):
    # Verificación: email o documento ya registrados
    if coleccion.find_one({"email": datos["email"]}):
        raise ValueError("Email ya registrado")
    
    if coleccion.find_one({"documento": datos["documento"]}):
        raise ValueError("Documento ya registrado")

    # Validación de campos básicos
    campos_obligatorios = ["nombre", "email", "documento", "contrasena", "rol"]
    for campo in campos_obligatorios:
        if not datos.get(campo):
            raise ValueError(f"Falta el campo obligatorio: {campo}")

    datos["_id"] = ObjectId()
    datos["contrasena"] = generate_password_hash(datos["contrasena"])
    coleccion.insert_one(datos)
    return datos["nombre"]


def editar_usuario(usuario_id, nuevos_datos):
    coleccion.update_one({"_id": ObjectId(usuario_id)}, {"$set": nuevos_datos})

def eliminar_usuario(usuario_id):
    coleccion.delete_one({"_id": ObjectId(usuario_id)})

def encontrar_usuarios(filtro):
    return list(coleccion.find(filtro))