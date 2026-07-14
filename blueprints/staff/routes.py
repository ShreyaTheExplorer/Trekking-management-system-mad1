"""
blueprints/staff/routes.py
"""

from flask import render_template, redirect, url_for, flash, abort
from flask_login import current_user

from . import bp
from .forms import UpdateTrekForm
from extensions import db
from models import Trek, Booking
from utils import staff_required


# ── DASHBOARD ──────────────────────────────────────────────────────────────

@bp.route("/dashboard")
@staff_required
def dashboard():
    profile = current_user.staff_profile
    treks = (
        Trek.query
        .filter_by(assigned_staff_id=profile.id)
        .order_by(Trek.start_date)
        .all()
    )
    trek_data = []
    for trek in treks:
        booked_count = Booking.query.filter_by(trek_id=trek.id, status="Booked").count()
        trek_data.append({"trek": trek, "booked_count": booked_count})
    return render_template("staff/dashboard.html", trek_data=trek_data)


# ── UPDATE SLOTS & STATUS ──────────────────────────────────────────────────

@bp.route("/treks/<int:trek_id>/update", methods=["GET", "POST"])
@staff_required
def update_trek(trek_id):
    trek = db.get_or_404(Trek, trek_id)
    if trek.assigned_staff_id != current_user.staff_profile.id:
        abort(403)

    form = UpdateTrekForm(obj=trek)
    if form.validate_on_submit():
        new_slots = form.available_slots.data
        if new_slots is not None:
            if new_slots > trek.total_slots:
                flash(f"Available slots ({new_slots}) cannot exceed total slots ({trek.total_slots}).", "danger")
                return render_template("staff/update_trek.html", form=form, trek=trek)
        if new_slots is not None:
            from sqlalchemy import func
            # Count total people already confirmed, not just number of records.
            booked_people = (
                db.session.query(func.sum(Booking.num_people))
                .filter_by(trek_id=trek.id, status="Booked")
                .scalar()
            ) or 0
            if new_slots < booked_people:
                flash(
                    f"Cannot reduce slots to {new_slots} — "
                    f"{booked_people} person(s) are already booked on this trek.",
                    "danger",
                )
                return render_template("staff/update_trek.html", form=form, trek=trek)
            trek.available_slots = new_slots
        trek.status = form.status.data
        db.session.commit()
        flash(f"Trek '{trek.name}' updated successfully.", "success")
        return redirect(url_for("staff.dashboard"))

    return render_template("staff/update_trek.html", form=form, trek=trek)


# ── PARTICIPANTS ───────────────────────────────────────────────────────────

@bp.route("/treks/<int:trek_id>/participants")
@staff_required
def participants(trek_id):
    trek = db.get_or_404(Trek, trek_id)
    if trek.assigned_staff_id != current_user.staff_profile.id:
        abort(403)
    bookings = (
        Booking.query
        .filter_by(trek_id=trek_id)
        .order_by(Booking.status, Booking.booking_date.desc())
        .all()
    )
    return render_template("staff/participants.html", trek=trek, bookings=bookings)


# ── STATUS TRANSITIONS ─────────────────────────────────────────────────────

@bp.route("/treks/<int:trek_id>/mark-started", methods=["POST"])
@staff_required
def mark_started(trek_id):
    trek = db.get_or_404(Trek, trek_id)
    if trek.assigned_staff_id != current_user.staff_profile.id:
        abort(403)
    if trek.status not in ("Open", "Approved"):
        flash("Trek can only be started from Open or Approved status.", "warning")
        return redirect(url_for("staff.dashboard"))
    trek.status = "Closed"   # Closed = started; no new bookings accepted
    db.session.commit()
    flash(f"Trek '{trek.name}' has started — new bookings are now closed.", "info")
    return redirect(url_for("staff.dashboard"))


@bp.route("/treks/<int:trek_id>/mark-completed", methods=["POST"])
@staff_required
def mark_completed(trek_id):
    trek = db.get_or_404(Trek, trek_id)
    if trek.assigned_staff_id != current_user.staff_profile.id:
        abort(403)
    trek.status = "Completed"
    # Cascade: all active bookings become Completed too
    Booking.query.filter_by(trek_id=trek_id, status="Booked").update({"status": "Completed"})
    db.session.commit()
    flash(
        f"Trek '{trek.name}' marked as completed. "
        "All active bookings have been updated.",
        "success",
    )
    return redirect(url_for("staff.dashboard"))