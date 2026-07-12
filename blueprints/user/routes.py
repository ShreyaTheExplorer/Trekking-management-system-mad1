"""
blueprints/user/routes.py
"""

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from sqlalchemy import or_, func

from . import bp
from .forms import ProfileForm
from extensions import db
from models import User, Trek, Booking, create_booking, cancel_booking
from utils import trekker_required


# ── BROWSE TREKS ────────────────────────────────────────────────────────────

@bp.route("/treks")
def browse_treks():
    # Extract filter parameters from URL
    location = request.args.get("location", "").strip()
    month = request.args.get("month", "").strip()
    season = request.args.get("season", "").strip()
    difficulty = request.args.get("difficulty", "").strip()

    # Query open treks
    query = Trek.query.filter(Trek.status == "Open")

    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))
    if month:
        query = query.filter(Trek.month == month)
    if season:
        query = query.filter(Trek.season == season)
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)

    treks = query.order_by(Trek.start_date.asc()).all()

    # "Suggested for you" block logic
    last_booking = None
    if current_user.is_authenticated and current_user.is_trekker:
        last_booking = (
            Booking.query.filter_by(user_id=current_user.id)
            .order_by(Booking.booking_date.desc())
            .first()
        )

    suggested_treks = []
    suggestion_reason = ""
    if last_booking and last_booking.trek:
        ref_trek = last_booking.trek
        suggestion_reason = f"Based on your recent booking: {ref_trek.name}"
        # Suggest treks with same location or difficulty, excluding the already booked one
        suggested_treks = (
            Trek.query.filter(
                Trek.status == "Open",
                Trek.id != ref_trek.id,
                or_(
                    Trek.location.ilike(f"%{ref_trek.location}%"),
                    Trek.difficulty == ref_trek.difficulty
                )
            )
            .limit(4)
            .all()
        )
        # If no matching treks found, fallback to most-booked
        if not suggested_treks:
            last_booking = None

    if not last_booking:
        suggestion_reason = "Popular treks overall"
        # Find most-booked treks overall
        most_booked = (
            db.session.query(Trek, func.count(Booking.id).label("booking_count"))
            .join(Booking, Booking.trek_id == Trek.id, isouter=True)
            .filter(Trek.status == "Open")
            .group_by(Trek.id)
            .order_by(db.desc("booking_count"), Trek.id.desc())
            .limit(4)
            .all()
        )
        suggested_treks = [item[0] for item in most_booked]

    # Pre-populate lists for search/filter form drop-downs
    locations = [r[0] for r in db.session.query(Trek.location).distinct().all() if r[0]]
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    seasons = ["Summer", "Monsoon", "Autumn", "Winter", "Spring"]
    difficulties = ["Easy", "Moderate", "Hard"]

    return render_template(
        "user/browse.html",
        treks=treks,
        suggested_treks=suggested_treks,
        suggestion_reason=suggestion_reason,
        locations=locations,
        months=months,
        seasons=seasons,
        difficulties=difficulties,
        # Keep track of filter state
        filter_location=location,
        filter_month=month,
        filter_season=season,
        filter_difficulty=difficulty,
    )


# ── TREK DETAIL ─────────────────────────────────────────────────────────────

@bp.route("/treks/<int:trek_id>")
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    # Check if this trek has already been booked by the current user (if logged in)
    has_booked = False
    if current_user.is_authenticated and current_user.is_trekker:
        has_booked = Booking.query.filter_by(
            user_id=current_user.id, trek_id=trek.id, status="Booked"
        ).first() is not None

    return render_template("user/trek_detail.html", trek=trek, has_booked=has_booked)


# ── BOOK TREK ───────────────────────────────────────────────────────────────

@bp.route("/treks/<int:trek_id>/book", methods=["POST"])
@trekker_required
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    try:
        create_booking(user=current_user, trek=trek, num_people=1)
        flash(f"Successfully booked '{trek.name}'!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("user.trek_detail", trek_id=trek_id))


# ── MY BOOKINGS ─────────────────────────────────────────────────────────────

@bp.route("/bookings")
@trekker_required
def my_bookings():
    # Active bookings (status 'Booked')
    active_bookings = (
        Booking.query.filter_by(user_id=current_user.id, status="Booked")
        .order_by(Booking.booking_date.desc())
        .all()
    )
    # History bookings (status 'Cancelled' or 'Completed')
    history_bookings = (
        Booking.query.filter(
            Booking.user_id == current_user.id,
            Booking.status.in_(["Cancelled", "Completed"])
        )
        .order_by(Booking.booking_date.desc())
        .all()
    )
    return render_template(
        "user/bookings.html",
        active_bookings=active_bookings,
        history_bookings=history_bookings,
    )


# ── CANCEL BOOKING ──────────────────────────────────────────────────────────

@bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@trekker_required
def cancel_booking_route(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        abort(403)
    try:
        cancel_booking(booking)
        flash("Booking cancelled successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("user.my_bookings"))


# ── PROFILE ─────────────────────────────────────────────────────────────────

@bp.route("/profile", methods=["GET", "POST"])
@trekker_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # Check if email is already taken by another user
        existing = User.query.filter(User.email == form.email.data, User.id != current_user.id).first()
        if existing:
            flash("That email is already registered to another account.", "danger")
        else:
            current_user.full_name = form.full_name.data
            current_user.phone = form.phone.data
            current_user.email = form.email.data
            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for("user.profile"))
    return render_template("user/profile.html", form=form)


# ── DASHBOARD (REDIRECT) ────────────────────────────────────────────────────

@bp.route("/dashboard")
@trekker_required
def dashboard():
    return redirect(url_for("user.browse_treks"))
