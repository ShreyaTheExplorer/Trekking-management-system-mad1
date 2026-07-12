"""
blueprints/staff/forms.py
"""

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange


class UpdateTrekForm(FlaskForm):
    available_slots = IntegerField(
        "Available Slots",
        validators=[Optional(), NumberRange(min=0, message="Slots cannot be negative.")],
    )
    status = SelectField(
        "Trek Status",
        choices=[
            ("Open",   "Open — accepting bookings"),
            ("Closed", "Closed — no new bookings"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Changes")