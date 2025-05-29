from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from bson import ObjectId
from pymongo import MongoClient
import datetime
from utils.conexion_mongo import db 
from io import BytesIO
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from fpdf import FPDF
from utils.reporte_en_pdf import reporte_en_pdf

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")
coleccion_reportes = db["reportes"]

def construir_filtros_propiedades(params, usar_regex=True):
    filtros = {}

    # Campos de texto
    for campo in ["Ciudad", "Municipio", "Barrio", "Tipo de Inmueble"]:
        valor = params.get(campo) or params.get(campo.lower())
        if valor:
            if usar_regex:
                filtros[campo] = {"$regex": valor, "$options": "i"}
            else:
                filtros[campo] = valor

    # Estrato
    estrato = params.get("Estrato") or params.get("estrato")
    if estrato:
        try:
            filtros["Estrato"] = int(estrato)
        except ValueError:
            pass

    # Precio
    precio_min = params.get("precio_min")
    precio_max = params.get("precio_max")
    if precio_min or precio_max:
        rango = {}
        if precio_min:
            rango["$gte"] = int(precio_min)
        if precio_max:
            rango["$lte"] = int(precio_max)
        filtros["Precio"] = rango

    # Área
    area_min = params.get("area_min")
    area_max = params.get("area_max")
    if area_min or area_max:
        rango = {}
        if area_min:
            rango["$gte"] = float(area_min)
        if area_max:
            rango["$lte"] = float(area_max)
        filtros["Área Construida"] = rango

    return filtros



@reportes_bp.route("/crear", methods=["GET", "POST"])
@login_required
def crear_reporte():
    if request.method == "POST":
        # Construir filtros a partir del formulario
        filtros = construir_filtros_propiedades(request.form, usar_regex=False)
        propiedades_filtradas = list(db["venta"].find(filtros))

        if not propiedades_filtradas:
            flash("No se encontraron propiedades con esos filtros.", "warning")
            return redirect(url_for("reportes.crear_reporte"))

        pdf_bytes = reporte_en_pdf(propiedades_filtradas)

        if not pdf_bytes:
            flash("No se pudo generar el reporte. Verifica los datos.", "danger")
            return redirect(url_for("reportes.crear_reporte"))

        coleccion_reportes.insert_one({
            "usuario_id": current_user.id,
            "fecha": datetime.datetime.utcnow(),
            "titulo": "Top 20 ROI filtrado",
            "filtros": dict(request.form),
            "pdf": pdf_bytes
        })

        flash("Reporte generado exitosamente.", "success")
        return redirect(url_for("reportes.dashboard_reportes"))

    # Precargar valores para el formulario
    opciones = {
        "Ciudad": db["venta"].distinct("Ciudad"),
        "Municipio": db["venta"].distinct("Municipio"),
        "Barrio": db["venta"].distinct("Barrio"),
        "Tipo de Inmueble": db["venta"].distinct("Tipo de Inmueble")
    }
    return render_template("crear_reporte.html", opciones=opciones)

@reportes_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard_reportes():
    if current_user.rol == "Administrador":
        reportes = list(coleccion_reportes.find().sort("fecha", -1))
    else:
        reportes = list(coleccion_reportes.find({"usuario_id": current_user.id}).sort("fecha", -1))
    return render_template("dashboard_reportes.html", reportes=reportes)

@reportes_bp.route("/eliminar/<id>", methods=["POST"])
@login_required
def eliminar_reporte(id):
    reporte = coleccion_reportes.find_one({"_id": ObjectId(id)})
    if not reporte or (current_user.rol != "Administrador" and reporte["usuario_id"] != current_user.id):
        flash("No autorizado", "danger")
        return redirect(url_for("reportes.dashboard_reportes"))
    coleccion_reportes.delete_one({"_id": ObjectId(id)})
    flash("Reporte eliminado", "warning")
    return redirect(url_for("reportes.dashboard_reportes"))

@reportes_bp.route("/descargar/<id>", methods=["GET"])
@login_required
def descargar_reporte(id):
    reporte = coleccion_reportes.find_one({"_id": ObjectId(id)})
    if not reporte or (current_user.rol != "Administrador" and reporte["usuario_id"] != current_user.id):
        flash("No autorizado para descargar este reporte", "danger")
        return redirect(url_for("reportes.dashboard_reportes"))
    return send_file(
        BytesIO(reporte["pdf"]),
        mimetype="application/pdf",
        download_name=f"reporte_{id}.pdf",
        as_attachment=True
    )
