from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required, logout_user
from auth.forms import LoginForm, RecoverForm
from usuarios.users import validate_user

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard_view():
    """
    Ruta principal del dashboard que redirige a la vista de usuario
    según su rol.
    """
    user = current_user
    if user:
        if user.rol == "Administrador":
            return redirect("/admin/dashboard")
        else:
            return redirect("/analista/dashboard")
    else:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for("auth.login"))

@dashboard_bp.route("/admin/dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    """
    Vista del dashboard para el administrador.
    Aquí se pueden agregar más funcionalidades específicas.
    """
    return render_template("admin_dashboard.html")

@dashboard_bp.route("/analista/dashboard", methods=["GET", "POST"])
@login_required
def analista_dashboard():
    """
    Vista del dashboard para el administrador.
    Aquí se pueden agregar más funcionalidades específicas.
    """
    return render_template("analista_dashboard.html")