from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import Optional, EqualTo, DataRequired, Email

class UsuarioCrearForm(FlaskForm):
    nombre = StringField("Name", validators=[DataRequired()])
    rol = SelectField("Role", choices=[("Administrador", "Administrador"), ("Analista", "Analista")], validators=[DataRequired()])
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Create")

class UsuarioEditarForm(FlaskForm):
    nombre = StringField("Name", validators=[DataRequired()])
    rol = SelectField("Role", choices=[("Administrador", "Administrador"), ("Analista", "Analista")], validators=[DataRequired()])
    documento = StringField("ID", render_kw={"readonly": True})
    email = StringField("E-mail", render_kw={"readonly": True})
    nueva_contrasena = PasswordField("New Password", validators=[Optional()])
    confirmar_contrasena = PasswordField("Confirm Password", validators=[
        Optional(),
        EqualTo('nueva_contrasena', message='Passwords must match')
    ])
    submit = SubmitField("Save")