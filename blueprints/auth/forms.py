"""
blueprints/auth/forms.py
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SelectField, RadioField,
    IntegerField, TextAreaField, SubmitField,
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Optional, NumberRange,
)


class RegisterForm(FlaskForm):
    role = SelectField(
        "Register as",
        choices=[("trekker", "Trekker"), ("staff", "Trek Staff")],
        validators=[DataRequired()],
    )
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )

    # Staff-only fields — leave blank if registering as a Trekker.
    bio = TextAreaField("Short Bio", validators=[Optional(), Length(max=500)])
    experience_years = IntegerField(
        "Years of Experience", validators=[Optional(), NumberRange(min=0, max=60)]
    )
    certification = StringField("Certification", validators=[Optional(), Length(max=200)])

    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    """
    Backs the three-tab (Admin / Staff / Trekker) login page. Each tab has
    its own field names so a CSS-only tab toggle can show/hide panels
    without their submitted values colliding with each other.
    """
    role = RadioField(
        "Login as",
        choices=[("admin", "Admin"), ("staff", "Trek Staff"), ("trekker", "Trekker")],
        default="trekker",
        validators=[DataRequired()],
    )

    admin_username = StringField("Username", validators=[Optional()])
    admin_password = PasswordField("Password", validators=[Optional()])

    staff_username = StringField("Username", validators=[Optional()])
    staff_password = PasswordField("Password", validators=[Optional()])
    staff_id = StringField("Staff ID", validators=[Optional()])

    trekker_username = StringField("Username", validators=[Optional()])
    trekker_password = PasswordField("Password", validators=[Optional()])

    submit = SubmitField("Login")


class CheckStatusForm(FlaskForm):
    identifier = StringField("Username or Email", validators=[DataRequired()])
    submit = SubmitField("Check Status")