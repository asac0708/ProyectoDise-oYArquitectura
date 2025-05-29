from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user
from auth.forms import LoginForm, RecoverForm
from usuarios.users import validate_user
from werkzeug.security import generate_password_hash
from bson.objectid import ObjectId
import smtplib
import random
import string
from email.message import EmailMessage
import os
from dotenv import load_dotenv
from mongo_utils import db

auth_bp = Blueprint("auth", __name__)
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def generar_contrasena(longitud=10):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))

def enviar_email(destinatario, nueva_contrasena):
    mensaje = EmailMessage()
    mensaje['Subject'] = 'Recuperación de contraseña - Colombia Realty HUB'
    mensaje['From'] = EMAIL_USER
    mensaje['To'] = destinatario
    mensaje.set_content(f"Hola,\nTu nueva contraseña es: {nueva_contrasena}\nTe recomendamos cambiarla luego de iniciar sesión.")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASSWORD)
        smtp.send_message(mensaje)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = validate_user(form.id.data, form.password.data)
        if user:
            login_user(user)
            flash("Login exitoso", "success")
            if user.rol == "Administrador":
                return redirect("/admin/dashboard")
            else:
                return redirect("/analista/dashboard")
        else:
            flash("Documento o contraseña inválidos", "danger")
    return render_template("login.html", form=form)

@auth_bp.route("/", methods=["GET", "POST"])
def redirecting_to_login():
    return redirect("/login")

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth_bp.route("/recover", methods=["GET", "POST"])
def recover():
    form = RecoverForm()
    if form.validate_on_submit():
        usuario = db["usuarios"].find_one({
            "documento": form.id.data,
            "email": form.email.data
        })
        if usuario:
            nueva_contrasena = generar_contrasena()
            hash_contrasena = generate_password_hash(nueva_contrasena)

            db["usuarios"].update_one(
                {"_id": usuario["_id"]},
                {"$set": {"contrasena": hash_contrasena}}
            )

            enviar_email(form.email.data, nueva_contrasena)
            flash("Se ha enviado una nueva contraseña a tu correo electrónico.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("ID o correo no encontrados", "danger")
    return render_template("recover.html", form=form)
