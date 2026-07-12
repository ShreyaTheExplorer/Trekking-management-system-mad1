"""
blueprints/admin/forms.py
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, IntegerField,
    FloatField, TextAreaField, DateField, SubmitField,
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange


_MONTHS = [("", "-- Auto from start date --")] + [
    (m, m) for m in [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
]

_SEASONS = [
    ("", "-- Select Season --"),
    ("Summer", "Summer"),
    ("Monsoon", "Monsoon"),
    ("Autumn", "Autumn"),
    ("Winter", "Winter"),
    ("Spring", "Spring"),
]

_STATUSES = [
    ("Pending", "Pending"),
    ("Approved", "Approved"),
    ("Open", "Open"),
    ("Closed", "Closed"),
    ("Completed", "Completed"),
]

_DIFFICULTIES = [("Easy", "Easy"), ("Moderate", "Moderate"), ("Hard", "Hard")]


class TrekForm(FlaskForm):
    name = StringField("Trek Name", validators=[DataRequired(), Length(max=150)])
    location = StringField("Location", validators=[DataRequired(), Length(max=150)])
    difficulty = SelectField("Difficulty", choices=_DIFFICULTIES, validators=[DataRequired()])
    duration_days = IntegerField(
        "Duration (days)", validators=[DataRequired(), NumberRange(min=1, max=365)]
    )
    total_slots = IntegerField(
        "Total Slots", validators=[DataRequired(), NumberRange(min=1, max=999)]
    )
    # Shown on edit only — on create the route overrides it with total_slots.
    available_slots = IntegerField(
        "Available Slots", validators=[Optional(), NumberRange(min=0)]
    )
    start_date = DateField("Start Date", format="%Y-%m-%d", validators=[DataRequired()])
    end_date = DateField("End Date", format="%Y-%m-%d", validators=[DataRequired()])
    month = SelectField("Month", choices=_MONTHS, validators=[Optional()])
    season = SelectField("Season", choices=_SEASONS, validators=[Optional()])
    price = FloatField("Price (₹)", default=0.0, validators=[Optional(), NumberRange(min=0)])
    description = TextAreaField("Description", validators=[Optional()])
    # Store relative path: static/images/myfile.jpg  or an external URL.
    cover_image = StringField("Cover Image Path/URL", validators=[Optional(), Length(max=255)])
    status = SelectField("Status", choices=_STATUSES, validators=[DataRequired()])
    submit = SubmitField("Save Trek")


class AssignStaffForm(FlaskForm):
    """
    Choices must be populated in the route before rendering:
        form.staff_profile_id.choices = [(p.id, label) for p in eligible]
    Uses Optional() so that value 0 (the "Unassign" option) passes validation —
    DataRequired() would reject 0 because it is falsy.
    """
    staff_profile_id = SelectField(
        "Staff Member", coerce=int, validators=[Optional()]
    )
    submit = SubmitField("Assign")