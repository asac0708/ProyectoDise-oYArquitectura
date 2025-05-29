from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import DataRequired, Email

class RecoverForm(FlaskForm):
    """
    FlaskForm for account recovery.

    Fields:
        id (StringField): User's document ID. Required.
        email (StringField): User's registered email address. Required and must be a valid email.
        submit (SubmitField): Button to submit the recovery form.
    """
    id = StringField("ID", validators=[DataRequired()], render_kw={"placeholder": "Your document"})
    email = StringField("E-mail", validators=[DataRequired(), Email()], render_kw={"placeholder": "Your registered e-mail"})
    submit = SubmitField("Recover")
    
class LoginForm(FlaskForm):
    """
    Login form for user authentication.

    Fields:
        id (StringField): User's document ID. Required.
        password (PasswordField): User's password. Required.
        submit (SubmitField): Button to submit the login form.
    """
    id = StringField("ID", validators=[DataRequired()], render_kw={"placeholder": "Your document"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"placeholder": "Your password"})
    submit = SubmitField("Login")

class RecoverForm(FlaskForm):
    """
    FlaskForm for account recovery.

    Fields:
        id (StringField): User's identification, required.
        email (StringField): User's email address, required and must be a valid email.
        submit (SubmitField): Button to submit the recovery form.
    """
    id = StringField("ID", validators=[DataRequired()])
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    submit = SubmitField("Recover")
