from flask import Flask
from flask_login import LoginManager
from auth.routes import auth_bp
from usuarios.routes import usuarios_bp
from usuarios.users import Usuario
from utils.conexion_mongo import db
from bson import ObjectId
from dashboard.routes import dashboard_bp
from scraping.routes import scraping_bp
from utils.api import api_bp
from reportes.routes import reportes_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = "clave-super-secreta"

    # Registrar Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(scraping_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(reportes_bp)

    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"  # Nombre del endpoint, no la ruta
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        user_data = db["usuarios"].find_one({"_id": ObjectId(user_id)}) # type: ignore
        return Usuario(user_data) if user_data else None

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)