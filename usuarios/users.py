from flask_login import UserMixin
from werkzeug.security import check_password_hash
from utils.conexion_mongo import db

class Usuario(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.documento = user_data["documento"]
        self.rol = user_data["rol"]
        self.nombre = user_data.get("nombre", "")
        self.email = user_data.get("email", "")

def validate_user(documento, password):
    user_data = db["usuarios"].find_one({"documento": documento})
    if user_data and check_password_hash(user_data["contrasena"], password):
        return Usuario(user_data)
    return None
