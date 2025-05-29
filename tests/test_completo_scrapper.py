
# test_completo_scrapper.py
# ============================
# Pruebas unitarias y de integración para el sistema Colombia Realty HUB


import sys
import os
import app
from unittest.mock import patch
from bson.objectid import ObjectId
from flask import Flask, url_for
from flask_testing import TestCase
from flask_login import login_user
import pytest
from app import create_app
from usuarios.users import Usuario
import pytest
from mongo_utils import insertar_propiedades
from utils.api import limpiar_precio, limpiar_area
from usuarios.forms import UsuarioCrearForm, UsuarioEditarForm
from auth.forms import RecoverForm, LoginForm
from usuarios.users import Usuario

# =====================================
# Sección 1: routes.py (Usuarios)
# =====================================

class TestUsuariosRoutes(TestCase):

    def create_app(self):
        from app import create_app
        app = create_app()
        app.config["WTF_CSRF_ENABLED"] = False
        return app

    @patch("usuarios.controller.listar_usuarios")
    def test_users_view_admin(self, mock_listar_usuarios):
        mock_listar_usuarios.return_value = [{"nombre": "Admin", "rol": "Administrador"}]
        idn= ObjectId()
        with self.client:
            from usuarios.users import Usuario
            user = Usuario({"_id": idn, "rol": "Administrador", "nombre": "Admin", "email": "admin@correo.com", "documento": "EQ0001"})
            login_user(user)
            response = self.client.get("/admin/users")
            self.assert200(response)
            self.assert_template_used("users.html")
            self.assertIn(b"Admin", response.data)

    @patch("usuarios.controller.crear_usuario")
    @patch("usuarios.forms.UsuarioCrearForm")
    def test_crear_usuario_exitoso(self, mock_form_class, mock_crear_usuario):
        idn= ObjectId()
        mock_form = mock_form_class.return_value
        mock_form.validate_on_submit.return_value = True
        mock_form.nombre.data = "Nuevo"
        mock_form.rol.data = "Analista"
        mock_form.email.data = "nuevo@correo.com"
        mock_form.password.data = "contrasenaSegura123"
        with self.client:
            from usuarios.users import Usuario
            user = Usuario({"_id": idn, "rol": "Administrador", "documento": "EQ0000001", "email": "admin@test.com"})
            login_user(user)
            response = self.client.post("/admin/crear")
            self.assert_redirects(response, url_for("usuarios.users_view"))
            mock_crear_usuario.assert_called_once()

    @patch("usuarios.controller.obtener_usuario")
    @patch("usuarios.controller.editar_usuario")
    @patch("usuarios.forms.UsuarioEditarForm")
    def test_editar_usuario_admin(self, mock_form_class, mock_editar_usuario, mock_obtener_usuario):
        idn= ObjectId()
        mock_obtener_usuario.return_value = {
            "_id": idn,
            "nombre": "Prueba",
            "rol": "Analista",
            "email": "prueba@correo.com",
            "documento": "EQ0000002"
        }
        mock_form = mock_form_class.return_value
        mock_form.validate_on_submit.return_value = True
        mock_form.nombre.data = "NuevoNombre"
        mock_form.rol.data = "Analista"
        mock_form.email.data = "nuevo@correo.com"
        mock_form.nueva_contrasena.data = ""
        with self.client:
            from usuarios.users import Usuario
            user = Usuario({"_id": "admin1", "rol": "Administrador", "documento": "EQ0000001", "email": "admin@correo.com"})
            login_user(user)
            response = self.client.post("/editar/123abc")
            self.assert_redirects(response, url_for("usuarios.users_view"))
            mock_editar_usuario.assert_called_once_with("123abc", {
                "nombre": "NuevoNombre",
                "rol": "Analista",
                "email": "nuevo@correo.com"
            })

    @patch("usuarios.controller.obtener_usuario")
    @patch("usuarios.controller.eliminar_usuario")
    def test_eliminar_usuario_exitoso(self, mock_eliminar_usuario, mock_obtener_usuario):
        idn= ObjectId()
        mock_obtener_usuario.return_value = {
            "_id": idn,
            "nombre": "Eliminar",
            "rol": "Analista",
            "email": "eliminar@correo.com",
            "documento": "EQ0000003"
        }
        with self.client:
            from usuarios.users import Usuario
            user = Usuario({"_id": "admin1", "rol": "Administrador", "documento": "EQ0000001", "email": "admin@correo.com"})
            login_user(user)
            response = self.client.post("/admin/eliminar/123abc")
            self.assert_redirects(response, url_for("usuarios.users_view"))
            mock_eliminar_usuario.assert_called_once_with("123abc")

    # =====================================
    # Sección 2: users.py
    # =====================================

    @patch("users.db")
    @patch("users.check_password_hash")
    def test_validate_user_exitoso(self,mock_check_password_hash, mock_db):
        idn= ObjectId()
        mock_user_data = {
            "_id": idn,
            "documento": "EQ1234567",
            "rol": "Administrador",
            "contrasena": "hashed_pwd",
            "nombre": "Admin",
            "email": "admin@correo.com"
        }
        mock_db.__getitem__.return_value.find_one.return_value = mock_user_data
        mock_check_password_hash.return_value = True

        from users import validate_user
        user = validate_user("EQ1234567", "password123")
        assert user is not None
        assert user.id == "1a2b3c"
        assert user.rol == "Administrador"

    @patch("users.db")
    @patch("users.check_password_hash")
    def test_validate_user_falla_password(self,mock_check_password_hash, mock_db):
        idn= ObjectId()
        mock_user_data = {
            "_id": idn,
            "documento": "EQ1234567",
            "rol": "Administrador",
            "contrasena": "hashed_pwd",
            "nombre": "Admin",
            "email": "admin@correo.com"
        }
        mock_db.__getitem__.return_value.find_one.return_value = mock_user_data
        mock_check_password_hash.return_value = False

        from users import validate_user
        user = validate_user("EQ1234567", "password_incorrecta")
        assert user is None

    # =====================================
    # Sección 3: api.py
    # =====================================

    def test_consultar_propiedades_tipo_invalido(self):
        from app import create_app
        app = create_app()
        client = app.test_client()
        response = client.get("/api/propiedades/inversion")
        assert response.status_code == 400
        assert "Tipo debe ser" in response.get_data(as_text=True)

    @patch("api.db")
    def test_filtros_precio_area(self,mock_db):
        idn= ObjectId()
        mock_collection = mock_db.__getitem__.return_value
        mock_collection.find.return_value.limit.return_value = [
            {"_id": idn, "Precio": 400000000, "Área Construida": 150.0}
        ]
        app = create_app()
        client = app.test_client()
        response = client.get("/api/propiedades/venta?precio_min=300000000&precio_max=500000000&area_min=100&area_max=200")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert all(300000000 <= p["Precio"] <= 500000000 for p in data)


    def test_utilidades_limpiar_precio_y_area(self):
        assert limpiar_precio("$ 330.000.000") == 330000000
        assert limpiar_precio("No disponible") is None
        assert limpiar_area("162.00  m2") == 162.0
        assert limpiar_area("N/A") is None

    # =====================================
    # Sección 4: controller.py
    # =====================================

    @patch("usuarios.controller.coleccion")
    @patch("usuarios.controller.generate_password_hash")
    def test_crear_usuario_exitoso(self,mock_hash, mock_coleccion):
        datos = {
            "nombre": "Carlos",
            "rol": "Analista",
            "email": "carlos@test.com",
            "contrasena": "segura123",
            "documento": "EQ1234567"
        }
        mock_coleccion.find_one.return_value = None
        mock_hash.return_value = "hashed_pass"
        from usuarios.controller import crear_usuario
        nombre = crear_usuario(datos)
        assert nombre == "Carlos"
        assert datos["contrasena"] == "hashed_pass"
        mock_coleccion.insert_one.assert_called_once()

    @patch("usuarios.controller.coleccion")
    def test_crear_usuario_documento_duplicado(self,mock_coleccion):
        mock_coleccion.find_one.side_effect = [None, {"documento": "EQ1234567"}]
        from usuarios.controller import crear_usuario
        datos = {
            "nombre": "Carlos",
            "rol": "Analista",
            "email": "nuevo@correo.com",
            "contrasena": "clave123",
            "documento": "EQ1234567"
        }
        with pytest.raises(ValueError, match="Documento ya registrado"):
            crear_usuario(datos)

    @patch("usuarios.controller.coleccion")
    def test_editar_usuario(self,mock_coleccion):
        from usuarios.controller import editar_usuario
        editar_usuario("64e3f9b2485b2fc3b8d7a1f3", {"nombre": "Nuevo"})
        mock_coleccion.update_one.assert_called_once()

    @patch("usuarios.controller.coleccion")
    def test_eliminar_usuario(self,mock_coleccion):
        from usuarios.controller import eliminar_usuario
        eliminar_usuario("64e3f9b2485b2fc3b8d7a1f3")
        mock_coleccion.delete_one.assert_called_once()

    # =====================================
    # Sección 5: forms.py
    # =====================================


    def test_usuario_crear_form_valido(self):
        app = Flask(__name__)
        app.config["WTF_CSRF_ENABLED"] = False
        with app.test_request_context(method="POST", data={
            "nombre": "Juan Pérez",
            "rol": "Administrador",
            "email": "juan@correo.com",
            "password": "clave123"
        }):
            form = UsuarioCrearForm()
            assert form.validate() is True

    def test_usuario_editar_form_contrasena_no_coincide(self):
        app = Flask(__name__)
        app.config["WTF_CSRF_ENABLED"] = False
        with app.test_request_context(method="POST", data={
            "nombre": "Ana",
            "rol": "Analista",
            "nueva_contrasena": "clave123",
            "confirmar_contrasena": "otraClave"
        }):
            form = UsuarioEditarForm()
            assert not form.validate()
            assert "Passwords must match" in form.confirmar_contrasena.errors[0]

    # =====================================
    # Sección 6: scraping.routes
    # =====================================

    @patch("scraping.routes.obtener_opciones_unicas")
    def test_scraping_view_acceso_autenticado(self,mock_opciones):
        mock_opciones.return_value = {
            "Ciudad": ["Bogotá", "Medellín"],
            "Municipio": ["Cundinamarca"],
            "Barrio": ["Chapinero"],
            "Tipo de Inmueble": ["Casa"]
        }
        with app.test_client() as client:
            idn= ObjectId()
            user = Usuario({"_id": idn, "rol": "Administrador", "documento": "EQ1234567", "email": "admin@correo.com", "nombre": "Admin"})
            login_user(user)
            response = client.get("/scraping/")
            assert response.status_code == 200
            assert b"Bogot" in response.data

    @patch("scraping.routes.db")
    def test_obtener_opciones_unicas_correctamente(self,mock_db):
        mock_db.__getitem__.return_value.distinct.side_effect = [
            ["Bogotá", None, "N/A", "Medellín"],
            ["Antioquia"],
            ["Chapinero", "N/A"],
            ["Casa", "Apartamento"]
        ]
        from scraping.routes import obtener_opciones_unicas
        opciones = obtener_opciones_unicas("venta")
        assert opciones["Ciudad"] == ["Bogotá", "Medellín"]
        assert opciones["Municipio"] == ["Antioquia"]
        assert opciones["Barrio"] == ["Chapinero"]
        assert opciones["Tipo de Inmueble"] == ["Apartamento", "Casa"]

    # =====================================
    # Sección 7: dashboard.routes
    # =====================================

    def test_redireccion_dashboard_admin(self):
        idn= ObjectId()
        with app.test_client() as client:
            user = Usuario({"_id": idn, "rol": "Administrador", "documento": "EQ1234567", "email": "admin@correo.com", "nombre": "Admin"})
            login_user(user)
            response = client.get("/dashboard")
            assert response.status_code == 302
            assert "/admin/dashboard" in response.location

    def test_redireccion_dashboard_analista(self):
        with app.test_client() as client:
            idn= ObjectId()
            user = Usuario({"_id": idn, "rol": "Analista", "documento": "EQ7654321", "email": "ana@correo.com", "nombre": "Ana"})
            login_user(user)
            response = client.get("/dashboard")
            assert response.status_code == 302
            assert "/analista/dashboard" in response.location

    def test_render_admin_dashboard(self):
        idn= ObjectId()
        with app.test_client() as client:
            user = Usuario({"_id": idn, "rol": "Administrador", "documento": "EQ1234567", "email": "admin@correo.com", "nombre": "Admin"})
            login_user(user)
            response = client.get("/admin/dashboard")
            assert response.status_code == 200

    def test_render_analista_dashboard(self):
        idn= ObjectId()
        with app.test_client() as client:
            user = Usuario({"_id": idn, "rol": "Analista", "documento": "EQ7654321", "email": "ana@correo.com", "nombre": "Ana"})
            login_user(user)
            response = client.get("/analista/dashboard")
            assert response.status_code == 200

    # =====================================
    # Sección 8: mongo_utils.py
    # =====================================

    
    def test_insertar_propiedades_tipo_invalido(self):
        with pytest.raises(ValueError, match="El tipo debe ser 'venta' o 'arriendo'"):
            insertar_propiedades([], "compra")

    @patch("mongo_utils.db")
    def test_insertar_propiedades_exitoso(self,mock_db):
        mock_coleccion = mock_db.__getitem__.return_value
        mock_resultado = mock_coleccion.insert_many.return_value
        mock_resultado.inserted_ids = [1, 2, 3]
        insertar_propiedades([{"Precio": "100"}, {"Precio": "200"}], "venta")
        mock_coleccion.insert_many.assert_called_once()

    # =====================================
    # Sección 9: auth.routes y forms (1).py
    # =====================================

    @patch("auth.routes.validate_user")
    def test_login_exitoso_admin(self,mock_validate_user):
        from auth.forms import LoginForm
        idn= ObjectId()
        mock_user = Usuario({"_id": idn, "rol": "Administrador", "documento": "EQ1234567", "email": "admin@correo.com", "nombre": "Admin"})
        mock_validate_user.return_value = mock_user
        app = Flask(__name__)
        app.config["WTF_CSRF_ENABLED"] = False
        app.testing = True
        with app.test_client() as client:
            with app.test_request_context():
                login_user(mock_user)
            response = client.post("/login", data={"id": "EQ1234567", "password": "clave123"}, follow_redirects=False)
            assert response.status_code in [302, 303]
            assert "/admin/dashboard" in response.location

    @patch("auth.routes.db")
    @patch("auth.routes.enviar_email")
    @patch("auth.routes.generate_password_hash")
    def test_recover_envia_email(self,mock_hash, mock_enviar_email, mock_db):
        idn= ObjectId()
        mock_hash.return_value = "hashed_nueva"
        mock_db.__getitem__.return_value.find_one.return_value = {
            "_id": idn,
            "documento": "EQ1234567",
            "email": "user@correo.com"
        }
        app = Flask(__name__)
        app.config["WTF_CSRF_ENABLED"] = False
        app.testing = True
        with app.test_client() as client:
            response = client.post("/recover", data={"id": "EQ1234567", "email": "user@correo.com"}, follow_redirects=True)
            assert b"Se ha enviado una nueva contrase" in response.data
            mock_enviar_email.assert_called_once()


    def test_login_form_valido(self):
        app = Flask(__name__)
        app.config["WTF_CSRF_ENABLED"] = False
        with app.test_request_context(method="POST", data={
            "id": "EQ1234567",
            "password": "clave123"
        }):
            form = LoginForm()
            assert form.validate() is True

    def test_recover_form_email_invalido(self):
        app = Flask(__name__)
        app.config["WTF_CSRF_ENABLED"] = False
        with app.test_request_context(method="POST", data={
            "id": "EQ1234567",
            "email": "correo_invalido"
        }):
            form = RecoverForm()
            assert not form.validate()
            assert "Invalid email address" in form.email.errors[0]

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    pytest.main([__file__])