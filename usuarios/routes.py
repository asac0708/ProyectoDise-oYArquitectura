from flask import Blueprint, jsonify, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from bson import ObjectId
from usuarios.forms import UsuarioCrearForm, UsuarioEditarForm
from usuarios.controller import listar_usuarios, obtener_usuario, crear_usuario, editar_usuario, eliminar_usuario, encontrar_usuarios
import random
from werkzeug.security import generate_password_hash

usuarios_bp = Blueprint("usuarios", __name__)

def generar_documento_id():
    return "EQ" + ''.join([str(random.randint(0, 9)) for _ in range(7)])


@usuarios_bp.route("/admin/users")
@login_required
def users_view():
    usuarios = listar_usuarios()
    return render_template("users.html", usuarios=usuarios)


@usuarios_bp.route("/admin/crear", methods=["GET", "POST"])
@login_required
def crear_usuario_view():
    form = UsuarioCrearForm()
    id_generado = generar_documento_id()

    if form.validate_on_submit():
        datos = {
            "nombre": form.nombre.data,
            "rol": form.rol.data,
            "email": form.email.data,
            "contrasena": form.password.data,
            "documento": id_generado
        }
        try:
            crear_usuario(datos)
            flash("Usuario creado exitosamente", "success")
            return redirect(url_for("usuarios.users_view"))
        except ValueError as e:
            flash(str(e), "danger")
    else:
        # Mostrar errores de validación de WTForms
        for campo, errores in form.errors.items():
            for error in errores:
                flash(f"{campo.capitalize()}: {error}", "danger")

    return render_template("usuario_crear.html", form=form, id_generado=id_generado)

@usuarios_bp.route("/editar/<id>", methods=["GET", "POST"])
@login_required
def editar_usuario_view(id):
    usuario = obtener_usuario(id)
    if not usuario:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for("usuarios.users_view"))

    form = UsuarioEditarForm(data=usuario)

    es_admin = current_user.rol == "Administrador"
    es_propietario = current_user.id == id
    print(f"Usuario actual: {current_user.id}, Usuario a editar: {id}")

    # Definir campos editables según rol y si edita su propio perfil
    editable = {
        "nombre": True,
        "rol": es_admin,
        "email": es_propietario,
        "contrasena": current_user.documento == usuario["documento"]
    }

    if form.validate_on_submit():
        nuevos_datos = {}
        if editable["nombre"]:
            nuevos_datos["nombre"] = form.nombre.data
        if editable["rol"]:
            nuevos_datos["rol"] = form.rol.data
        if editable["email"]:
            nuevos_datos["email"] = form.email.data
        if editable["contrasena"] and form.nueva_contrasena.data:
            print(f"Contraseña nueva: {form.nueva_contrasena.data}")
            hash_nueva = generate_password_hash(form.nueva_contrasena.data)
            print(f"Hash de nueva contraseña: {hash_nueva}")
            nuevos_datos["contrasena"] = hash_nueva
        editar_usuario(id, nuevos_datos)
        flash("Usuario actualizado", "success")
        return redirect(url_for('usuarios.users_view') if es_admin else url_for('usuarios.perfil'))

    return render_template(
        "usuario_editar.html",
        form=form,
        editable=editable,
        volver_url=url_for('usuarios.users_view') if es_admin else url_for('usuarios.perfil'),
    )

@usuarios_bp.route("/admin/eliminar/<id>", methods=["GET", "POST"])
@login_required
def confirmar_eliminar(id):
    usuario = obtener_usuario(id)
    if request.method == "POST":
        eliminar_usuario(id)
        flash("Usuario eliminado", "warning")
        return redirect(url_for("usuarios.users_view"))
    return render_template("usuario_confirmar_eliminar.html", usuario=usuario)

@usuarios_bp.route("/perfil")
@login_required
def perfil():
    return render_template("perfil.html")

@usuarios_bp.route("/usuarios/buscar", methods=["GET"])
@login_required
def buscar_usuarios():
    query = request.args.get("q", "")
    filtro = {
        "$or": [
            {"nombre": {"$regex": query, "$options": "i"}},
            {"documento": {"$regex": query, "$options": "i"}},
            {"rol": {"$regex": query, "$options": "i"}}
        ]
    }
    usuarios = encontrar_usuarios(filtro)
    if not usuarios:
        flash("No se encontraron usuarios", "info")
        return jsonify([])
    for u in usuarios:
        u["_id"] = str(u["_id"])
    print(f"Usuarios encontrados: {usuarios}")
    return jsonify(usuarios)
