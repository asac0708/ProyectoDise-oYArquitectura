from flask import Blueprint, render_template
from flask_login import login_required, current_user
from utils.conexion_mongo import db

scraping_bp = Blueprint("scraping", __name__, url_prefix="/scraping")

def obtener_opciones_unicas(tipo):
    coleccion = db[tipo]
    campos = ["Ciudad", "Municipio", "Barrio", "Tipo de Inmueble"]
    opciones = {}
    for campo in campos:
        valores = coleccion.distinct(campo)
        opciones[campo] = sorted([v for v in valores if v and v != "N/A"])
    return opciones


@scraping_bp.route("/", methods=["GET"])
@login_required
def scraping_view():
    tipo = "venta"  # valor por defecto al entrar
    opciones = obtener_opciones_unicas(tipo)
    return render_template("scraping.html", rol=current_user.rol, opciones=opciones, tipo=tipo)