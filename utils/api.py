from flask import Blueprint, request, jsonify
from bson import ObjectId
from pymongo import MongoClient
import re
from utils.conexion_mongo import db

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Utilidad para convertir precios tipo "$ 330.000.000" a int

def limpiar_precio(texto):
    if not texto or texto == "No disponible":
        return None
    return int(re.sub(r"\D", "", texto))  # quita $ . , espacios

# Utilidad para convertir área tipo "162.00  m2" a float

def limpiar_area(texto):
    if not texto or texto == "N/A":
        return None
    return float(texto.replace("m2", "").strip())

@api_bp.route("/propiedades/<tipo>", methods=["GET"])
def consultar_propiedades(tipo):
    if tipo not in ["venta", "arriendo"]:
        return jsonify({"error": "Tipo debe ser 'venta' o 'arriendo'"}), 400

    coleccion = db[tipo]
    filtros = {}

    # Filtros de texto exacto o regex
    for campo in ["Ciudad", "Municipio", "Barrio", "Tipo de Inmueble", "Estrato"]:
        valor = request.args.get(campo.lower())
        if valor:
            filtros[campo] = {"$regex": valor, "$options": "i"}

    # Filtros de precio
    precio_min = request.args.get("precio_min")
    precio_max = request.args.get("precio_max")
    if precio_min or precio_max:
        rango = {}
        if precio_min:
            rango["$gte"] = int(precio_min)
        if precio_max:
            rango["$lte"] = int(precio_max)
        filtros["Precio"] = rango

    # Filtros de área
    area_min = request.args.get("area_min")
    area_max = request.args.get("area_max")
    if area_min or area_max:
        rango = {}
        if area_min:
            rango["$gte"] = float(area_min)
        if area_max:
            rango["$lte"] = float(area_max)
        filtros["Área Construida"] = rango

    # Búsqueda general
    q = request.args.get("q")
    if q:
        filtros["$or"] = [
            {"Ciudad": {"$regex": q, "$options": "i"}},
            {"Municipio": {"$regex": q, "$options": "i"}},
            {"Barrio": {"$regex": q, "$options": "i"}},
            {"Tipo de Inmueble": {"$regex": q, "$options": "i"}}
        ]
    filtros["Estrato"] = int(request.args.get("estrato")) if request.args.get("estrato") else {"$exists": True}
    resultados = []
    for doc in coleccion.find(filtros).limit(100):
        doc["_id"] = str(doc["_id"])
        resultados.append(doc)

    return jsonify(resultados)
